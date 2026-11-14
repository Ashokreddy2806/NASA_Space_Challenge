"""Phase 1 terrain pipeline: ETOPO 2022 → global 0.05° terrain features.

For each 10°×10° tile the native 1-arc-minute ETOPO DEM is reprojected to a
local azimuthal-equidistant grid at 2 km. Relief, slope, multi-scale roughness
and a Hurst exponent are computed there in kilometre-sized windows, then
sampled back onto the common 0.05° search grid.

ETOPO includes bathymetry, so coastal land cells would otherwise see the
continental shelf inside their 20 km window and get spurious relief and slope.
Ocean cells are therefore filled with the nearest land elevation before any
filtering, using the WorldClim land mask from ``earth_climate.nc``.

Run from ``NASA_Space_Challenge/`` (after ``backend.pipeline.earth_climate``)::

    python -m backend.pipeline.earth_terrain

Output: ``data/processed/earth_terrain.nc`` (unmasked; the climate script adds
the WorldClim land mask and ``build_earth_features.py`` writes the final dataset).
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import numpy as np
import rasterio
from netCDF4 import Dataset
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.windows import Window
from rasterio.warp import reproject
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    percentile_filter,
    uniform_filter,
)

from backend.paths import PROCESSED_DIR, RAW
from backend.pipeline.earth_grid import (
    ETOPO_PATH,
    LAT_MAX,
    LOCAL_PIXEL_M,
    LON_MIN,
    RES_DEG,
    TILE_DEG,
    Tile,
    global_slices,
    iter_tiles,
    local_grid,
)
from backend.pipeline.feature_store import GridStore

FEATURE_ATTRS = {
    "relief_20km_m": {
        "long_name": "Local relief in a 20 km window",
        "units": "m",
        "definition": "p95 - p5 of the DEM within 20 km; robust to single-cell artefacts",
    },
    "slope_20km_deg": {
        "long_name": "Mean slope in a 20 km window",
        "units": "degrees",
        "definition": "mean of atan(|grad z|) over 20 km",
    },
    "roughness_5km_m": {
        "long_name": "High-pass roughness at 5 km",
        "units": "m",
        "definition": "std of DEM residual (Gaussian high-pass) in a 5 km window",
    },
    "roughness_10km_m": {
        "long_name": "High-pass roughness at 10 km",
        "units": "m",
        "definition": "std of DEM residual (Gaussian high-pass) in a 10 km window",
    },
    "roughness_20km_m": {
        "long_name": "High-pass roughness at 20 km",
        "units": "m",
        "definition": "std of DEM residual (Gaussian high-pass) in a 20 km window",
    },
    "hurst_2_32km": {
        "long_name": "Scale-robust roughness (Hurst exponent)",
        "units": "unitless",
        "definition": "0.5 * slope of log structure function vs log lag for lags 2-32 km",
    },
}


def read_etopo_window(dataset: rasterio.DatasetReader, tile: Tile) -> tuple[np.ndarray, object]:
    """Read the ETOPO window covering a tile plus halo; fill nodata with NaN."""
    lon_min, lat_min, lon_max, lat_max = tile.padded_bounds
    row0, col0 = dataset.index(lon_min, lat_max)
    row1, col1 = dataset.index(lon_max, lat_min)
    row0 = max(0, row0 - 1)
    col0 = max(0, col0 - 1)
    row1 = min(dataset.height, row1 + 1)
    col1 = min(dataset.width, col1 + 1)
    window = Window(col0, row0, col1 - col0, row1 - row0)
    data = dataset.read(1, window=window, masked=True).astype("float32")
    return np.ma.filled(data, np.nan), dataset.window_transform(window)


def read_land_window(climate: Dataset, tile: Tile) -> tuple[np.ndarray, object]:
    """Read the 0.05° WorldClim land-fraction window covering a tile plus halo."""
    lon_min, lat_min, lon_max, lat_max = tile.padded_bounds
    variable = climate.variables["land_fraction"]
    rows, cols = variable.shape
    row0 = max(0, int(np.floor((LAT_MAX - lat_max) / RES_DEG)))
    row1 = min(rows, int(np.ceil((LAT_MAX - lat_min) / RES_DEG)))
    col0 = max(0, int(np.floor((lon_min - LON_MIN) / RES_DEG)))
    col1 = min(cols, int(np.ceil((lon_max - LON_MIN) / RES_DEG)))
    values = np.asarray(variable[row0:row1, col0:col1], dtype="float32")
    west = LON_MIN + col0 * RES_DEG
    north = LAT_MAX - row0 * RES_DEG
    return values, from_origin(west, north, RES_DEG, RES_DEG)


def _fill_nan_nearest(array: np.ndarray) -> np.ndarray:
    """Fill NaN cells with the nearest finite value (edges only, no invention)."""
    if np.isfinite(array).all():
        return array
    mask = ~np.isfinite(array)
    indices = distance_transform_edt(mask, return_distances=False, return_indices=True)
    return array[tuple(indices)]


def _window_px(km: float, pixel_m: float) -> int:
    """Window size in pixels, at least one cell."""
    return max(1, int(np.ceil(km * 1000.0 / pixel_m)))


def _local_std(array: np.ndarray, size: int) -> np.ndarray:
    """Standard deviation in a square moving window."""
    mean = uniform_filter(array, size=size, mode="nearest")
    mean_sq = uniform_filter(array * array, size=size, mode="nearest")
    return np.sqrt(np.maximum(mean_sq - mean * mean, 0.0)).astype("float32")


def hurst_exponent(
    elevation: np.ndarray,
    pixel_m: float,
    lags_km: tuple[float, ...] = (2, 4, 8, 16, 32),
    window_km: float = 32.0,
) -> np.ndarray:
    """Estimate the Hurst exponent from the elevation structure function.

    For fractional Brownian topography, ``E[(z(x+L)-z(x))^2] ∝ L^(2H)``.
    The local log-log slope is computed for lags from 2 to 32 km. A flat or
    noiseless surface has no usable scaling and is returned as NaN.
    """
    lags_px = [max(1, int(round(lag * 1000.0 / pixel_m))) for lag in lags_km]
    window_px = _window_px(window_km, pixel_m)
    structure: list[np.ndarray] = []
    for lag in lags_px:
        diff_x = np.zeros_like(elevation, dtype="float32")
        diff_y = np.zeros_like(elevation, dtype="float32")
        valid = np.zeros_like(elevation, dtype="float32")
        diff_x[:, lag:] = (elevation[:, lag:] - elevation[:, :-lag]) ** 2
        diff_y[lag:, :] = (elevation[lag:, :] - elevation[:-lag, :]) ** 2
        valid[:, lag:] = 1.0
        valid[lag:, :] += 1.0
        numerator = uniform_filter(diff_x + diff_y, size=window_px, mode="nearest")
        denominator = uniform_filter(valid, size=window_px, mode="nearest")
        structure.append(np.maximum(numerator / np.maximum(denominator, 1e-6), 1e-12))

    log_structure = np.log(np.stack(structure, axis=0))
    log_lags = np.log(np.asarray(lags_km, dtype="float32"))
    centered = log_lags - log_lags.mean()
    denominator = float(np.sum(centered**2))
    local_slope = np.sum(
        centered[:, None, None] * (log_structure - log_structure.mean(axis=0)), axis=0
    ) / denominator
    hurst = 0.5 * local_slope
    return np.clip(hurst, 0.0, 1.5).astype("float32")


def compute_terrain_features(
    elevation: np.ndarray,
    pixel_m: float,
    land: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Compute the six MVP terrain features on a local metric DEM.

    ``land`` is an optional boolean mask on the same grid. Ocean cells are
    replaced by the nearest land elevation before filtering, so bathymetry
    cannot inflate coastal relief, slope or roughness. The ocean cells are
    masked out of the published product later.
    """
    elevation = _fill_nan_nearest(np.asarray(elevation, dtype="float32"))
    if land is not None:
        land = np.asarray(land, dtype=bool)
        if land.any() and not land.all():
            ocean = ~land
            indices = distance_transform_edt(
                ocean, return_distances=False, return_indices=True
            )
            elevation = elevation.copy()
            elevation[ocean] = elevation[tuple(indices)][ocean]
    window_20 = _window_px(20.0, pixel_m)

    relief = (
        percentile_filter(elevation, 95, size=window_20, mode="nearest")
        - percentile_filter(elevation, 5, size=window_20, mode="nearest")
    ).astype("float32")

    gradient_y, gradient_x = np.gradient(elevation, pixel_m, pixel_m)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y))).astype("float32")
    slope = uniform_filter(slope, size=window_20, mode="nearest").astype("float32")

    roughness: dict[str, np.ndarray] = {}
    for window_km in (5.0, 10.0, 20.0):
        sigma_px = max(0.75, (window_km / 2.0) * 1000.0 / pixel_m)
        residual = elevation - gaussian_filter(elevation, sigma=sigma_px, mode="nearest")
        roughness[f"roughness_{int(window_km)}km_m"] = _local_std(
            residual.astype("float32"), _window_px(window_km, pixel_m)
        )

    return {
        "relief_20km_m": relief,
        "slope_20km_deg": slope,
        **roughness,
        "hurst_2_32km": hurst_exponent(elevation, pixel_m),
    }


