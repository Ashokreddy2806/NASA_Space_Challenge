"""Phase 3 unit tests for the similarity engine (synthetic data, no large files)."""
import numpy as np
import pytest

from backend.engine.run_scoring import rank_check
from backend.engine.similarity import (
    ICE, PRESETS, STATUS_FACTOR, Ecdf, cold_trap_fraction, score_map, target_values, top_sites, transform,
)


def test_ecdf_midrank_and_ties():
    e = Ecdf(np.array([1.0, 2.0, 2.0, 3.0]), np.ones(4))
    assert e.percentile(0.0) == 0 and e.percentile(9.0) == 100
    assert abs(float(e.percentile(2.0)) - 50) < 1e-4


def test_area_weights_change_percentile():
    e = Ecdf(np.array([1.0, 2.0]), np.array([1.0, 3.0]))
    assert abs(float(e.percentile(1.0)) - 12.5) < 1e-4


def test_ecdf_value_at_quantile():
    e = Ecdf(np.array([1.0, 2.0, 3.0, 4.0]), np.ones(4))
    assert e.value_at(5) == 1.0 and e.value_at(50) == 2.0 and e.value_at(95) == 4.0


def grids(n=4):
    rng = np.random.default_rng(1)
    return {k: rng.uniform(0, 100, (n, n)).astype("float32")
            for k in ["relief_20km_m", "slope_20km_deg", "precip_annual_mm", ICE]}


def test_identical_cell_scores_100_and_monotone():
    g = grids()
    t = {k: float(v[0, 0]) for k, v in g.items()}
    scales = {k: 1.0 for k in g}
    s, subs, used = score_map(g, t, {"relief_20km_m": 1, "slope_20km_deg": 1}, scales)
    assert s[0, 0] == 100 and (s <= 100).all() and used == ["relief_20km_m", "slope_20km_deg"]
    assert np.argmax(s) == 0 or s.max() == 100


def test_missing_target_features_dropped_not_guessed():
    g = grids()
    s, subs, used = score_map(g, {"relief_20km_m": 50.0}, {"relief_20km_m": 1, "slope_20km_deg": 1},
                              {"relief_20km_m": 1.0, "slope_20km_deg": 1.0})
    assert used == ["relief_20km_m"] and "slope_20km_deg" not in subs


def test_zero_factor_removes_feature():
    g = grids()
    t = {"relief_20km_m": 50.0, "slope_20km_deg": 50.0}
    _, _, used = score_map(g, t, {"relief_20km_m": 1, "slope_20km_deg": 1},
                           {"relief_20km_m": 1.0, "slope_20km_deg": 1.0}, {"slope_20km_deg": 0.0})
    assert used == ["relief_20km_m"]


def test_scaled_distance_separates_cells_that_percentiles_tie():
    earth = np.log1p(np.arange(1000.0))
    ecdf = Ecdf(earth, np.ones(1000))
    scale = ecdf.value_at(95) - ecdf.value_at(5)
    target = float(np.log1p(990.0))
    near, far = np.log1p(1089.0), np.log1p(3960.0)  # 1.1x and 4x the target in metres
    assert ecdf.percentile(near) == ecdf.percentile(far) == 100
    g = {"relief_20km_m": np.array([[near, far]], "float32")}
    _, subs, _ = score_map(g, {"relief_20km_m": target}, {"relief_20km_m": 1}, {"relief_20km_m": scale})
    assert subs["relief_20km_m"][0, 0] - subs["relief_20km_m"][0, 1] > 30


def test_cold_trap_fraction_ignores_ocean_cells_in_window():
    tmax = np.full((7, 7), -5.0)
    tmax[:, 4:] = np.nan
    tmax[:, 1] = 5.0  # warm column inside the 5x5 window of column 3
    frac = cold_trap_fraction(tmax)
    assert frac[3, 3] == pytest.approx(2 / 3, abs=1e-4)
    assert np.isnan(frac[3, 4])


