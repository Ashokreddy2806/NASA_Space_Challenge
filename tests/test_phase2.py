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
    for t in targets().values():
        for k in TEMPERATURE:
            assert t["features"][k]["value"] is None


def test_moon_psr_fraction_sane():
    assert 0.02 < targets()["moon_south_pole"]["ice_cold_trap_proxy"]["psr_area_fraction"] < 0.3
