#!/usr/bin/env python3
"""TERRATWIN — Scientific API Server & Static Host.

Serves the interactive frontend and provides REST API endpoints
for targets, profiles, rankings, mission presets, and dynamic weight recalculation.
Built using Python's standard library (zero external dependencies).
"""

from __future__ import annotations

import cgi
import http.server
import json
import os
import socketserver
import sys
import urllib.parse
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to sys.path so scientific_engine can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.data.loading import load_yaml_config
from scientific_engine.src.similarity.ranking import GLOBAL_CANDIDATE_POOL
from scientific_engine.src.similarity.scoring import SimilarityScorer

FRONTEND_DIR = Path(__file__).resolve().parent

# Load data caches
PROFILES_PATH = ENGINE_DIR / "outputs" / "profiles" / "target_profiles.json"
RANKINGS_PATH = ENGINE_DIR / "outputs" / "rankings" / "all_target_rankings.json"
WEIGHTS_PATH = ENGINE_DIR / "config" / "weights.yaml"
FEATURES_PATH = ENGINE_DIR / "config" / "features.yaml"

TARGET_PROFILES: Dict[str, Any] = {}
TARGET_RANKINGS: Dict[str, Any] = {}
WEIGHT_CONFIG: Dict[str, Any] = {}
FEATURE_CONFIG: Dict[str, Any] = {}
SCORER: Optional[SimilarityScorer] = None

def init_data():
    global TARGET_PROFILES, TARGET_RANKINGS, WEIGHT_CONFIG, FEATURE_CONFIG, SCORER
    if PROFILES_PATH.exists():
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            TARGET_PROFILES = json.load(f)
    if RANKINGS_PATH.exists():
        with open(RANKINGS_PATH, "r", encoding="utf-8") as f:
            TARGET_RANKINGS = json.load(f)
    if WEIGHTS_PATH.exists():
        WEIGHT_CONFIG = load_yaml_config(WEIGHTS_PATH)
    if FEATURES_PATH.exists():
        FEATURE_CONFIG = load_yaml_config(FEATURES_PATH)
    try:
        SCORER = SimilarityScorer()
    except Exception as e:
        print(f"Warning: Could not initialize SimilarityScorer: {e}", file=sys.stderr)

init_data()

class TerratwinRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler routing /api endpoints and serving frontend."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_DIR), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        if path == "" or path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()

        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # Fallback to static file serving
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/similarity/recalculate":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(body) if body else {}
                self.handle_recalculate(data)
            except Exception as e:
                self.send_json_response({"error": str(e)}, status=400)
            return

        self.send_json_response({"error": "Endpoint not found"}, status=404)

    def handle_api_get(self, path: str, query: Dict[str, List[str]]):
        if path == "/api/health":
            self.send_json_response({
                "status": "healthy",
                "version": "1.0.0",
                "targets_loaded": len(TARGET_PROFILES.get("targets", {})),
                "candidates_loaded": len(GLOBAL_CANDIDATE_POOL)
            })
            return

        if path == "/api/targets":
            targets_summary = []
            targets_dict = TARGET_PROFILES.get("targets", {})
            for tid, t in targets_dict.items():
                targets_summary.append({
                    "target_id": tid,
                    "target_name": t.get("target_name"),
                    "body": t.get("body"),
                    "mission_context": t.get("mission_context"),
                    "geological_epoch": t.get("geological_epoch"),
                    "aoi": t.get("aoi"),
                    "feature_count": len(t.get("features", {})),
                    "summary": f"{t.get('body')} — {t.get('geological_epoch', '')} ({t.get('mission_context', '')})"
                })
            self.send_json_response({"targets": targets_summary})
            return

        if path.startswith("/api/targets/") and path.endswith("/profile"):
            parts = path.split("/")
            if len(parts) >= 4:
                tid = parts[3]
                target = TARGET_PROFILES.get("targets", {}).get(tid)
                if target:
                    self.send_json_response(target)
                else:
                    self.send_json_response({"error": f"Target '{tid}' not found"}, status=404)
                return

        if path.startswith("/api/similarity/") and path.endswith("/sites"):
            parts = path.split("/")
            if len(parts) >= 4:
                tid = parts[3]
                rankings = TARGET_RANKINGS.get(tid, {})
                if not rankings:
                    self.send_json_response({"error": f"Rankings for '{tid}' not found"}, status=404)
                    return
                include_famous = query.get("include_famous", ["true"])[0].lower() == "true"
                show_all = query.get("all", ["false"])[0].lower() == "true"
                if show_all:
                    sites = rankings.get("all_ranked", [])
                    filter_name = "all_ranked"
                else:
                    filter_name = "top10_including_famous" if include_famous else "top10_excluding_famous"
                    sites = rankings.get(filter_name, [])
                self.send_json_response({
                    "target_id": tid,
                    "filter": filter_name,
                    "total_candidates": rankings.get("total_candidates", len(sites)),
                    "count": len(sites),
                    "sites": sites
                })
                return

        if path.startswith("/api/similarity/"):
            parts = path.split("/")
            if len(parts) >= 3:
                tid = parts[3]
                rankings = TARGET_RANKINGS.get(tid)
                target = TARGET_PROFILES.get("targets", {}).get(tid)
                if rankings:
                    self.send_json_response({
                        "target_id": tid,
                        "target_name": target.get("target_name") if target else tid,
                        "rankings": rankings
                    })
                else:
                    self.send_json_response({"error": f"No similarity data for '{tid}'"}, status=404)
                return

        if path == "/api/presets":
            presets = WEIGHT_CONFIG.get("presets", {})
            features = FEATURE_CONFIG.get("features", {})
            self.send_json_response({
                "presets": presets,
                "features": features
            })
            return

        if path.startswith("/api/analysis/"):
            parts = path.split("/")
            if len(parts) >= 5:
                tid = parts[3]
                site_id = parts[4]
                self.handle_site_analysis(tid, site_id)
                return

        self.send_json_response({"error": "Unknown API endpoint"}, status=404)

    def handle_recalculate(self, data: Dict[str, Any]):
        global SCORER
        if not SCORER:
            SCORER = SimilarityScorer()

        target_id = data.get("target_id", "moon_south_pole")
        custom_weights = data.get("weights", {})
        preset_name = data.get("preset_name", "custom")

        target = TARGET_PROFILES.get("targets", {}).get(target_id)
        if not target:
            self.send_json_response({"error": f"Target '{target_id}' not found"}, status=404)
            return

        ranked_results = []
        for cand in GLOBAL_CANDIDATE_POOL:
            res = SCORER.score_cell(
                earth_values=cand["features"],
                target_profile=target,
                preset_name=preset_name,
                custom_weights=custom_weights if custom_weights else None
            )
            cand_dict = {
                "site_name": cand["name"],
                "country": cand["country"],
                "region": cand.get("region", ""),
                "continent": cand.get("continent", "Global"),
                "environment_type": cand.get("environment_type", "desert"),
                "latitude": cand["lat"],
                "longitude": cand["lon"],
                "elevation_m": cand.get("elevation_m", 0.0),
                "is_famous": cand["famous"],
                "validation_status": cand.get("validation_status", "candidate_region"),
                "data_source": cand.get("data_source", "ETOPO 2022 / WorldClim 2.1"),
                "description": cand.get("description", ""),
                "overall_score": round(res.overall_score, 2),
                "data_quality_percent": round(res.data_quality * 100.0, 1),
                "top_matching_features": [(k, round(v, 1)) for k, v in res.top_matching_features],
                "top_deviating_features": [(k, round(v, 1)) for k, v in res.top_deviating_features],
                "missing_features": res.missing_features,
                "exploration_suitability": res.exploration_suitability,
                "feature_subscores": {k: round(v, 1) for k, v in res.feature_subscores.items()},
                "features": cand["features"]
            }
            ranked_results.append(cand_dict)

        ranked_results.sort(key=lambda x: x["overall_score"], reverse=True)

        famous_included = ranked_results[:10]
        famous_excluded = [r for r in ranked_results if not r["is_famous"]][:10]

        self.send_json_response({
            "target_id": target_id,
            "weights_used": custom_weights,
            "top10_including_famous": famous_included,
            "top10_excluding_famous": famous_excluded,
            "all_ranked": ranked_results
        })

    def handle_site_analysis(self, target_id: str, site_id: str):
        # Match site by name substring or ID
        matched_cand = None
        for cand in GLOBAL_CANDIDATE_POOL:
            norm_name = cand["name"].lower().replace(" ", "_")
            if site_id.lower() in norm_name or norm_name in site_id.lower():
                matched_cand = cand
                break

        if not matched_cand:
            self.send_json_response({"error": f"Site '{site_id}' not found"}, status=404)
            return

        target = TARGET_PROFILES.get("targets", {}).get(target_id, {})
        res = SCORER.score_cell(matched_cand["features"], target) if SCORER and target else None

        analysis = {
            "site_name": matched_cand["name"],
            "country": matched_cand["country"],
            "coordinates": {"lat": matched_cand["lat"], "lon": matched_cand["lon"]},
            "is_famous": matched_cand["famous"],
            "target_id": target_id,
            "target_name": target.get("target_name", target_id),
            "score": round(res.overall_score, 2) if res else None,
            "matches": [(k, round(v, 1)) for k, v in res.top_matching_features] if res else [],
            "deviations": [(k, round(v, 1)) for k, v in res.top_deviating_features] if res else [],
            "unreplicable_factors": [
                {"factor": "Surface Gravity", "earth": "1.00 g (9.81 m/s²)", "planetary": "0.166 g (Moon) / 0.376 g (Mars)", "impact": "Alters wheel slippage, sinkage, regolith shearing, and dust suspension times."},
                {"factor": "Atmosphere & Pressure", "earth": "101.3 kPa (N₂/O₂)", "planetary": "<10⁻¹⁰ Pa (Moon vacuum) / 0.6 kPa (Mars CO₂)", "impact": "No aerodynamic drag, extreme thermal convection loss, triple-point water sublimation."},
                {"factor": "Ionizing Radiation", "earth": "~2.4 mSv/year (magnetosphere & thick atmosphere)", "planetary": "300 - 1,100 mSv/year (unshielded GCR + SPE)", "impact": "High-dose single event upsets in avionics; deep DNA double-strand breaks for crew."},
                {"factor": "Regolith Morphology", "earth": "Rounded fluvial/aeolian quartz grains with clays", "planetary": "Jagged, sub-micron impact glass shards with electrostatic clinging", "impact": "Severe mechanical seal abrasion, visor scratching, and respiratory hazard."}
            ]
        }
        self.send_json_response(analysis)

    def send_json_response(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

def run_server(port: int = 8080):
    handler = TerratwinRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"================================================================")
        print(f" TERRATWIN API & Web Server running at: http://localhost:{port}/")
        print(f" Serving Phase 5 frontend and Phase 2/3 scientific outputs")
        print(f"================================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")

if __name__ == "__main__":
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
