"""Phase 2 tests: PSR checks, thermal tables, targets and group summaries.

Everything expected here is either a config value or a property of the supplied
data. The tests never hard-code a target coordinate, a window, a PSR area or a
literature temperature: those live in ``config/*.yaml`` and the cited CSVs.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from backend.config import load_config
from backend.features import registry
from backend.features.registry import Availability
from backend.targets import distribution, thermal
from backend.targets.build_target_profiles import group_summary
from backend.targets.psr import (
    load_psr_table,
    parse_wkt_rings,
    rasterize_psr,
    ring_area_km2,
    verify_psr,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQUARE_WKT = "POLYGON ((0 0, 1000 0, 1000 1000, 0 1000, 0 0))"


def _require(path: Path) -> None:
    if not path.exists():
        pytest.skip(f"{path} missing; Phase 2 needs the supplied datasets")


# --- PSR parsing and rasterising ---------------------------------------------


def test_parse_wkt_rings_returns_closed_rings() -> None:
    rings = parse_wkt_rings(SQUARE_WKT)
    assert len(rings) == 1
    assert rings[0].shape == (5, 2)
    assert rings[0][0].tolist() == rings[0][-1].tolist()


def test_ring_area_matches_known_square() -> None:
    ring = parse_wkt_rings(SQUARE_WKT)[0]
    assert ring_area_km2(ring) == pytest.approx(1.0, rel=1e-6)


def test_parse_wkt_ignores_malformed_rings() -> None:
    assert parse_wkt_rings("POLYGON ((0 0, 1 1))") == []
    assert parse_wkt_rings("") == []


def test_load_psr_table_applies_the_configured_area_floor(tmp_path: Path) -> None:
    path = tmp_path / "psr.csv"
    path.write_text(
        "gid,WKT,area_km2,name\n"
        f'1,"{SQUARE_WKT}",1.0,a\n'
        f'2,"{SQUARE_WKT}",0.25,b\n',
        encoding="utf-8",
    )
    entries, info = load_psr_table(path, min_area_km2=1.0)
    assert [entry.gid for entry in entries] == ["1"]
    assert info["n_polygons"] == 1
    assert info["n_skipped_below_min_area"] == 1
    assert info["total_area_km2"] == pytest.approx(1.0)


def test_rasterize_psr_burns_the_polygon_footprint(tmp_path: Path) -> None:
    from rasterio.transform import from_origin

    path = tmp_path / "psr.csv"
    path.write_text(
        "gid,WKT,area_km2,name\n" f'1,"{SQUARE_WKT}",1.0,square\n',
        encoding="utf-8",
    )
    entries, _ = load_psr_table(path, min_area_km2=0.0)
    mask = rasterize_psr(entries, from_origin(0.0, 1000.0, 100.0, 100.0), (10, 10))
    assert mask.dtype == bool
    assert mask.sum() == 100, "a 1 km² square on 100 m pixels is 100 pixels"


# --- Distribution summaries --------------------------------------------------


def test_summarise_is_a_distribution_not_a_point(config) -> None:
    values = np.arange(101, dtype="float32")
    summary = distribution.summarise(
        values, sampled=True, percentiles=config.distribution.percentiles
    )
    assert summary["n"] == 101
    assert summary["median"] == pytest.approx(50.0)
    assert summary["p16"] == pytest.approx(16.0)
    assert summary["p84"] == pytest.approx(84.0)
    assert summary["spread"] == pytest.approx(68.0)
    assert summary["min"] == 0.0 and summary["max"] == 100.0
    assert summary["sampled"] is True


def test_summarise_reports_empty_arrays_without_inventing_numbers(config) -> None:
    summary = distribution.summarise(
        np.full(5, np.nan),
        sampled=False,
        percentiles=config.distribution.percentiles,
    )
    assert summary["n"] == 0
    assert math.isnan(summary["median"])
    assert summary["sampled"] is False


def test_profile_entry_records_how_the_window_was_resolved(config) -> None:
    definition = config.terrain_features[0]
    verdict = Availability(
        available=True,
        reason="",
        marginal=True,
        detail={"window_span_px": 2.5},
    )
    entry = distribution.profile_entry(
        definition,
        np.linspace(0.0, 10.0, 11),
        verdict,
        n_cells=100,
        sampled=True,
        percentiles=config.distribution.percentiles,
    )
    assert entry["resolution"] == "marginal"
    assert entry["window_span_px"] == 2.5
    assert entry["n_cells"] == 100
    assert entry["median"] == pytest.approx(5.0)
    assert entry["units"] == definition.units


# --- Thermal literature: cited values only -----------------------------------


def _write_thermal_csv(path: Path) -> None:
    path.write_text(
        "feature,statistic,value,units,source,notes\n"
        "temp_mean_k,median,215,K,Test 2020,\n"
        "temp_mean_k,p16,200,K,Test 2020,\n"
        "temp_mean_k,p84,230,K,Test 2020,\n"
        "temp_mean_k,min,100,K,Test 2020,\n"
        "temp_mean_k,max,400,K,Test 2020,\n",
        encoding="utf-8",
    )


def test_thermal_reader_collects_statistics(tmp_path: Path) -> None:
    path = tmp_path / "thermal.csv"
    _write_thermal_csv(path)
    table = thermal.load_thermal_table(path)
    assert table["temp_mean_k"]["units"] == "K"
    assert table["temp_mean_k"]["values"]["median"] == 215.0
    assert table["temp_mean_k"]["source"] == "Test 2020"


def test_thermal_reader_rejects_tables_without_required_columns(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad.csv"
    path.write_text("feature\nx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        thermal.load_thermal_table(path)


def test_match_thermal_features_converts_kelvin_exactly(
    config, tmp_path: Path
) -> None:
    path = tmp_path / "thermal.csv"
    _write_thermal_csv(path)
    table = thermal.load_thermal_table(path)
    availability = {
        "available": True,
        "path": str(path),
        "reason": "",
        "table": table,
    }
    entries = thermal.match_thermal_features(
        config, availability, config.targets["moon"]
    )
    entry = entries["temp_mean_c"]
    assert entry["resolution"] == "literature"
    assert entry["units"] == "degC"
    assert entry["median"] == pytest.approx(215.0 - 273.15)
    assert entry["spread"] == pytest.approx(30.0)
    assert entry["min"] == pytest.approx(100.0 - 273.15)
    assert entry["conversion"] == "K -> degC (subtract 273.15)"


def test_match_thermal_features_reports_missing_table_by_path(config) -> None:
    missing = PROJECT_ROOT / "does_not_exist" / "thermal.csv"
    availability = {
        "available": False,
        "path": str(missing),
        "reason": f"cited thermal table {missing} is not on disk",
        "table": {},
    }
    entries = thermal.match_thermal_features(
        config, availability, config.targets["moon"]
    )
    temperature = {
        definition.id
        for definition in config.all_features
        if definition.group == "temperature"
    }
    assert temperature, "config must define temperature features"
    for feature_id in temperature:
        assert entries[feature_id]["resolution"] == "unavailable"
        assert str(missing) in entries[feature_id]["resolution_note"]
        assert math.isnan(entries[feature_id]["median"])


def test_match_thermal_features_does_not_guess_a_missing_row(
    config, tmp_path: Path
) -> None:
    path = tmp_path / "thermal_other.csv"
    path.write_text(
        "feature,statistic,value,units\nunrelated_quantity,median,1.0,1\n",
        encoding="utf-8",
    )
    availability = {
        "available": True,
        "path": str(path),
        "reason": "",
        "table": thermal.load_thermal_table(path),
    }
    entries = thermal.match_thermal_features(
        config, availability, config.targets["moon"]
    )
    assert entries["temp_mean_c"]["resolution"] == "unavailable"
    assert "no row" in entries["temp_mean_c"]["resolution_note"]


# --- Group summaries and weight renormalisation ------------------------------


def _fake_profile(config, *, ice_available: bool, skip: set[str] | None = None) -> dict:
    skip = skip or set()
    features = {
        definition.id: {"resolution": "resolved"}
        for definition in config.terrain_features
        if definition.id not in skip
    }
    return {
        "features": features,
        "ice_proxy": (
            {"available": True} if ice_available else {"available": False, "reason": "no proxy"}
        ),
    }


def test_group_summary_renormalises_available_weights(config) -> None:
    profile = _fake_profile(config, ice_available=False)
    rows = group_summary(config, profile, config.targets["moon"])
    usable = [row for row in rows if row["status"] in {"available", "partial"}]
    assert usable, "terrain groups must be usable"
    assert sum(row["renormalised_weight"] for row in usable) == pytest.approx(1.0)
    for row in rows:
        if row not in usable:
            assert row["renormalised_weight"] == 0.0
    assert all(row["renormalised_weight"] == 0.0 for row in rows if row["group"] == "temperature")


def test_group_summary_marks_partial_groups(config) -> None:
    missing = next(
        definition.id
        for definition in config.terrain_features
        if definition.group == "roughness"
    )
    profile = _fake_profile(config, ice_available=True, skip={missing})
    rows = {row["group"]: row for row in group_summary(config, profile, config.targets["moon"])}
    assert rows["roughness"]["status"] == "partial"
    assert missing not in rows["roughness"]["available_members"]
    assert rows["ice_proxy"]["status"] == "available"


def test_group_summary_uses_configured_weights(config) -> None:
    profile = _fake_profile(config, ice_available=True)
    rows = group_summary(config, profile, config.targets["mars"])
    weights = {row["group"]: row["weight"] for row in rows}
    for group in config.groups:
        assert weights[group.name] == group.weight


# --- Body targets ------------------------------------------------------------


def test_moon_cap_radius_comes_from_the_configured_edge_latitude(config) -> None:
    pytest.importorskip("rasterio")
    from backend.targets.moon_target import region_geometry
    from backend.targets.geometry import polar_radius_m

    dem = config.raw_source("moon", "dem")
    _require(dem)
    import rasterio

    with rasterio.open(dem) as dataset:
        geometry = region_geometry(config, dataset)
        expected = polar_radius_m(
            dataset.crs, float(config.targets["moon"]["region"]["lat_max"])
        )
    assert geometry.radius_m == pytest.approx(expected)
    assert geometry.radius_m > 0
    assert geometry.row1 > geometry.row0 and geometry.col1 > geometry.col0


def test_psr_verification_is_consistent_with_the_dem(config) -> None:
    pytest.importorskip("rasterio")
    _require(config.raw_source("moon", "dem"))
    _require(config.raw_source("moon", "psr"))

    result = verify_psr(config)
    table = result["psr_table"]
    extent = result["extent"]
    crs = result["crs_check"]
    topo = result["topography"]

    assert extent["polygons_fully_inside_dem"] == table["n_polygons"]
    assert extent["polygons_inside_region_cap"] > 0
    assert crs["region_radius_km"] > 0
    assert topo["psr_pixel_fraction_of_region"] == pytest.approx(
        topo["psr_pixels_in_region"] / topo["region_pixels"]
    )
    assert 0.0 < topo["psr_pixel_fraction_of_region"] < 1.0
    assert set(result["verdict"]) == {
        "psr_on_lows",
        "psr_on_low_slopes",
        "region_cap_unaffected_by_corner_clip",
    }


def test_mars_profile_marks_unresolvable_windows_as_unavailable(config) -> None:
    pytest.importorskip("rasterio")
    from backend.targets.mars_target import analyse_mars

    _require(config.raw_source("mars", "dem"))
    profile = analyse_mars(config)
    mars = config.targets["mars"]

    expected = math.pi * (mars["site"]["radius_km"] * 1000.0) ** 2 / (
        mars["working_pixel_m"] ** 2
    )
    assert profile["extent"]["region_pixels_full"] == pytest.approx(expected, rel=0.01)
    assert abs(profile["site_check"]["difference_m"]) <= 100.0

    features = profile["features"]
    assert features["relief_20km_m"]["resolution"] in {"resolved", "marginal"}
    for feature_id in ("roughness_5km_m", "hurst_2_32km"):
        assert features[feature_id]["resolution"] == "unavailable"
        assert features[feature_id]["resolution_note"], feature_id
    assert features["roughness_10km_m"]["resolution"] in {"marginal", "unavailable"}

    thermal_path = Path(profile["thermal"]["path"])
    assert profile["thermal"]["available"] is thermal_path.exists()

    # Configured exclusions win over the literature table.
    for feature_id in mars.get("unavailable_features") or []:
        assert features[feature_id]["resolution"] == "unavailable"
        assert "no surface-temperature range" in features[feature_id]["resolution_note"]


def test_target_profiles_json_is_publishable(config) -> None:
    path = config.output("target_profiles")
    if not path.exists():
        pytest.skip("run python -m backend.targets.build_target_profiles first")
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["moon"]["extent"]["radius_km"] > 0
    assert payload["mars"]["extent"]["site"]["lat_deg"] == pytest.approx(
        config.targets["mars"]["site"]["lat_deg"]
    )
    for body in ("moon", "mars"):
        for entry in payload[body]["features"].values():
            assert "resolution" in entry
            assert "units" in entry
            if entry["resolution"] != "unavailable":
                assert entry["median"] is not None
