"""Phase 2 smoke tests: target profile file is complete and honest."""
import json

import pytest

from backend.paths import DOCS_DIR
from backend.pipeline.target_profiles import DRYNESS, TEMPERATURE, TERRAIN

PATH = DOCS_DIR / "target_profiles.json"
pytestmark = pytest.mark.skipif(not PATH.exists(), reason="run python -m backend.pipeline.target_profiles")


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
    # Mars has no site-specific value; the Moon only has what Diviner provides (mean, max).
    for k in TEMPERATURE:
        assert targets()["mars_jezero"]["features"][k]["value"] is None
    moon = targets()["moon_south_pole"]["features"]
    for k in ("temp_diurnal_range_c", "temp_min_coldest_c", "temp_annual_range_c"):
        assert moon[k]["value"] is None
    for k in ("temp_mean_c", "temp_max_warmest_c"):
        assert moon[k]["value"] is not None and moon[k]["p10"] <= moon[k]["value"] <= moon[k]["p90"]
        assert moon[k]["beyond_earth_range"] and moon[k]["status"] == "measured_surface_vs_air"


def test_diviner_cold_trap_agrees_with_psr():
    m = targets()["moon_south_pole"]
    assert abs(m["diviner_thermal"]["cold_trap_area_fraction"] - m["ice_cold_trap_proxy"]["psr_area_fraction"]) < 0.01


def test_moon_psr_fraction_sane():
    assert 0.02 < targets()["moon_south_pole"]["ice_cold_trap_proxy"]["psr_area_fraction"] < 0.3
