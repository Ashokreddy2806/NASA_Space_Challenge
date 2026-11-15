"""Phase 4 API tests (need Phase 1-3 outputs; skipped otherwise)."""
import json

import pytest

from backend.config import load_config

try:
    _c = load_config()
    need = [_c.output(k) for k in ("target_profiles", "top_sites", "scores_moon", "scores_mars", "earth_features")]
    HAVE = all(p.exists() for p in need)
except Exception:
    HAVE = False
pytestmark = pytest.mark.skipif(not HAVE, reason="run `make all` first")


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    return TestClient(app)


def test_targets_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    ts = {t["id"]: t for t in client.get("/targets").json()}
    assert set(ts) == {"moon", "mars"}
    assert any(n["feature"] == "hurst_2_32km" for n in ts["mars"]["not_scored"])  # unresolved at MOLA resolution
    assert client.get("/targets/nope").status_code == 404


def test_profile_has_limits(client):
    p = client.get("/targets/moon").json()
    assert p["earth_cannot_replicate"] and p["ice_proxy"]["value"] > 0


def test_top_sites_and_geojson(client):
    r = client.get("/targets/moon/top-sites", params={"n": 5}).json()
    assert len(r["sites"]) == 5 and r["sites"][0]["site_score"] >= r["sites"][-1]["site_score"]
    assert r["sites"][0]["features"]
    g = client.get("/targets/moon/top-sites", params={"format": "geojson", "exclude_famous": True}).json()
    assert g["type"] == "FeatureCollection" and not any(f["properties"]["famous"] for f in g["features"])
    assert client.get("/targets/moon/top-sites", params={"preset": "nope"}).status_code == 422


def test_site_evidence(client):
    r = client.get("/targets/mars/site", params={"lat": -26.8, "lon": 16.2}).json()
    f = {x["feature"]: x for x in r["features"]}
    assert "absolute_gap" in f["relief_20km_m"] and "rank_similarity" in f["relief_20km_m"]
    assert 0 <= r["score"] <= 1 and r["earth_cannot_replicate"]
    assert any(n["feature"] == "roughness_5km_m" for n in r["not_scored"])


def test_site_ocean_404_and_bad_params(client):
    assert client.get("/targets/moon/site", params={"lat": 0, "lon": -30}).status_code == 404
    assert client.get("/targets/moon/site", params={"lat": 95, "lon": 0}).status_code == 422
    assert client.get("/targets/moon/site", params={"lat": -13, "lon": -73.5, "weights": '{"bogus": 1}'}).status_code == 422


def test_custom_weights_match_preset(client):
    pre = client.get("/targets/moon/site", params={"lat": -12.9, "lon": -73.6, "preset": "rover_mobility"}).json()["score"]
    w = json.dumps({"relief": 1, "slope": 1.5, "roughness": 1, "scale_robust_roughness": 0.5})
    cus = client.get("/targets/moon/site", params={"lat": -12.9, "lon": -73.6, "weights": w}).json()["score"]
    assert abs(pre - cus) < 1e-4


def test_validation_and_png(client):
    v = client.get("/targets/moon/validation").json()
    assert any(s["name"] == "Atacama" for s in v["sites"])
    r = client.get("/targets/moon/score.png", params={"step": 10})
    assert r.status_code == 200 and r.content[:4] == b"\x89PNG"
    assert client.get("/targets/moon/score.png", params={"preset": "nope"}).status_code == 422


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "Earth Analog Finder" in r.text
    assert client.get("/app.js").status_code == 200
