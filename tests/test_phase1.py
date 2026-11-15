"""Phase 1 tests: grid geometry, registry terrain features, published dataset.

Every expected value comes from ``config/*.yaml``: grid limits and resolution,
feature ids and windows, and validation-site coordinates and bounds.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from backend.features import registry
from backend.pipeline.earth_grid import (
    GLOBE_LAT_MAX,
    GLOBE_LAT_MIN,
    GLOBE_LON_MAX,
    GLOBE_LON_MIN,
    Tile,
    global_slices,
    iter_tiles,
    lat_centers,
    local_grid,
    lon_centers,
    sample_point_rowcol,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _feature(config, feature_id: str):
    return next(d for d in config.all_features if d.id == feature_id)


def _terrain_ids(config) -> list[str]:
    return [d.id for d in config.terrain_features]


# --- Grid geometry -----------------------------------------------------------


def test_grid_dimensions_match_resolution(config) -> None:
    spec = config.grid
    assert spec.nx * spec.resolution_deg == pytest.approx(spec.lon_max - spec.lon_min)
    assert spec.ny * spec.resolution_deg == pytest.approx(spec.lat_max - spec.lat_min)


def test_cell_centres_span_the_grid(config) -> None:
    spec = config.grid
    lat = lat_centers(spec)
    lon = lon_centers(spec)
    assert lat.shape == (spec.ny,) and lon.shape == (spec.nx,)
    assert lat[0] == pytest.approx(spec.lat_max - spec.resolution_deg / 2.0)
    assert lat[-1] == pytest.approx(spec.lat_min + spec.resolution_deg / 2.0)
    assert lon[0] == pytest.approx(spec.lon_min + spec.resolution_deg / 2.0)
    assert lon[-1] == pytest.approx(spec.lon_max - spec.resolution_deg / 2.0)
    assert np.all(np.diff(lat) < 0), "rows must run north to south"


def test_tiles_cover_the_grid_exactly_once(config) -> None:
    spec = config.grid
    covered = np.zeros((spec.ny, spec.nx), dtype=np.uint8)
    tiles = list(iter_tiles(spec))
    for tile in tiles:
        row_slice, col_slice = global_slices(tile)
        covered[row_slice, col_slice] += 1
    assert covered.min() == 1 and covered.max() == 1
    expected_tiles = int(
        np.ceil((spec.lon_max - spec.lon_min) / spec.tile_deg)
        * np.ceil((spec.lat_max - spec.lat_min) / spec.tile_deg)
    )
    assert len(tiles) == expected_tiles


def test_partial_edge_tiles_are_clipped(config) -> None:
    """A bounding box that is not a whole number of tiles still tiles cleanly."""
    from dataclasses import replace

    spec = replace(
        config.grid,
        lon_min=-17.0,
        lon_max=13.0,
        lat_min=3.0,
        lat_max=27.0,
    )
    covered = np.zeros((spec.ny, spec.nx), dtype=np.uint8)
    for tile in iter_tiles(spec):
        row_slice, col_slice = global_slices(tile)
        covered[row_slice, col_slice] += 1
    assert covered.min() == 1 and covered.max() == 1


def test_padded_bounds_stay_inside_legal_lonlat(config) -> None:
    spec = config.grid
    corners = [
        (spec.lat_min, spec.lon_min),
        (spec.lat_max - spec.tile_deg, spec.lon_max - spec.tile_deg),
    ]
    for lat0, lon0 in corners:
        tile = next(
            tile
            for tile in iter_tiles(spec)
            if tile.lat0 == lat0 and tile.lon0 == lon0
        )
        lon_min, lat_min, lon_max, lat_max = tile.padded_bounds
        assert GLOBE_LON_MIN <= lon_min < lon_max <= GLOBE_LON_MAX
        assert GLOBE_LAT_MIN <= lat_min < lat_max <= GLOBE_LAT_MAX


def test_local_grid_is_metric_aeqd(config) -> None:
    tile = next(iter(iter_tiles(config.grid)))
    transform, width, height, crs = local_grid(tile)
    assert crs.is_projected
    assert crs.to_dict()["proj"] == "aeqd"
    assert transform.a == pytest.approx(config.grid.working_pixel_m)
    assert width > 0 and height > 0


def test_sample_point_rowcol_is_inverse_for_cell_centres(config) -> None:
    spec = config.grid
    lat = lat_centers(spec)[100]
    lon = lon_centers(spec)[200]
    row, col = sample_point_rowcol(spec, lat, lon)
    assert (row, col) == (100, 200)


# --- Registry terrain features ----------------------------------------------


def _plane(config, size: int = 129, gradient: float = 0.0, offset: float = 1000.0) -> np.ndarray:
    pixel = config.grid.working_pixel_m
    rows = np.arange(size, dtype="float32")[:, None]
    return (offset + gradient * rows * pixel) * np.ones((size, size), dtype="float32")


def _terrain(config, dem: np.ndarray, land: np.ndarray | None = None):
    return registry.compute_all(
        config.terrain_features,
        dem,
        config.grid.working_pixel_m,
        config.comparability,
        land=land,
        native_pixel_m=config.earth.native_pixel_m,
    )


def test_window_px_uses_kilometres(config) -> None:
    window = _feature(config, "relief_20km_m").params["window_km"]
    assert registry.window_pixels(window, 2_000.0) == int(np.ceil(window / 2.0))
    assert registry.window_pixels(0.5, 2_000.0) == 1


def test_flat_surface_has_no_relief_slope_or_roughness(config) -> None:
    features, status = _terrain(config, _plane(config, gradient=0.0))
    assert all(verdict.available for verdict in status.values())
    assert np.nanmax(features["relief_20km_m"]) < 1e-3
    assert np.nanmax(features["slope_20km_deg"]) < 1e-3
    for definition in config.terrain_features:
        if definition.group == "roughness":
            assert np.nanmax(features[definition.id]) < 1e-3


def test_constant_slope_is_recovered(config) -> None:
    gradient = 0.1  # 10 % rise, i.e. 5.7106 degrees
    features, _ = _terrain(config, _plane(config, gradient=gradient))
    expected = float(np.degrees(np.arctan(gradient)))
    assert np.nanmedian(features["slope_20km_deg"]) == pytest.approx(expected, rel=1e-3)


def test_roughness_grows_with_window_for_white_noise(config) -> None:
    rng = np.random.default_rng(7)
    noise = rng.normal(0.0, 50.0, size=(129, 129)).astype("float32")
    features, _ = _terrain(config, noise)
    rough = {
        _feature(config, d.id).params["window_km"]: np.nanmedian(features[d.id])
        for d in config.terrain_features
        if d.group == "roughness"
    }
    ordered = [value for _, value in sorted(rough.items())]
    assert ordered == sorted(ordered), f"roughness should grow with window: {rough}"
    assert ordered[-1] > 0


def test_hurst_is_near_one_for_a_ramp_and_low_for_white_noise(config) -> None:
    hurst_id = next(d.id for d in config.terrain_features if d.function == "hurst")
    ramp = _plane(config, size=257, gradient=0.05)
    ramp_hurst, _ = _terrain(config, ramp)
    assert np.nanmedian(ramp_hurst[hurst_id][60:-60, 60:-60]) == pytest.approx(1.0, abs=0.15)

    rng = np.random.default_rng(11)
    noise = rng.normal(0.0, 100.0, size=(257, 257)).astype("float32")
    noise_hurst, _ = _terrain(config, noise)
    assert np.nanmedian(noise_hurst[hurst_id][60:-60, 60:-60]) < 0.25


def test_features_handle_nan_and_stay_finite(config) -> None:
    data = _plane(config, size=129, gradient=0.02)
    data[0:3, :] = np.nan
    features, _ = _terrain(config, data)
    for name, values in features.items():
        assert np.isfinite(values).all(), f"{name} has non-finite values after NaN fill"


def test_ocean_bathymetry_does_not_inflate_coastal_relief(config) -> None:
    elevation = np.full((65, 65), -4_000.0, dtype="float32")
    elevation[:, 32:] = 1_000.0
    land = np.zeros((65, 65), dtype=bool)
    land[:, 32:] = True

    raw, _ = _terrain(config, elevation)
    assert np.nanmax(raw["relief_20km_m"]) > 4_000.0, "test setup should span bathymetry"

    filled, _ = _terrain(config, elevation, land=land)
    assert np.nanmax(filled["relief_20km_m"]) < 1.0
    assert np.nanmax(filled["slope_20km_deg"]) < 1.0


def test_large_window_percentile_matches_exact_when_subsampled(config) -> None:
    """The approximation path must stay close to the exact percentile filter."""
    from scipy.ndimage import percentile_filter

    rng = np.random.default_rng(3)
    smooth = rng.normal(0.0, 100.0, size=(300, 300)).astype("float32")
    size = config.comparability.exact_percentile_max_px * 2
    exact = percentile_filter(smooth, 95, size=size, mode="nearest")
    approximate = registry.local_percentile(smooth, size, 95, config.comparability)
    assert approximate.shape == exact.shape
    difference = np.abs(approximate - exact)
    assert np.nanmedian(difference) < 25.0
    assert np.nanpercentile(difference, 99) < 120.0


# --- Published dataset -------------------------------------------------------


@pytest.fixture(scope="module")
def dataset(config):
    xarray = pytest.importorskip("xarray")
    path = config.output("earth_features")
    if not path.exists():
        pytest.skip(f"{path.name} missing; run python -m backend.pipeline.build_earth_features")
    ds = xarray.open_dataset(path)
    yield ds
    ds.close()


@pytest.fixture(scope="module")
def meta(config) -> dict:
    path = config.output("earth_meta")
    if not path.exists():
        pytest.skip(f"{path.name} missing; run the Phase 1 pipeline")
    return json.loads(path.read_text(encoding="utf-8"))


def test_dataset_shape_and_coordinates(dataset, config) -> None:
    spec = config.grid
    assert dataset.sizes == {"lat": spec.ny, "lon": spec.nx}
    assert float(dataset.lat[0]) == pytest.approx(spec.lat_max - spec.resolution_deg / 2.0)
    assert float(dataset.lat[-1]) == pytest.approx(spec.lat_min + spec.resolution_deg / 2.0)
    assert float(dataset.lon[0]) == pytest.approx(spec.lon_min + spec.resolution_deg / 2.0)
    assert float(dataset.lon[-1]) == pytest.approx(spec.lon_max - spec.resolution_deg / 2.0)


def test_all_configured_variables_are_present(dataset, config) -> None:
    spec = config.grid
    for definition in config.all_features:
        assert definition.id in dataset, f"missing variable {definition.id}"
        assert dataset[definition.id].shape == (spec.ny, spec.nx)
        assert dataset[definition.id].dtype == np.float32
    for name in ("land_mask", "land_fraction"):
        assert name in dataset


def test_land_mask_is_binary_and_covers_expected_area(dataset, config) -> None:
    spec = config.grid
    mask = dataset.land_mask.values
    assert set(np.unique(mask)) <= {0, 1}
    cell_fraction = float(mask.mean())
    assert 0.25 < cell_fraction < 0.40

    lat = np.deg2rad(dataset.lat.values)
    weights = np.cos(lat)[:, None] * np.ones((1, spec.nx))
    area_fraction = float((weights * mask).sum() / weights.sum())
    assert 0.25 < area_fraction < 0.33, "area-weighted land should be near 29%"


def test_features_are_nan_over_ocean_and_finite_over_land(dataset, config) -> None:
    mask = dataset.land_mask.values.astype(bool)
    ocean = ~mask
    for definition in config.all_features:
        values = dataset[definition.id].values
        assert np.isnan(values[ocean]).all(), f"{definition.id} leaks over the ocean"
        valid = np.isfinite(values[mask]).mean()
        assert valid > 0.99, f"{definition.id} only covers {valid:.2%} of land"


def test_feature_ranges_are_physical(dataset, config) -> None:
    ranges = {
        "relief": (0.0, np.inf),
        "slope": (0.0, 90.0),
        "roughness": (0.0, np.inf),
        "scale_robust_roughness": (0.0, 1.5),
    }
    for definition in config.all_features:
        if definition.group not in ranges:
            continue
        values = dataset[definition.id].values
        finite = values[np.isfinite(values)]
        low, high = ranges[definition.group]
        assert finite.min() >= low, definition.id
        assert finite.max() <= high, definition.id
    assert -60.0 < np.nanmin(dataset["temp_mean_c"].values) < np.nanmax(
        dataset["temp_mean_c"].values
    ) < 35.0


def test_polar_land_is_present(dataset, config) -> None:
    mask = dataset.land_mask.values.astype(bool)
    lat = dataset.lat.values
    polar = config.report.polar_circle_deg
    assert int((mask & (lat[:, None] >= polar)).sum()) > 0, "no Arctic land"
    assert int((mask & (lat[:, None] <= -polar)).sum()) > 0, "no Antarctic land"
    antarctic_limit = config.targets["moon"]["region"]["lat_max"]
    assert int((mask & (lat[:, None] <= antarctic_limit)).sum()) > 0, (
        f"Antarctica missing at {antarctic_limit}S"
    )


def test_configured_sites_meet_their_expectations(dataset, config) -> None:
    """Bounds come from config/validation_sites.yaml, not from this file."""
    spec = config.grid
    checked = 0
    for site in config.validation_sites:
        row, col = sample_point_rowcol(spec, site.lat, site.lon)
        for feature_id, bounds in site.expect.items():
            value = float(dataset[feature_id].values[row, col])
            assert np.isfinite(value), f"{site.name} has no {feature_id}"
            if "min" in bounds:
                assert value >= bounds["min"], f"{site.name} {feature_id}={value:g} < {bounds['min']}"
            if "max" in bounds:
                assert value <= bounds["max"], f"{site.name} {feature_id}={value:g} > {bounds['max']}"
            checked += 1
    assert checked >= len(config.validation_sites), "expectations were not exercised"


def test_metadata_matches_configuration(meta, config) -> None:
    spec = config.grid
    assert meta["grid"]["nx"] == spec.nx and meta["grid"]["ny"] == spec.ny
    assert meta["grid"]["resolution_deg"] == pytest.approx(spec.resolution_deg)
    assert meta["grid"]["lon_min"] == pytest.approx(spec.lon_min)
    assert meta["grid"]["lat_max"] == pytest.approx(spec.lat_max)
    names = {row["name"] for row in meta["features"]}
    assert names == {definition.id for definition in config.all_features}
    assert "coverage" in meta and "limitations" in meta
    assert meta["config"]["feature_ids"] == [d.id for d in config.all_features]


def test_report_and_figures_exist(config) -> None:
    report = config.output("earth_report")
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    spec = config.grid
    for expected in (
        f"{spec.resolution_deg:g}",
        "ETOPO",
        "WorldClim",
        config.validation_sites[0].name,
    ):
        assert expected in text, f"report is missing {expected!r}"

    figures_dir = config.outputs.figures_dir
    prefix = config.outputs.figure_prefix
    figures = list(figures_dir.glob(f"{prefix}*.png"))
    assert len(figures) >= len(config.all_features) + 1
    overview = figures_dir / config.outputs.overview_figure
    assert overview.exists() and overview.stat().st_size > 50_000


def test_stored_resolution_status_is_recorded(dataset, config) -> None:
    """Marginal windows are flagged in the product, not silently trusted."""
    for definition in config.terrain_features:
        assert "resolution_status" in dataset[definition.id].attrs
        assert dataset[definition.id].attrs["resolution_status"] in {
            "resolved",
            "marginal",
            "unavailable",
        }