def test_ice_distance_uses_square_root_of_fraction():
    g = {ICE: np.array([[0.1, 0.0, 0.25]], "float32")}
    _, subs, _ = score_map(g, {ICE: 0.1}, {ICE: 1}, {})
    assert subs[ICE][0, 0] == pytest.approx(100, abs=1e-4)
    assert subs[ICE][0, 1] == pytest.approx(100 * (1 - np.sqrt(0.1)), abs=1e-3)
    assert subs[ICE][0, 2] == pytest.approx(100 * (1 - (np.sqrt(0.25) - np.sqrt(0.1))), abs=1e-3)
    assert subs[ICE][0, 1] < subs[ICE][0, 2] < subs[ICE][0, 0]


def test_measured_surface_status_halves_weight():
    assert STATUS_FACTOR["measured_surface"] == 0.5
    g = {"relief_20km_m": np.zeros((1, 1), "float32"), "slope_20km_deg": np.zeros((1, 1), "float32")}
    target = {"relief_20km_m": 0.0, "slope_20km_deg": 5.0}  # slope is maximally far (d = 1)
    s, _, used = score_map(g, target, {"relief_20km_m": 1, "slope_20km_deg": 1},
                           {"relief_20km_m": 1.0, "slope_20km_deg": 1.0},
                           {"slope_20km_deg": STATUS_FACTOR["measured_surface"]})
    assert used == ["relief_20km_m", "slope_20km_deg"]
    assert s[0, 0] == pytest.approx(100 * (1 - 0.5 / 1.5), abs=1e-3)


def test_target_values_one_sided_dryness_and_dropped_features():
    prof = {"features": {"precip_annual_mm": {"value": 0.0, "status": "one_sided_constraint"},
                         "temp_mean_c": {"value": None, "status": "missing_site_specific_literature_value"}},
            "ice_cold_trap_proxy": {"status": "not_in_mvp"}}
    vals, dropped, factor = target_values(prof)
    assert vals == {"precip_annual_mm": 0.0} and factor == {"precip_annual_mm": 1.0}
    assert dropped == {"temp_mean_c": "missing_site_specific_literature_value", ICE: "not_in_mvp"}


def test_moon_ice_target_is_diviner_area_fraction():
    prof = {"features": {}, "ice_cold_trap_proxy": {"status": "measured", "cold_trap_area_fraction": 0.1}}
    vals, dropped, factor = target_values(prof)
    assert vals == {ICE: 0.1} and factor == {ICE: 1.0} and dropped == {}


def test_thermal_cycling_available_when_mean_temperature_has_target():
    prof = {"features": {"temp_mean_c": {"value": -20.0, "status": "measured_surface"},
                         "temp_max_warmest_c": {"value": None, "status": "missing_no_source"}},
            "ice_cold_trap_proxy": {"status": "not_in_mvp"}}
    vals, _, factor = target_values(prof)
    g = {"temp_mean_c": np.zeros((2, 2), "float32")}
    _, _, used = score_map(g, vals, PRESETS["thermal_cycling"], {"temp_mean_c": 10.0}, factor)
    assert used == ["temp_mean_c"] and factor["temp_mean_c"] == 0.5


def test_rank_check_passes_at_75_and_fails_below():
    assert rank_check(75.0) == "PASS" and rank_check(74.9) == "FAIL"


def test_top_sites_separated():
    lat, lon = np.linspace(89.975, -89.975, 3600), np.linspace(-179.975, 179.975, 7200)
    s = np.full((3600, 7200), 50, "float32")
    s[1800, 3600] = 99
    s[1801, 3601] = 98  # same place: must be suppressed
    s[900, 900] = 97
    p = top_sites(s, lat, lon, n=3)
    assert [round(x["score"]) for x in p[:2]] == [99, 97]


def test_hyperarid_cell_is_close_to_zero_precip_target():
    near = transform("precip_annual_mm", 15.0) - transform("precip_annual_mm", 0.0)
    span = transform("precip_annual_mm", 2315.0) - transform("precip_annual_mm", 30.0)
    assert near / span < 0.15
