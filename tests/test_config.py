"""Config layer tests: YAML is the single source of project settings."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from backend.config import PROJECT_ROOT, load_config
from backend.features import registry
from backend.features.registry import FUNCTIONS


def _raw(name: str) -> dict:
    with (PROJECT_ROOT / "config" / name).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def test_all_config_files_exist() -> None:
    for name in (
        "config.yaml",
        "features.yaml",
        "paths.yaml",
        "targets.yaml",
        "validation_sites.yaml",
    ):
        assert (PROJECT_ROOT / "config" / name).exists(), name


def test_grid_values_come_from_yaml(config) -> None:
    raw = _raw("config.yaml")["grid"]
    for key, value in raw.items():
        assert getattr(config.grid, key) == value
    assert config.grid.nx == int(round((config.grid.lon_max - config.grid.lon_min) / config.grid.resolution_deg))
    assert config.grid.ny == int(round((config.grid.lat_max - config.grid.lat_min) / config.grid.resolution_deg))


def test_feature_registry_is_complete(config) -> None:
    ids = [definition.id for definition in config.all_features]
    assert len(ids) == len(set(ids)), "duplicate feature ids"
    for definition in config.all_features:
        assert definition.function in FUNCTIONS, definition.function
        assert definition.units
        assert definition.label


def test_groups_reference_known_features(config) -> None:
    known = {definition.id for definition in config.all_features}
    assert config.groups, "no scoring groups configured"
    for group in config.groups:
        assert set(group.members) <= known, f"{group.name} has unknown members"
        # A scored group must carry weight; a context-only group (PSR area
        # fraction) is deliberately zero-weight because Earth has no map for it.
        if group.scored:
            assert group.weight > 0, f"{group.name} is scored but weightless"
        else:
            assert group.weight == 0, f"{group.name} is context only but weighted"


def test_validation_sites_come_from_yaml(config) -> None:
    raw = _raw("validation_sites.yaml")["sites"]
    assert [site.name for site in config.validation_sites] == [site["name"] for site in raw]
    for site, raw_site in zip(config.validation_sites, raw):
        assert site.lat == pytest.approx(raw_site["lat"])
        assert site.lon == pytest.approx(raw_site["lon"])
        assert set(site.expect) <= {definition.id for definition in config.all_features}


def test_window_override_changes_only_that_feature() -> None:
    base = load_config()
    proof = load_config(override="config/proofs/window_30km.yaml")
    base_relief = next(f for f in base.terrain_features if f.id == "relief_20km_m")
    proof_relief = next(f for f in proof.terrain_features if f.id == "relief_20km_m")
    assert base_relief.params["window_km"] != proof_relief.params["window_km"]
    assert proof_relief.params["window_km"] == pytest.approx(30.0)
    # Every other feature is untouched.
    base_others = {f.id: f.params for f in base.terrain_features if f.id != "relief_20km_m"}
    proof_others = {f.id: f.params for f in proof.terrain_features if f.id != "relief_20km_m"}
    assert base_others == proof_others
    # The grid is untouched by this proof.
    assert proof.grid.bounds == base.grid.bounds


def test_bounding_box_override_changes_grid_only() -> None:
    base = load_config()
    proof = load_config(override="config/proofs/sahara.yaml")
    assert proof.grid.bounds == (-20.0, 10.0, 40.0, 40.0)
    assert proof.grid.nx == 1200 and proof.grid.ny == 600
    assert proof.terrain_features == base.terrain_features
    assert proof.output("earth_features") != base.output("earth_features")
    assert proof.output("earth_report").name == "proof_sahara_report.md"


def test_unknown_feature_override_is_rejected(tmp_path: Path) -> None:
    override = tmp_path / "bad.yaml"
    override.write_text(
        "features.yaml:\n  overrides:\n    not_a_feature:\n      params:\n        window_km: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="unknown ids"):
        load_config(override=override)


def test_missing_config_directory_is_reported(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing configuration file"):
        load_config(config_dir=tmp_path)


def test_distribution_settings_come_from_yaml(config) -> None:
    raw = _raw("config.yaml")["distribution"]
    assert config.distribution.sample_stride_px == raw["sample_stride_px"]
    assert config.distribution.percentiles == tuple(
        float(value) for value in raw["percentiles"]
    )


def test_targets_come_from_yaml(config) -> None:
    raw = _raw("targets.yaml")
    assert config.targets["moon"]["region"]["lat_max"] == raw["moon"]["region"]["lat_max"]
    assert config.targets["moon"]["region"]["lat_min"] == raw["moon"]["region"]["lat_min"]
    for key, value in raw["mars"]["site"].items():
        assert config.targets["mars"]["site"][key] == value
    assert config.targets["mars"]["native_pixel_m"] == raw["mars"]["native_pixel_m"]


def test_output_routing(config) -> None:
    assert config.output("earth_features").parent == config.outputs.processed_dir
    assert config.output("earth_report").parent == config.outputs.docs_dir
    with pytest.raises(KeyError):
        config.output("no_such_output")


def test_targets_are_values_not_code(config) -> None:
    moon = config.targets["moon"]
    mars = config.targets["mars"]
    assert -90.0 <= moon["region"]["lat_min"] < moon["region"]["lat_max"] <= 90.0
    assert moon["region"]["lat_max"] == pytest.approx(-85.0)
    assert mars["site"]["lon_deg_east"] == pytest.approx(77.5945)
    assert mars["site"]["elevation_m"] == pytest.approx(-2656.0)
    assert mars["site"]["radius_km"] > 0
    # Mars has no surface-temperature range in the supplied literature.
    assert "temp_diurnal_range_c" in mars["unavailable_features"]
    assert "temp_annual_range_c" in mars["unavailable_features"]


def test_source_files_are_configured(config) -> None:
    assert config.raw_source("earth", "terrain").name == config.sources["earth"]["terrain"]
    for body in ("earth", "moon", "mars"):
        assert body in config.sources
    assert config.raw_source("mars", "dem").suffix == ".img"
    assert set(config.sources["earth"]["climate"]) == {
        str(definition.params["file_key"]) for definition in config.climate_features
    }


def test_comparability_thresholds_are_ordered(config) -> None:
    options = config.comparability
    assert 0 < options.min_window_pixels < options.marginal_window_pixels
    assert options.min_hurst_lags >= 2
    assert options.min_lag_pixels > 0
    assert options.exact_percentile_max_px >= 2
    assert options.approx_percentile_window_px >= 2


def test_availability_is_body_aware(config) -> None:
    """Earth keeps every MVP feature; Mars loses the small windows (config-driven)."""
    options = config.comparability
    native = {
        "earth": config.earth.native_pixel_m,
        "moon": config.targets["moon"]["native_pixel_m"],
        "mars": config.targets["mars"]["native_pixel_m"],
    }
    status = {
        body: {
            definition.id: registry.availability(definition, px, options, native[body])
            for definition in config.terrain_features
        }
        for body, px in (
            ("earth", config.grid.working_pixel_m),
            ("moon", config.targets["moon"]["working_pixel_m"]),
            ("mars", config.targets["mars"]["working_pixel_m"]),
        )
    }
    assert all(v.available for v in status["earth"].values())
    assert all(v.available for v in status["moon"].values())
    assert status["earth"]["roughness_5km_m"].resolution == "marginal"
    assert not status["mars"]["roughness_5km_m"].available
    assert status["mars"]["roughness_10km_m"].resolution == "marginal"
    assert status["mars"]["relief_20km_m"].resolution == "resolved"
    assert not status["mars"]["hurst_2_32km"].available
    # Every unavailable verdict explains itself.
    for body in status.values():
        for verdict in body.values():
            if not verdict.available:
                assert "km per pixel" in verdict.reason
