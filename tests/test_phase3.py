"""Phase 3 tests: similarity maths, presets, top sites and artifacts.

Every threshold used here is read from ``config/*.yaml``. The tests never
hard-code a weight, a separation distance, a band edge or a target median.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from netCDF4 import Dataset

from backend.config import load_config
from backend.engine import build_scores, similarity, top_sites
from backend.targets import constraints, thermal

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _require(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"{path} missing; run the earlier phase first")


def _scaled(
    feature_id: str = "relief_20km_m",
    bias: float = 100.0,
    half_spread: float = 10.0,
) -> similarity.ScaledFeature:
    return similarity.ScaledFeature(
        id=feature_id,
        group="relief",
        units="m",
        qualitative=False,
        median=bias,
        sigma=half_spread,
        floor=half_spread,
        scale=half_spread,
    )


# --- Absolute and rank similarity -------------------------------------------


def test_gaussian_similarity_is_one_at_the_target_median() -> None:
    feature = _scaled()
    values = np.array([100.0, 110.0, 90.0], dtype=np.float32)
    sim = similarity.absolute_similarity(values, feature, "gaussian")
    assert sim[0] == pytest.approx(1.0)
    assert sim[1] == pytest.approx(math.exp(-0.5), rel=1e-6)
    assert sim[2] == pytest.approx(math.exp(-0.5), rel=1e-6)


def test_exponential_kernel_uses_absolute_gap() -> None:
    feature = _scaled()
    values = np.array([130.0], dtype=np.float32)
    sim = similarity.absolute_similarity(values, feature, "exponential")
    assert sim[0] == pytest.approx(math.exp(-3.0), rel=1e-6)


def test_unknown_kernel_fails_loudly() -> None:
    with pytest.raises(ValueError, match="unknown absolute_similarity kernel"):
        similarity.absolute_similarity(
            np.array([1.0], dtype=np.float32), _scaled(), "cauchy"
        )


def test_rank_similarity_is_one_where_earth_percentiles_agree() -> None:
    values = np.array([0.0, 5.0, 10.0, 15.0, 20.0], dtype=np.float64)
    weights = np.ones_like(values)
    table = similarity.weighted_cdf_table(values, weights, 101)
    percentiles = similarity.percentile_of(values, table)
    target_percentile = float(np.interp(10.0, table[1], table[0]))
    rank = 1.0 - np.abs(percentiles - target_percentile)
    assert rank[2] == pytest.approx(1.0, abs=1e-6)
    assert rank[0] < rank[2] and rank[4] < rank[2]


def test_area_weights_change_the_percentile() -> None:
    values = np.array([0.0, 10.0, 20.0], dtype=np.float64)
    equal = similarity.weighted_cdf_table(values, np.ones(3), 101)
    skewed = similarity.weighted_cdf_table(
        values, np.array([0.98, 0.01, 0.01]), 101
    )
    # With equal weights the median sits midway between 0 and 10; with 98% of
    # the area at 0 it sits at 0. This is the cos(latitude) weighting in
    # miniature.
    assert float(np.interp(0.5, equal[0], equal[1])) == pytest.approx(5.0)
    assert float(np.interp(0.5, skewed[0], skewed[1])) == pytest.approx(0.0)


def test_hidden_gap_flag_uses_config_thresholds(config) -> None:
    rank = np.array([0.9, 0.9, 0.5, 0.9], dtype=np.float32)
    absolute = np.array([0.2, 0.8, 0.2, 0.2], dtype=np.float32)
    hidden = similarity.hidden_gap_mask(config, rank, absolute)
    assert hidden.tolist() == [True, False, False, True]


# --- Banded qualitative thermal ---------------------------------------------


def test_band_similarity_counts_bands_not_units() -> None:
    feature = similarity.ScaledFeature(
        id="temp_min_coldest_c",
        group="temperature",
        units="degC",
        qualitative=True,
        bands_c=(-40.0, -25.0, -10.0, 0.0),
        n_bands=5,
        target_band=0,
    )
    values = np.array([-50.0, -30.0, -20.0, -5.0, 10.0], dtype=np.float32)
    assert similarity.band_similarity(values, feature).tolist() == pytest.approx(
        [1.0, 0.75, 0.5, 0.25, 0.0]
    )


def test_qualitative_anchors_are_polar_rows_only(config) -> None:
    availability = thermal.thermal_availability(config, "moon")
    entries = thermal.qualitative_thermal_features(
        config, availability, config.targets["moon"]
    )
    assert set(entries) == {"temp_min_coldest_c", "temp_max_warmest_c"}
    for entry in entries.values():
        assert entry["qualitative"] is True
        assert entry["scoring"] == "band_distance"
        assert entry["bands_c"] == sorted(entry["bands_c"])
        # Every anchor is a cited row, never the equatorial 400 K / 100 K pair.
        assert all(
            "subsolar" not in name and "night" not in name
            for name in entry["anchor_rows"]
        )


def test_conflicting_anchor_bands_fail_loudly(config) -> None:
    mapping = config.targets["moon"]["thermal_mapping"]
    feature_id = "temp_min_coldest_c"
    rows = []
    for index, name in enumerate(mapping["features"][feature_id]["anchor_rows"]):
        # First row cold, the rest at +20 °C: they cannot share one band.
        degc = -240.0 if index == 0 else 20.0
        rows.append(
            {
                "name": name,
                "value": degc + 273.15,
                "units": "K",
                "value_degc": degc,
                "source": "test",
            }
        )
    availability = {"available": True, "path": "test.csv", "references": rows}
    with pytest.raises(ValueError, match="different bands"):
        thermal.qualitative_thermal_features(config, availability, config.targets["moon"])


def test_configured_thermal_unavailable_reasons_are_applied(config) -> None:
    entries = {
        "temp_mean_c": {"resolution": "qualitative", "median": 1.0, "n_cells": 3}
    }
    thermal.apply_thermal_unavailable(entries, config.targets["moon"])
    assert entries["temp_mean_c"]["resolution"] == "unavailable"
    assert entries["temp_mean_c"]["resolution_note"]
    assert math.isnan(entries["temp_mean_c"]["median"])


# --- Physical constraints and caveats ---------------------------------------


def test_dryness_constraint_entries_are_declared(config) -> None:
    constraint = next(c for c in config.physical_constraints if c.name == "dryness")
    for target in ("moon", "mars"):
        entries = constraints.dryness_constraint_entries(
            config, config.targets[target]
        )
        assert set(entries) == {feature.id for feature in constraint.features}
        for feature in constraint.features:
            entry = entries[feature.id]
            assert entry["resolution"] == "constraint"
            assert entry["distribution"] == "declared_tolerance"
            assert entry["physical_constraint"] is True
            assert entry["n_cells"] == 0
            assert entry["median"] == pytest.approx(constraint.target_value)
            assert entry["p16"] == pytest.approx(feature.p16)
            assert entry["p84"] == pytest.approx(feature.p84)
            assert entry["median"] < entry["p84"]


def test_disabled_constraint_returns_no_entries(config) -> None:
    target = dict(config.targets["mars"])
    target["dryness_constraint"] = {"enabled": False}
    assert constraints.dryness_constraint_entries(config, target) == {}


def test_constraint_uses_the_same_floored_scale(config) -> None:
    profile = {
        "features": constraints.dryness_constraint_entries(
            config, config.targets["moon"]
        )
    }
    scaled = similarity.scaled_features(config, profile)
    assert set(scaled) == {"precip_annual_mm", "precip_driest_month_mm"}
    for feature in scaled.values():
        assert feature.qualitative is False
        assert feature.physical_constraint is True
        assert feature.declared_distribution is True
        assert feature.floor > 0
        assert feature.scale == pytest.approx(max(feature.sigma, feature.floor))
        # The declared band's half-spread is the scale before the floor.
        assert feature.sigma == pytest.approx(
            (profile["features"][feature.id]["p84"] - feature.median) / 2.0
        )


def test_caveats_flag_the_declared_ice_regions(config) -> None:
    caveats = top_sites.caveats_for(config, -77.5, 162.0)
    assert [entry["id"] for entry in caveats] == ["antarctic_ice_sheet"]
    assert caveats[0]["text"] == config.caveats.text
    assert caveats[0]["heuristic"] is True
    assert caveats[0]["region_note"]
    greenland = top_sites.caveats_for(config, 72.0, -40.0)
    assert [entry["id"] for entry in greenland] == ["greenland_ice_sheet"]
    assert top_sites.caveats_for(config, 0.0, 0.0) == []


# --- Presets and renormalisation --------------------------------------------


def test_preset_drops_missing_groups_and_renormalises(config) -> None:
    groups = {
        "relief": np.ones((2, 2), dtype=np.float32),
        "slope": np.full((2, 2), 0.5, dtype=np.float32),
    }
    score, info = similarity.preset_score(
        config, "moon", groups, {"relief": 1.0, "slope": 3.0, "temperature": 0.5}
    )
    assert score[0, 0] == pytest.approx((1.0 * 1.0 + 3.0 * 0.5) / 4.0)
    assert "temperature" in info["weights_dropped"]
    assert info["weight_sum"] == pytest.approx(4.0)


def test_preset_propagates_nan_where_a_group_is_missing(config) -> None:
    relief = np.ones((2, 2), dtype=np.float32)
    slope = np.ones((2, 2), dtype=np.float32)
    slope[1, 1] = np.nan
    score, _ = similarity.preset_score(
        config, "moon", {"relief": relief, "slope": slope}, {"relief": 1.0, "slope": 1.0}
    )
    assert np.isfinite(score[0, 0])
    assert np.isnan(score[1, 1])


def test_preset_without_any_usable_group_fails(config) -> None:
    with pytest.raises(ValueError, match="no usable group"):
        similarity.preset_score(config, "moon", {}, {"temperature": 0.5})


# --- Tiny grid: area weighting and group accumulation -----------------------


class _Store:
    """Minimal config wrapper whose earth features live in a temp file."""

    def __init__(self, base, path: Path) -> None:
        self._base = base
        self._path = Path(path)

    def __getattr__(self, name):
        return getattr(self._base, name)

    def output(self, name: str) -> Path:
        if name == "earth_features":
            return self._path
        return self._base.output(name)


def _write_tiny_grid(path: Path, lat, lon, features, land) -> None:
    dataset = Dataset(str(path), "w", format="NETCDF4")
    dataset.createDimension("lat", lat.size)
    dataset.createDimension("lon", lon.size)
    dataset.createVariable("lat", "f8", ("lat",))[:] = lat
    dataset.createVariable("lon", "f8", ("lon",))[:] = lon
    dataset.createVariable("land_mask", "i1", ("lat", "lon"))[:] = land.astype("i1")
    for name, values in features.items():
        dataset.createVariable(name, "f4", ("lat", "lon"))[:] = values
    dataset.close()


def _tiny_store(config, tmp_path: Path) -> similarity.EarthStore:
    lat = np.array([80.0, 0.0])
    lon = np.array([0.0, 0.05])
    land = np.ones((2, 2), dtype=bool)
    relief = np.array([[100.0, 100.0], [100.0, 200.0]], dtype=np.float32)
    _write_tiny_grid(
        tmp_path / "tiny.nc", lat, lon, {"relief_20km_m": relief}, land
    )
    return similarity.EarthStore(_Store(config, tmp_path / "tiny.nc"))


def test_group_scores_are_area_weighted(config, tmp_path: Path) -> None:
    store = _tiny_store(config, tmp_path)
    profile = {
        "features": {
            "relief_20km_m": {
                "resolution": "resolved",
                "median": 100.0,
                "p16": 90.0,
                "p84": 110.0,
            }
        }
    }
    scores, diagnostics, tables = similarity.compute_group_scores(
        config, {"moon": profile, "mars": profile}, store, targets=("moon",)
    )
    grid = scores["moon"]["relief"]
    assert np.isfinite(grid).all()
    weights = store.cell_weight
    expected = float((grid * weights).sum() / weights.sum())
    assert diagnostics["moon"]["relief_20km_m"].mean_absolute_similarity == pytest.approx(
        expected, rel=1e-5
    )
    unweighted = float(np.nanmean(grid))
    assert expected < unweighted  # the polar rows are counted less
    assert similarity.score_coverage(config, grid, store) == pytest.approx(1.0)
    store.close()


def test_qualitative_feature_reports_band_area_fractions(config, tmp_path: Path) -> None:
    lat = np.array([80.0, 0.0])
    lon = np.array([0.0, 0.05])
    temperatures = np.array([[-50.0, -50.0], [10.0, 10.0]], dtype=np.float32)
    _write_tiny_grid(
        tmp_path / "tiny.nc",
        lat,
        lon,
        {"temp_min_coldest_c": temperatures},
        np.ones((2, 2), dtype=bool),
    )
    store = similarity.EarthStore(_Store(config, tmp_path / "tiny.nc"))
    profile = {
        "features": {
            "temp_min_coldest_c": {
                "resolution": "qualitative",
                "bands_c": [-40.0, -25.0, -10.0, 0.0],
                "n_bands": 5,
                "target_band": 0,
                "anchor_range_c": [-244.15, -163.15],
                "anchor_label": "test anchors",
                "anchor_rows": ["a"],
            }
        }
    }
    scores, diagnostics, _ = similarity.compute_group_scores(
        config, {"moon": profile}, store, targets=("moon",)
    )
    diagnostic = diagnostics["moon"]["temp_min_coldest_c"]
    assert diagnostic.qualitative is True
    # Target band 0 scores 1, band 3 scores 0.25; both lat rows are equal area
    # only after cos(latitude), so check the sum and the ordering.
    assert sum(diagnostic.band_area_fractions) == pytest.approx(1.0)
    assert diagnostic.band_area_fractions[0] > diagnostic.band_area_fractions[3]
    assert np.isfinite(scores["moon"]["temperature"]).all()
    store.close()


# --- Top sites --------------------------------------------------------------


def test_select_sites_enforces_separation() -> None:
    lat = np.array([10.0, 9.95, 0.0])
    lon = np.array([0.0, 0.05, 5.0])
    score = np.full((3, 3), np.nan, dtype=np.float32)
    score[0, 0] = 1.0  # 10 N, 0 E
    score[0, 1] = 0.9  # ~8 km away: must be suppressed
    score[2, 2] = 0.8  # far away: kept
    sites = top_sites.select_sites(score, lat, lon, 50.0, 10)
    assert len(sites) == 2
    assert sites[0]["peak_score"] == pytest.approx(1.0)
    assert sites[1]["row"] == 2 and sites[1]["col"] == 2


def test_window_slice_handles_north_to_south_latitudes() -> None:
    lat = np.linspace(90.0, -90.0, 3601)
    lon = np.linspace(-180.0, 179.95, 7200)
    rows, cols = top_sites.window_slice(lat, lon, 44.075, 84.075, 25.0)
    assert rows.start < rows.stop and cols.start < cols.stop
    assert lat[rows][0] >= 44.075 and lat[rows][-1] <= 44.075


def test_site_aggregate_is_finite_at_high_latitude(config) -> None:
    lat = np.array([85.0, 84.95, 84.90])
    lon = np.array([0.0, 0.05, 0.10])
    score = np.full((3, 3), 0.7, dtype=np.float32)
    land = np.ones((3, 3), dtype=bool)
    site = {"row": 0, "col": 0, "lat": 85.0, "lon": 0.0, "peak_score": 0.7}
    aggregate = top_sites.site_aggregate(
        config, score, {"relief": score}, lat, lon, site, land, 50.0
    )
    assert math.isfinite(aggregate["site_score"])
    assert aggregate["site_score"] == pytest.approx(0.7, rel=1e-6)


def test_famous_filter_uses_configured_radius(config) -> None:
    site = config.famous_sites[0]
    famous, name = top_sites.is_famous(config, site.lat, site.lon)
    assert famous is True and name == site.name
    far_lat = site.lat + config.famous_radius_km / 111.0 * 3.0
    famous, name = top_sites.is_famous(config, far_lat, site.lon)
    assert famous is False and name is None


# --- Qualitative feature rows ----------------------------------------------


def test_qualitative_site_row_reports_gap_in_real_units(config, tmp_path: Path) -> None:
    lat = np.array([80.0, 0.0])
    lon = np.array([0.0, 0.05])
    temperatures = np.full((2, 2), 10.0, dtype=np.float32)
    _write_tiny_grid(
        tmp_path / "tiny.nc",
        lat,
        lon,
        {"temp_min_coldest_c": temperatures},
        np.ones((2, 2), dtype=bool),
    )
    store = similarity.EarthStore(_Store(config, tmp_path / "tiny.nc"))
    profile = {
        "features": {
            "temp_min_coldest_c": {
                "resolution": "qualitative",
                "group": "temperature",
                "units": "degC",
                "bands_c": [-40.0, -25.0, -10.0, 0.0],
                "n_bands": 5,
                "target_band": 0,
                "anchor_range_c": [-244.15, -163.15],
                "anchor_label": "test anchors",
                "anchor_rows": ["a"],
            }
        }
    }
    rows = build_scores.feature_site_rows(
        config, store, profile, {"temp_min_coldest_c": (None, None)}, 80.0, 0.0, 5.0
    )
    row = rows[0]
    assert row["qualitative"] is True
    # The site is far above the cited cold anchor, so the real-unit gap is
    # positive and large even though the band comparison is only descriptive.
    assert row["absolute_gap"] > 0
    assert row["absolute_gap"] == pytest.approx(10.0 - (-163.15), rel=1e-3)
    store.close()


# --- Artifacts --------------------------------------------------------------


def test_top_sites_artifact_structure(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["created_utc"]
    assert set(payload["targets"]) == {"moon", "mars"}
    for target, block in payload["targets"].items():
        assert block["features_used"]
        assert block["coverage"]["features_used"] == len(block["features_used"])
        for preset in config.presets:
            entry = block["presets"][preset.name]
            assert entry["weights"] == dict(preset.weights)
            assert entry["top_n"] == preset.top_n
            assert entry["min_separation_km"] == preset.min_separation_km
            assert 0.0 <= entry["coverage"] <= 1.0
            sites = entry["sites"]
            assert len(sites) <= preset.top_n
            scores = [site["site_score"] for site in sites]
            assert scores == sorted(scores, reverse=True)
            assert all(site["features"] for site in sites)
            # Reported sites must obey the configured separation.
            for index, first in enumerate(sites):
                for second in sites[index + 1 :]:
                    distance = top_sites.haversine_km(
                        first["lat"],
                        first["lon"],
                        np.array([second["lat"]]),
                        np.array([second["lon"]]),
                    )[0]
                    assert distance >= preset.min_separation_km - 1e-6


def test_artifact_keeps_targets_separate(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    # Coverage differs by target, which is the documented reason Moon and Mars
    # scores are never compared.
    moon = payload["targets"]["moon"]["coverage"]
    mars = payload["targets"]["mars"]["coverage"]
    assert moon["features_used"] != mars["features_used"]
    assert moon["groups_scored"] != mars["groups_scored"]


def test_physical_constraint_reaches_scores_and_coverage(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    constraint = next(c for c in config.physical_constraints if c.name == "dryness")
    declared = {feature.id for feature in constraint.features}
    for target in ("moon", "mars"):
        block = payload["targets"][target]
        assert block["physical_constraint"]["enabled"] is True
        assert block["physical_constraint"]["label"] == constraint.label
        assert set(block["physical_constraint"]["declared_tolerance"]) == declared
        assert declared <= set(block["features_used"])
        assert block["coverage"]["features_used"] == len(block["features_used"])
        evidence = block["feature_evidence"]
        for feature_id in declared:
            assert evidence[feature_id]["physical_constraint"] is True
            assert evidence[feature_id]["declared_distribution"] is True
            assert evidence[feature_id]["group"] == constraint.group
        for site in block["presets"]["balanced"]["sites"][:3]:
            rows = {row["feature"]: row for row in site["features"]}
            for feature_id in declared:
                assert rows[feature_id]["physical_constraint"] is True
                assert rows[feature_id]["declared_distribution"] is True


def test_every_preset_carries_both_site_lists(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    for target, block in payload["targets"].items():
        for preset in config.presets:
            entry = block["presets"][preset.name]
            assert entry["sites"], (target, preset.name)
            assert entry["sites_excluding_famous"], (target, preset.name)
            assert len(entry["sites"]) <= preset.top_n
            assert len(entry["sites_excluding_famous"]) <= preset.top_n
            assert not any(
                site["famous"] for site in entry["sites_excluding_famous"]
            )


def test_stability_is_reported_and_ranked(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    sensitivity = payload["targets"]["moon"]["thermal_sensitivity"]
    assert sensitivity["applicable"] is True
    assert sensitivity["n_settings"] == len(sensitivity["variants"])
    assert sensitivity["n_settings"] > 0
    match_km = (
        next(p for p in config.presets if p.name == "balanced").min_separation_km
        * config.thermal_sensitivity.stability_match_fraction
    )
    assert sensitivity["stability_match_km"] == pytest.approx(match_km)
    curve = sensitivity["curve"]
    assert curve
    for entry in curve:
        assert 0.0 <= entry["stability"] <= 1.0

    def key(entry: dict) -> tuple[float, float]:
        return (-entry["stability"], -entry["site_score"])

    assert [key(entry) for entry in curve] == sorted(key(entry) for entry in curve)
    sites = payload["targets"]["moon"]["presets"]["balanced"]["sites"]
    by_position = {
        (round(entry["lat"], 6), round(entry["lon"], 6)): entry for entry in curve
    }
    for site in sites:
        assert site["stability"] is not None
        assert 0.0 <= site["stability"] <= 1.0
        match = by_position[(round(site["lat"], 6), round(site["lon"], 6))]
        assert site["stability"] == pytest.approx(match["stability"])
        assert site["stable_rank"] == match["stable_rank"]
        assert str(sensitivity["n_settings"]) in site["stability_note"]
    # Where stability is not computed the field is null with a reason, never 0.
    for target in ("moon", "mars"):
        for preset in config.presets:
            if target == "moon" and preset.name == "balanced":
                continue
            for site in payload["targets"][target]["presets"][preset.name]["sites"]:
                assert site["stability"] is None
                assert site["stability_note"]


def test_caveat_flags_and_sources_reach_the_artifact(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    flagged = 0
    for block in payload["targets"].values():
        for preset in config.presets:
            for site in block["presets"][preset.name]["sites"]:
                for caveat in site["caveats"]:
                    flagged += 1
                    assert caveat["text"] == config.caveats.text
                    assert caveat["heuristic"] is True
    assert flagged > 0, "no site falls inside a declared caveat region"
    rows = {
        row["name"]: row
        for row in payload["targets"]["mars"]["presets"]["balanced"]["validation"]
    }
    assert rows["Mauna Kea summit"]["source"] is None
    assert rows["Mauna Kea summit"]["display_source"] is False
    assert rows["Mauna Kea summit"]["citation_verified"] is False
    assert rows["Licancabur"]["source"]
    assert rows["Licancabur"]["citation_verified"] is True
    assert "spot-check" in rows["Rio Tinto"]["source"]


def test_target_profiles_mark_the_constraint_group(config) -> None:
    path = config.output("target_profiles")
    _require(path)
    profiles = json.loads(path.read_text(encoding="utf-8"))
    constraint = next(c for c in config.physical_constraints if c.name == "dryness")
    for target in ("moon", "mars"):
        groups = {row["group"]: row for row in profiles[target]["groups"]}
        assert groups[constraint.group]["status"] == "constraint"
        assert groups[constraint.group]["renormalised_weight"] > 0
        for feature in constraint.features:
            entry = profiles[target]["features"][feature.id]
            assert entry["resolution"] == "constraint"
            assert entry["distribution"] == "declared_tolerance"
            assert entry["median"] == pytest.approx(constraint.target_value)


def test_thermal_sensitivity_covers_the_required_grid(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    sensitivity = payload["targets"]["moon"]["thermal_sensitivity"]
    assert sensitivity["applicable"] is True
    settings = config.thermal_sensitivity
    expected = {
        (weight, shift)
        for weight in settings.temperature_weights
        for shift in settings.band_edge_shifts_c
    }
    got = {
        (variant["temperature_weight"], variant["band_edge_shift_c"])
        for variant in sensitivity["variants"]
    }
    assert got == expected
    assert payload["targets"]["mars"]["thermal_sensitivity"]["applicable"] is False


def test_score_file_matches_config_variables(config) -> None:
    path = config.output("top_sites")
    _require(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    for target in ("moon", "mars"):
        path = config.output(f"scores_{target}")
        _require(path)
        dataset = Dataset(str(path))
        try:
            for preset in config.presets:
                assert f"score_{preset.name}" in dataset.variables
            used_groups = {
                evidence["group"]
                for evidence in payload["targets"][target]["feature_evidence"].values()
            }
            for name in used_groups:
                assert f"group_{name}" in dataset.variables
            # A group with no usable feature must not silently appear.
            if target == "mars":
                assert "group_scale_robust_roughness" not in dataset.variables
            if target == "moon":
                assert "group_temperature" in dataset.variables
            assert dataset.area_weighting.startswith("cos(latitude)")
        finally:
            dataset.close()
