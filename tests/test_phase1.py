"""Phase 1 tests: grid geometry, synthetic terrain features, and the published dataset."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from backend.paths import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR
from backend.pipeline.earth_grid import (
    LAT_MAX,
    LON_MIN,
    NX,
    NY,
    RES_DEG,
    Tile,
    global_slices,
    lat_centers,
    lon_centers,
    local_grid,
)
from backend.pipeline.earth_terrain import (
    _window_px,
    compute_terrain_features,
    hurst_exponent,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET = PROCESSED_DIR / "earth_features.nc"
META = PROCESSED_DIR / "earth_features_meta.json"

TERRAIN_FEATURES = [
    "relief_20km_m",
    "slope_20km_deg",
    "roughness_5km_m",
    "roughness_10km_m",
    "roughness_20km_m",
    "hurst_2_32km",
]
CLIMATE_FEATURES = [
    "temp_mean_c",
    "temp_diurnal_range_c",
    "temp_max_warmest_c",
    "temp_min_coldest_c",
    "temp_annual_range_c",
    "precip_annual_mm",
    "precip_driest_month_mm",
]


# --- Grid geometry -----------------------------------------------------------


def test_grid_dimensions_match_resolution() -> None:
    assert NX == 7200 and NY == 3600
    assert RES_DEG == pytest.approx(0.05)


def test_cell_centres_span_the_globe() -> None:
    lat = lat_centers()
    lon = lon_centers()
    assert lat.shape == (NY,) and lon.shape == (NX,)
    assert lat[0] == pytest.approx(89.975, abs=1e-9)
    assert lat[-1] == pytest.approx(-89.975, abs=1e-9)
    assert lon[0] == pytest.approx(-179.975, abs=1e-9)
    assert lon[-1] == pytest.approx(179.975, abs=1e-9)
    assert np.all(np.diff(lat) < 0), "rows must run north to south"


def test_tile_slices_tile_the_grid_without_gaps() -> None:
    """All 648 core tiles must exactly cover 7200 x 3600 cells."""
    covered = np.zeros((NY, NX), dtype=np.uint8)
    tiles = 0
    for lat0 in np.arange(-90.0, 90.0, 10.0):
        for lon0 in np.arange(-180.0, 180.0, 10.0):
            tile = Tile(lat0=float(lat0), lon0=float(lon0))
            row_slice, col_slice = global_slices(tile)
            assert row_slice.stop - row_slice.start == 200
            assert col_slice.stop - col_slice.start == 200
            covered[row_slice, col_slice] += 1
            tiles += 1
    assert tiles == 648
    assert covered.min() == 1 and covered.max() == 1


def test_padded_bounds_stay_inside_legal_lonlat() -> None:
    for lat0, lon0 in ((-90.0, -180.0), (80.0, 170.0)):
        lon_min, lat_min, lon_max, lat_max = Tile(lat0, lon0).padded_bounds
        assert lon_min >= -180.0 and lon_max <= 180.0
        assert lat_min >= -90.0 and lat_max <= 90.0


def test_local_grid_is_metric_aeqd() -> None:
    transform, width, height, crs = local_grid(Tile(lat0=0.0, lon0=0.0), pixel_m=2_000.0)
    assert crs.is_projected
    assert crs.to_dict()["proj"] == "aeqd"
    assert transform.a == pytest.approx(2_000.0)
    assert width > 500 and height > 500


# --- Synthetic terrain features ---------------------------------------------


def _plane(size: int = 129, gradient: float = 0.0, offset: float = 1000.0) -> np.ndarray:
    rows = np.arange(size, dtype="float32")[:, None]
    return (offset + gradient * rows * 2_000.0) * np.ones((size, size), dtype="float32")


def test_window_px_uses_kilometres() -> None:
    assert _window_px(20.0, 2_000.0) == 10
    assert _window_px(20.0, 1_000.0) == 20
    assert _window_px(0.5, 2_000.0) == 1


def test_flat_surface_has_no_relief_slope_or_roughness() -> None:
    features = compute_terrain_features(_plane(gradient=0.0), pixel_m=2_000.0)
    assert np.nanmax(features["relief_20km_m"]) < 1e-3
    assert np.nanmax(features["slope_20km_deg"]) < 1e-3
    for name in ("roughness_5km_m", "roughness_10km_m", "roughness_20km_m"):
        assert np.nanmax(features[name]) < 1e-3


def test_constant_slope_is_recovered() -> None:
    gradient = 0.1  # 10 % rise, i.e. 5.7106 degrees
    features = compute_terrain_features(_plane(gradient=gradient), pixel_m=2_000.0)
    expected = float(np.degrees(np.arctan(gradient)))
    assert np.nanmedian(features["slope_20km_deg"]) == pytest.approx(expected, rel=1e-3)
    # Relief over a 20 km window on a constant ramp is about 0.1 * 20 km.
    interior = features["relief_20km_m"][30:-30, 30:-30]
    assert np.nanmedian(interior) == pytest.approx(2_000.0, rel=0.2)


def test_roughness_grows_with_window_for_white_noise() -> None:
    rng = np.random.default_rng(7)
    noise = rng.normal(0.0, 50.0, size=(129, 129)).astype("float32")
    features = compute_terrain_features(noise, pixel_m=2_000.0)
    assert np.nanmedian(features["roughness_5km_m"]) < np.nanmedian(
        features["roughness_20km_m"]
    )
    assert np.nanmedian(features["roughness_10km_m"]) > 0


def test_hurst_is_near_one_for_a_ramp_and_low_for_white_noise() -> None:
    ramp = _plane(size=257, gradient=0.05)
    ramp_hurst = hurst_exponent(ramp, pixel_m=2_000.0)
    assert np.nanmedian(ramp_hurst[60:-60, 60:-60]) == pytest.approx(1.0, abs=0.15)

    rng = np.random.default_rng(11)
    noise = rng.normal(0.0, 100.0, size=(257, 257)).astype("float32")
    noise_hurst = hurst_exponent(noise, pixel_m=2_000.0)
    assert np.nanmedian(noise_hurst[60:-60, 60:-60]) < 0.25


def test_features_handle_nan_and_stay_finite() -> None:
    data = _plane(size=129, gradient=0.02)
    data[0:3, :] = np.nan
    features = compute_terrain_features(data, pixel_m=2_000.0)
    for name, values in features.items():
        assert np.isfinite(values).all(), f"{name} has non-finite values after NaN fill"


def test_ocean_bathymetry_does_not_inflate_coastal_relief() -> None:
    elevation = np.full((65, 65), -4_000.0, dtype="float32")
    elevation[:, 32:] = 1_000.0
    land = np.zeros((65, 65), dtype=bool)
    land[:, 32:] = True

    raw = compute_terrain_features(elevation, pixel_m=2_000.0)
    assert np.nanmax(raw["relief_20km_m"]) > 4_000.0, "test setup should span bathymetry"

    filled = compute_terrain_features(elevation, pixel_m=2_000.0, land=land)
    assert np.nanmax(filled["relief_20km_m"]) < 1.0
    assert np.nanmax(filled["slope_20km_deg"]) < 1.0


# --- Published dataset -------------------------------------------------------


requires_dataset = pytest.mark.skipif(
    not DATASET.exists(),
    reason="run python -m backend.pipeline.build_earth_features first",
)


@pytest.fixture(scope="module")
def dataset():
    xarray = pytest.importorskip("xarray")
    ds = xarray.open_dataset(DATASET)
    yield ds
    ds.close()


@requires_dataset
def test_dataset_shape_and_coordinates(dataset) -> None:
    assert dataset.sizes == {"lat": NY, "lon": NX}
    assert float(dataset.lat[0]) == pytest.approx(89.975)
    assert float(dataset.lat[-1]) == pytest.approx(-89.975)
    assert float(dataset.lon[0]) == pytest.approx(-179.975)
    assert float(dataset.lon[-1]) == pytest.approx(179.975)


@requires_dataset
def test_all_mvp_variables_are_present(dataset) -> None:
    for name in TERRAIN_FEATURES + CLIMATE_FEATURES + ["land_mask", "land_fraction"]:
        assert name in dataset, f"missing variable {name}"
        assert dataset[name].shape == (NY, NX)
        assert dataset[name].dtype == np.float32 or name == "land_mask"


@requires_dataset
def test_land_mask_is_binary_and_covers_expected_area(dataset) -> None:
    mask = dataset.land_mask.values
    assert set(np.unique(mask)) <= {0, 1}
    cell_fraction = float(mask.mean())
    assert 0.25 < cell_fraction < 0.40

    lat = np.deg2rad(dataset.lat.values)
    weights = np.cos(lat)[:, None] * np.ones((1, NX))
    area_fraction = float((weights * mask).sum() / weights.sum())
    assert 0.25 < area_fraction < 0.33, "area-weighted land should be near 29%"


@requires_dataset
def test_features_are_nan_over_ocean_and_mostly_finite_over_land(dataset) -> None:
    mask = dataset.land_mask.values.astype(bool)
    ocean = ~mask
    for name in TERRAIN_FEATURES + CLIMATE_FEATURES:
        values = dataset[name].values
        assert np.isnan(values[ocean]).all(), f"{name} leaks over the ocean"
        valid = np.isfinite(values[mask]).mean()
        assert valid > 0.99, f"{name} only covers {valid:.2%} of land"


@requires_dataset
def test_feature_ranges_are_physical(dataset) -> None:
    def land_values(name: str) -> np.ndarray:
        values = dataset[name].values
        return values[np.isfinite(values)]

    assert land_values("relief_20km_m").min() >= 0.0
    assert land_values("slope_20km_deg").max() < 90.0
    for name in ("roughness_5km_m", "roughness_10km_m", "roughness_20km_m"):
        assert land_values(name).min() >= 0.0
    hurst = land_values("hurst_2_32km")
    assert hurst.min() >= 0.0 and hurst.max() <= 1.5
    assert -60.0 < land_values("temp_mean_c").min() < land_values("temp_mean_c").max() < 35.0
    assert land_values("precip_annual_mm").min() >= 0.0
    assert land_values("precip_driest_month_mm").min() >= 0.0


@requires_dataset
def test_polar_land_is_present(dataset) -> None:
    mask = dataset.land_mask.values.astype(bool)
    lat = dataset.lat.values
    assert int((mask & (lat[:, None] >= 66.5)).sum()) > 0, "no Arctic land"
    assert int((mask & (lat[:, None] <= -66.5)).sum()) > 0, "no Antarctic land"
    assert int((mask & (lat[:, None] <= -85.0)).sum()) > 0, "Antarctica missing at 85S"


@requires_dataset
def test_known_sites_have_plausible_values(dataset) -> None:
    def sample(name: str, site_lat: float, site_lon: float) -> float:
        row = int(round((LAT_MAX - site_lat) / RES_DEG - 0.5))
        col = int(round((site_lon - LON_MIN) / RES_DEG - 0.5))
        return float(dataset[name].values[row, col])

    # Atacama: cold-ish, hyper-arid.
    assert sample("temp_mean_c", -23.5, -68.5) < 20.0
    assert sample("precip_annual_mm", -23.5, -68.5) < 50.0
    # Sahara: hot and dry.
    assert sample("temp_mean_c", 23.0, 10.0) > 20.0
    assert sample("precip_annual_mm", 23.0, 10.0) < 50.0
    # Amazon: hot and wet.
    assert sample("temp_mean_c", -3.0, -60.0) > 24.0
    assert sample("precip_annual_mm", -3.0, -60.0) > 1_500.0
    # Dry Valleys, Antarctica: below freezing, dry.
    assert sample("temp_mean_c", -77.5, 162.0) < -15.0
    assert sample("precip_annual_mm", -77.5, 162.0) < 100.0


@requires_dataset
def test_metadata_and_report_exist() -> None:
    assert META.exists()
    metadata = json.loads(META.read_text(encoding="utf-8"))
    assert metadata["grid"]["nx"] == NX and metadata["grid"]["ny"] == NY
    assert len(metadata["features"]) == len(TERRAIN_FEATURES + CLIMATE_FEATURES)
    names = {row["name"] for row in metadata["features"]}
    assert names == set(TERRAIN_FEATURES + CLIMATE_FEATURES)
    assert "coverage" in metadata and "limitations" in metadata

    report = DOCS_DIR / "earth_grid_report.md"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    for expected in ("0.05", "ETOPO", "WorldClim", "Antarctica", "Atacama"):
        assert expected in text


@requires_dataset
def test_overview_figure_exists() -> None:
    figures = list(FIGURES_DIR.glob("earth_*.png"))
    assert len(figures) >= len(TERRAIN_FEATURES + CLIMATE_FEATURES) + 1
    overview = FIGURES_DIR / "earth_features_overview.png"
    assert overview.exists() and overview.stat().st_size > 50_000
