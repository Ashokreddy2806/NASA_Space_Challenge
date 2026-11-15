"""Phase 3 unit tests for the similarity engine (synthetic data, no large files)."""
import numpy as np

from backend.engine.similarity import ICE, PRESETS, Ecdf, score_map, target_percentiles, top_sites


def test_ecdf_midrank_and_ties():
    e = Ecdf(np.array([1.0, 2.0, 2.0, 3.0]), np.ones(4))
    assert e.percentile(0.0) == 0 and e.percentile(9.0) == 100
    assert abs(float(e.percentile(2.0)) - 50) < 1e-4


def test_area_weights_change_percentile():
    e = Ecdf(np.array([1.0, 2.0]), np.array([1.0, 3.0]))
    assert abs(float(e.percentile(1.0)) - 12.5) < 1e-4


def grids(n=4):
    rng = np.random.default_rng(1)
    return {k: rng.uniform(0, 100, (n, n)).astype("float32")
            for k in ["relief_20km_m", "slope_20km_deg", "precip_annual_mm", ICE]}


def test_identical_cell_scores_100_and_monotone():
    g = grids()
    t = {k: float(v[0, 0]) for k, v in g.items()}
    s, subs, used = score_map(g, t, {"relief_20km_m": 1, "slope_20km_deg": 1})
    assert s[0, 0] == 100 and (s <= 100).all() and used == ["relief_20km_m", "slope_20km_deg"]
    assert np.argmax(s) == 0 or s.max() == 100


def test_missing_target_features_dropped_not_guessed():
    g = grids()
    s, subs, used = score_map(g, {"relief_20km_m": 50.0}, {"relief_20km_m": 1, "slope_20km_deg": 1})
    assert used == ["relief_20km_m"] and "slope_20km_deg" not in subs


def test_zero_factor_removes_feature():
    g = grids()
    t = {"relief_20km_m": 50.0, "slope_20km_deg": 50.0}
    _, _, used = score_map(g, t, {"relief_20km_m": 1, "slope_20km_deg": 1}, {"slope_20km_deg": 0.0})
    assert used == ["relief_20km_m"]


def test_dryness_one_sided_and_thermal_unavailable():
    prof = {"features": {"precip_annual_mm": {"value": 0.0, "status": "one_sided_constraint"},
                         "temp_mean_c": {"value": None, "status": "missing_site_specific_literature_value"}},
            "ice_cold_trap_proxy": {"status": "not_in_mvp"}}
    ecdfs = {"precip_annual_mm": Ecdf(np.array([0.0, 10.0]), np.ones(2))}
    pct, dropped, _ = target_percentiles(prof, ecdfs)
    assert pct == {"precip_annual_mm": 0.0} and "temp_mean_c" in dropped and ICE in dropped
    g = {"precip_annual_mm": np.zeros((2, 2), "float32")}
    _, _, used = score_map(g, pct, PRESETS["thermal_cycling"])
    assert used == []


def test_top_sites_separated():
    lat, lon = np.linspace(89.975, -89.975, 3600), np.linspace(-179.975, 179.975, 7200)
    s = np.full((3600, 7200), 50, "float32")
    s[1800, 3600] = 99
    s[1801, 3601] = 98  # same place: must be suppressed
    s[900, 900] = 97
    p = top_sites(s, lat, lon, n=3)
    assert [round(x["score"]) for x in p[:2]] == [99, 97]
