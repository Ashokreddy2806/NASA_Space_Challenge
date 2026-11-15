"""Phase 2 smoke tests: target profile file is complete and honest."""
import json

import pytest

from backend.paths import DOCS_DIR
from backend.pipeline.diviner import diviner_south_profile
from backend.pipeline.target_profiles import DRYNESS, TEMPERATURE, TERRAIN

PATH = DOCS_DIR / "target_profiles.json"
pytestmark = pytest.mark.skipif(not PATH.exists(), reason="run python -m backend.pipeline.target_profiles")
DIVINER_HEADER = ("tri1_x,tri1_y,tri1_z,tri2_x,tri2_y,tri2_z,tri3_x,tri3_y,tri3_z,"
                  "tri_clon,tri_clat,tri_calt,temp_avg,temp_max,ice_depth")


def targets():
    return json.loads(PATH.read_text())["targets"]


def test_one_profile_per_target():
    assert set(targets()) == {"moon_south_pole", "mars_jezero"}


@pytest.mark.parametrize("key", ["moon_south_pole", "mars_jezero"])
def test_features_documented(key):
    feats = targets()[key]["features"]
    assert set(feats) == set(TERRAIN + TEMPERATURE + DRYNESS)
    for k in TERRAIN:
        f = feats[k]
        assert f["p10"] <= f["value"] <= f["p90"] and f["units"] and 0 <= f["earth_percentile"] <= 100
    assert targets()[key]["resolution_note"]


def test_temperatures_never_guessed():
    mars = targets()["mars_jezero"]["features"]
    for k in TEMPERATURE:
        assert mars[k]["value"] is None
    moon = targets()["moon_south_pole"]["features"]
    for k in ("temp_diurnal_range_c", "temp_min_coldest_c", "temp_annual_range_c"):
        assert moon[k]["value"] is None and moon[k]["status"] == "missing_no_source"
    for k in ("temp_mean_c", "temp_max_warmest_c"):
        assert moon[k]["value"] is not None
        assert moon[k]["status"] == "measured_surface" and moon[k]["beyond_earth_range"]


def test_diviner_weighted_median_and_cold_trap(tmp_path):
    path = tmp_path / "dlre_prp_south.tab"
    rows = [
        "0,0,0,2,0,0,0,2,0,0,-88,0,200,100,-999",
        "0,0,0,1,0,0,0,1,0,0,-86,0,250,200,-999",
        "0,0,0,1,0,0,0,1,0,0,-84,0,300,100,-999",
    ]
    path.write_text("\n".join([DIVINER_HEADER, *rows]) + "\n")
    profile = diviner_south_profile(path, lat_limit=-85.0)
    assert profile["n_triangles"] == 2
    assert profile["area_km2"] == pytest.approx(2.5)
    assert profile["temp_avg_c"]["median"] == pytest.approx(200 - 273.15)
    assert profile["temp_avg_c"]["p90"] == pytest.approx(250 - 273.15)
    assert profile["temp_max_c"]["median"] == pytest.approx(100 - 273.15)
    assert profile["cold_trap_area_fraction"] == pytest.approx(2 / 2.5)


def test_moon_psr_fraction_sane():
    assert 0.02 < targets()["moon_south_pole"]["ice_cold_trap_proxy"]["psr_area_fraction"] < 0.3
