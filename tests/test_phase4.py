"""Phase 4 API tests (need Phase 1-3 outputs; skipped otherwise)."""
import json

import pytest

from backend.paths import DOCS_DIR, PROCESSED_DIR

need = [DOCS_DIR / "top_sites.json", PROCESSED_DIR / "similarity_moon_south_pole.nc", PROCESSED_DIR / "earth_features.nc"]
pytestmark = pytest.mark.skipif(not all(p.exists() for p in need), reason="run Phase 1-3 first")

M = "/targets/moon_south_pole"


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    return TestClient(app)


def test_targets_and_health(client):
    assert client.get("/health").json()["status"] == "ok"
    ts = client.get("/targets").json()
    assert {t["id"] for t in ts} == {"moon_south_pole", "mars_jezero"}
    assert any("temp_mean_c" in t["not_scored"] for t in ts)
    assert client.get("/targets/nope").status_code == 404


def test_profile_has_limits(client):
    assert client.get(M).json()["earth_cannot_replicate"]


def test_top_sites_and_geojson(client):
    r = client.get(f"{M}/top-sites", params={"n": 5}).json()
    assert len(r["sites"]) == 5 and r["sites"][0]["score"] >= r["sites"][-1]["score"]
    g = client.get(f"{M}/top-sites", params={"format": "geojson", "exclude_famous": True}).json()
    assert g["type"] == "FeatureCollection" and len(g["features"]) == 10
    assert client.get("/targets/mars_jezero/top-sites", params={"preset": "thermal_cycling"}).status_code == 422


def test_site_breakdown_atacama(client):
    r = client.get(f"{M}/site", params={"lat": -23.5, "lon": -68.5}).json()
    f = {x["feature"]: x for x in r["features"]}
    assert f["precip_annual_mm"]["verdict"] == "match" and f["precip_annual_mm"]["earth_value"] is not None
    assert r["earth_cannot_replicate"] and r["not_scored"]


def test_site_ocean_404_and_bad_params(client):
    assert client.get(f"{M}/site", params={"lat": 0, "lon": -30}).status_code == 404
    assert client.get(f"{M}/site", params={"lat": 95, "lon": 0}).status_code == 422
    assert client.get(f"{M}/site", params={"lat": -23.5, "lon": -68.5, "weights": "{\"bogus\": 1}"}).status_code == 422


def test_custom_weights_match_preset(client):
    pre = client.get(f"{M}/site", params={"lat": -23.5, "lon": -68.5, "preset": "rover_mobility"}).json()["score"]
    w = json.dumps({"slope_20km_deg": 3, "relief_20km_m": 1, "roughness_5km_m": 2 / 3, "roughness_10km_m": 2 / 3,
                    "roughness_20km_m": 2 / 3, "hurst_2_32km": 0.5})
    cus = client.get(f"{M}/site", params={"lat": -23.5, "lon": -68.5, "weights": w}).json()["score"]
    assert abs(pre - cus) < 1.0  # uint8 rounding only


def test_score_png(client):
    r = client.get(f"{M}/score.png", params={"step": 10})
    assert r.status_code == 200 and r.content[:4] == b"\x89PNG"
    assert client.get("/targets/mars_jezero/score.png", params={"preset": "thermal_cycling"}).status_code == 422


def test_site_ice_row_is_frozen_ground_fraction(client):
    r = client.get(f"{M}/site", params={"lat": -77.5, "lon": 162.0}).json()
    ice = next(x for x in r["features"] if x["feature"] == "ice_proxy")
    assert ice["units"] == "fraction" and 0.05 < ice["target_value"] < 0.2
    assert 0 <= ice["earth_value"] <= 1 and "110 K" in ice["note"]