def reproject_to_local(
    source: np.ndarray,
    source_transform: object,
    tile: Tile,
    land_source: np.ndarray | None = None,
    land_transform: object | None = None,
) -> tuple[np.ndarray, np.ndarray | None, object, object]:
    """Reproject a lon/lat window to the tile's local metric grid.

    When ``land_source`` is supplied (WorldClim land fraction), it is reprojected
    to the same local grid and returned as a boolean land mask.
    """
    destination_transform, width, height, destination_crs = local_grid(tile)
    destination = np.full((height, width), np.nan, dtype="float32")
    reproject(
        source=source,
        destination=destination,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        dst_transform=destination_transform,
        dst_crs=destination_crs,
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )

    land = None
    if land_source is not None and land_transform is not None:
        fraction = np.zeros((height, width), dtype="float32")
        reproject(
            source=land_source,
            destination=fraction,
            src_transform=land_transform,
            src_crs="EPSG:4326",
            dst_transform=destination_transform,
            dst_crs=destination_crs,
            src_nodata=np.nan,
            dst_nodata=0.0,
            resampling=Resampling.bilinear,
        )
        land = fraction >= 0.5
    return destination, land, destination_transform, destination_crs


def reproject_feature_to_global(
    feature: np.ndarray,
    source_transform: object,
    source_crs: object,
    tile: Tile,
) -> np.ndarray:
    """Sample a local metric feature onto the tile's 0.05° core window."""
    row_slice, col_slice = global_slices(tile)
    height = row_slice.stop - row_slice.start
    width = col_slice.stop - col_slice.start
    destination = np.full((height, width), np.nan, dtype="float32")

    reproject(
        source=feature,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=from_origin(tile.lon0, tile.lat0 + TILE_DEG, RES_DEG, RES_DEG),
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.average,
    )
    return destination


