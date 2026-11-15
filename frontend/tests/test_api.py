"""Unit and integration tests for TERRATWIN API server.

Verifies:
1. Target profiles and metadata availability.
2. Similarity rankings and preset loading.
3. Live recalculation endpoint with custom weights.
4. HTTP GET and POST request handling with status codes and schemas.
"""

from __future__ import annotations

import io
import json
import unittest

from frontend.server import (
    FEATURE_CONFIG,
    GLOBAL_CANDIDATE_POOL,
    SCORER,
    TARGET_PROFILES,
    TARGET_RANKINGS,
    WEIGHT_CONFIG,
    TerratwinRequestHandler,
)


class MockSocket:
    """Mock socket for testing HTTP requests without external network binding."""

    def __init__(self, data: bytes = b""):
        self.rfile = io.BytesIO(data)
        self.wfile = io.BytesIO()

    def makefile(self, mode: str, *args, **kwargs):
        if "r" in mode:
            return self.rfile
        return self.wfile

    def sendall(self, data: bytes):
        self.wfile.write(data)


class TestTerratwinData(unittest.TestCase):
    """Test suite for data structures and scoring engine."""

    def test_targets_loaded(self):
        """Ensure all Phase 2 planetary targets are loaded."""
        targets = TARGET_PROFILES.get("targets", {})
        self.assertIn("moon_south_pole", targets)
        self.assertIn("mars_jezero_crater", targets)
        self.assertIn("mars_oxia_planum", targets)

        for tid, t in targets.items():
            self.assertIn("features", t)
            self.assertGreaterEqual(len(t["features"]), 12)
            self.assertIn("aoi", t)
            self.assertIn("mission_context", t)

    def test_rankings_loaded(self):
        """Ensure Phase 3 rankings are available for all targets."""
        for tid in ["moon_south_pole", "mars_jezero_crater", "mars_oxia_planum"]:
            self.assertIn(tid, TARGET_RANKINGS)
            r = TARGET_RANKINGS[tid]
            self.assertIn("top10_including_famous", r)
            self.assertIn("top10_excluding_famous", r)
            self.assertEqual(len(r["top10_including_famous"]), 10)
            self.assertEqual(len(r["top10_excluding_famous"]), 10)

    def test_candidate_pool(self):
        """Verify the global Earth candidate pool structure."""
        self.assertGreaterEqual(len(GLOBAL_CANDIDATE_POOL), 15)
        for cand in GLOBAL_CANDIDATE_POOL:
            self.assertIn("name", cand)
            self.assertIn("country", cand)
            self.assertIn("lat", cand)
            self.assertIn("lon", cand)
            self.assertIn("famous", cand)
            self.assertIn("features", cand)
            self.assertIn("slope_20km_deg", cand["features"])
            self.assertIn("roughness_10km_m", cand["features"])

    def test_presets_loaded(self):
        """Verify mission presets and feature weights."""
        presets = WEIGHT_CONFIG.get("presets", {})
        self.assertIn("rover_mobility", presets)
        self.assertIn("cold_trap_ice", presets)
        self.assertIn("thermal_cycling", presets)
        self.assertIn("balanced_default", presets)


class TestTerratwinHTTP(unittest.TestCase):
    """Test suite for HTTP API endpoints."""

    def _execute_request(self, raw_req: bytes) -> tuple[int, dict]:
        sock = MockSocket(raw_req)
        TerratwinRequestHandler(sock, ("127.0.0.1", 8080), None)
        out = sock.wfile.getvalue()
        header_end = out.find(b"\r\n\r\n")
        self.assertNotEqual(header_end, -1, "Missing HTTP header separator")
        headers_raw = out[:header_end].decode("utf-8")
        status_line = headers_raw.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1])
        body_raw = out[header_end + 4:].decode("utf-8")
        body = json.loads(body_raw) if body_raw else {}
        return status_code, body

    def test_get_health(self):
        """Test GET /api/health returns 200 and valid json."""
        req = b"GET /api/health HTTP/1.1\r\nHost: localhost\r\n\r\n"
        code, body = self._execute_request(req)
        self.assertEqual(code, 200)
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["targets_loaded"], 3)

    def test_get_targets(self):
        """Test GET /api/targets lists all planetary targets."""
        req = b"GET /api/targets HTTP/1.1\r\nHost: localhost\r\n\r\n"
        code, body = self._execute_request(req)
        self.assertEqual(code, 200)
        self.assertIn("targets", body)
        self.assertEqual(len(body["targets"]), 3)

    def test_post_recalculate(self):
        """Test POST /api/similarity/recalculate dynamically updates rankings."""
        payload = json.dumps({
            "target_id": "mars_jezero_crater",
            "weights": {"slope_20km_deg": 0.7, "roughness_10km_m": 0.3}
        }).encode("utf-8")
        req = (
            b"POST /api/similarity/recalculate HTTP/1.1\r\n"
            b"Host: localhost\r\n"
            b"Content-Length: " + str(len(payload)).encode() + b"\r\n"
            b"Content-Type: application/json\r\n\r\n" + payload
        )
        code, body = self._execute_request(req)
        self.assertEqual(code, 200)
        self.assertIn("top10_including_famous", body)
        self.assertEqual(len(body["top10_including_famous"]), 10)
        self.assertGreater(body["top10_including_famous"][0]["overall_score"], 80.0)


if __name__ == "__main__":
    unittest.main()