def build_terrain(
    output: Path,
    pixel_m: float = LOCAL_PIXEL_M,
    limit_tiles: int | None = None,
    climate_path: Path | None = None,
) -> None:
    """Run the terrain pipeline and write the intermediate NetCDF store."""
    climate_path = climate_path or PROCESSED_DIR / "earth_climate.nc"
    if not climate_path.exists():
        raise FileNotFoundError(
            f"{climate_path} not found; run `python -m backend.pipeline.earth_climate` first"
        )
    if output.exists():
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    started = time.perf_counter()
    tile_count = 0
    source_path = RAW["earth"] / ETOPO_PATH
    with GridStore(output, mode="w") as store:
        arrays = {
            name: store.create_feature(name, attrs) for name, attrs in FEATURE_ATTRS.items()
        }
        with Dataset(climate_path) as climate, rasterio.open(source_path) as dataset:
            for tile in iter_tiles():
                if limit_tiles is not None and tile_count >= limit_tiles:
                    break
                source, source_transform = read_etopo_window(dataset, tile)
                land_source, land_transform = read_land_window(climate, tile)
                local, land, local_transform, local_crs_value = reproject_to_local(
                    source, source_transform, tile, land_source, land_transform
                )
                features = compute_terrain_features(local, pixel_m, land=land)
                row_slice, col_slice = global_slices(tile)
                for name, array in arrays.items():
                    sampled = reproject_feature_to_global(
                        features[name], local_transform, local_crs_value, tile
                    )
                    array[row_slice, col_slice] = sampled
                tile_count += 1
                if tile_count % 50 == 0:
                    elapsed = time.perf_counter() - started
                    print(f"  terrain: {tile_count} tiles, {elapsed:.1f} s")

        store.set_attrs(
            {
                "title": "Earth terrain features on a 0.05 degree grid",
                "source": "ETOPO 2022 v1 60 arc-second surface elevation (NOAA NCEI)",
                "source_doi": "10.25921/fd45-gt74",
                "grid": "global 0.05 degree lon/lat, north-to-south rows",
                "working_grid": f"local azimuthal equidistant, {pixel_m / 1000:.1f} km pixels",
                "coastal_handling": (
                    "ocean cells filled with the nearest land elevation (WorldClim land "
                    "mask) before filtering, so bathymetry cannot inflate coastal features"
                ),
                "tiles_processed": tile_count,
                "runtime_seconds": round(time.perf_counter() - started, 1),
                "land_mask": "not applied here; see earth_climate.nc",
            }
        )
    print(f"Wrote {output} ({tile_count} tiles, {time.perf_counter() - started:.1f} s)")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROCESSED_DIR / "earth_terrain.nc"
    )
    parser.add_argument("--pixel-m", type=float, default=LOCAL_PIXEL_M)
    parser.add_argument("--limit-tiles", type=int, default=None)
    parser.add_argument(
        "--climate", type=Path, default=PROCESSED_DIR / "earth_climate.nc"
    )
    args = parser.parse_args()
    build_terrain(
        args.output,
        pixel_m=args.pixel_m,
        limit_tiles=args.limit_tiles,
        climate_path=args.climate,
    )


if __name__ == "__main__":
    main()
