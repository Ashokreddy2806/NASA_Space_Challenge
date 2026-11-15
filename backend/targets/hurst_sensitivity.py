"""Earth Hurst robustness: does the fit survive dropping the 2 km lag?

ETOPO 2022 is a 60 arc-second product (~1.85 km), so the 2 km lag in the
configured Hurst list is close to the sampling limit. This check draws random
land cells, reads a real ETOPO patch around each one, reprojects it to the same
local metric grid the terrain pipeline uses, and computes the Hurst exponent
twice: with the full configured lag list and with the 2 km lag removed.

Interpretation is data-driven and thresholded from ``config.yaml``: if the
median shift is small and the two estimates stay highly correlated, the fitted
exponent is not an artefact of the shortest lag.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import rasterio
import xarray as xr
from pyproj import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject

from backend.config import AppConfig, FeatureDefinition, load_config
from backend.features import registry


def _random_land_points(config: AppConfig, count: int) -> tuple[np.ndarray, np.ndarray]:
    """Draw reproducible random land cell centres from the published Earth grid."""
    path = config.output("earth_features")
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing; run the Phase 1 pipeline before the Hurst check"
        )
    with xr.open_dataset(path) as dataset:
        mask = dataset.land_mask.values.astype(bool)
        lat = dataset.lat.values.copy()
        lon = dataset.lon.values.copy()
    rows, cols = np.nonzero(mask)
    rng = np.random.default_rng(config.hurst_sensitivity.random_seed)
    take = min(count, rows.size)
    chosen = rng.choice(rows.size, size=take, replace=False)
    return lat[rows[chosen]], lon[cols[chosen]]


def _read_patch(
    dataset: rasterio.DatasetReader,
    lat: float,
    lon: float,
    patch_km: float,
    pixel_m: float,
) -> np.ndarray | None:
    """Read and reproject one ETOPO patch to a local metric grid."""
    half_m = patch_km * 1000.0 / 2.0
    half_deg = patch_km / 2.0 / 111.32
    lon_half = min(180.0, half_deg / max(np.cos(np.radians(lat)), 0.01))
    lat_min = max(-90.0, lat - half_deg)
    lat_max = min(90.0, lat + half_deg)
    lon_min, lon_max = lon - lon_half, lon + lon_half
    if lon_min < -180.0:
        lon_min, lon_max = -180.0, min(180.0, lon_max + 360.0)
    if lon_max > 180.0:
        lon_max = 180.0

    window = dataset.window(lon_min, lat_min, lon_max, lat_max)
    source = dataset.read(1, window=window, masked=True).astype("float32")
    source = np.ma.filled(source, np.nan)
    if not np.isfinite(source).any():
        return None

    size = int(np.ceil(2.0 * half_m / pixel_m)) + 1
    destination = np.full((size, size), np.nan, dtype="float32")
    destination_crs = CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +datum=WGS84 +units=m +no_defs"
    )
    reproject(
        source=source,
        destination=destination,
        src_transform=dataset.window_transform(window),
        src_crs=dataset.crs,
        dst_transform=from_origin(-half_m, half_m, pixel_m, pixel_m),
        dst_crs=destination_crs.to_wkt(),
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    return destination


def _hurst_at_centre(
    patch: np.ndarray,
    pixel_m: float,
    lags_km: list[float],
    window_km: float,
) -> float:
    values = registry.hurst(
        patch, pixel_m, {"lags_km": lags_km, "window_km": window_km}, None  # type: ignore[arg-type]
    )
    centre = values[values.shape[0] // 2, values.shape[1] // 2]
    return float(centre)


def analyse_hurst_sensitivity(config: AppConfig | None = None) -> dict[str, Any]:
    """Compare Hurst with and without the shortest configured lag."""
    config = config or load_config()
    options = config.hurst_sensitivity
    hurst_definition: FeatureDefinition = next(
        definition
        for definition in config.terrain_features
        if definition.function == "hurst"
    )
    full_lags = list(hurst_definition.lags_km)
    reduced_lags = [lag for lag in full_lags if lag > options.drop_lag_km]
    window_km = float(hurst_definition.window_km or 0.0)
    pixel_m = float(config.grid.working_pixel_m)
    started = time.perf_counter()

    lat, lon = _random_land_points(config, options.sample_count)
    full_values: list[float] = []
    reduced_values: list[float] = []
    skipped = 0
    discarded = 0
    with rasterio.open(config.raw_source("earth", "terrain")) as dataset:
        for index, (site_lat, site_lon) in enumerate(zip(lat, lon)):
            patch = _read_patch(dataset, float(site_lat), float(site_lon), options.patch_km, pixel_m)
            if patch is None:
                skipped += 1
                continue
            full = _hurst_at_centre(patch, pixel_m, full_lags, window_km)
            reduced = _hurst_at_centre(patch, pixel_m, reduced_lags, window_km)
            if np.isfinite(full) and np.isfinite(reduced):
                full_values.append(full)
                reduced_values.append(reduced)
            else:
                discarded += 1
            if (index + 1) % 100 == 0:
                print(
                    f"  hurst: {index + 1}/{len(lat)} patches, "
                    f"{time.perf_counter() - started:.1f} s"
                )

    a = np.asarray(full_values, dtype="float64")
    b = np.asarray(reduced_values, dtype="float64")
    if a.size < 10:
        return {
            "available": False,
            "reason": f"only {a.size} usable patches (skipped {skipped})",
            "runtime_seconds": time.perf_counter() - started,
        }

    difference = a - b
    correlation = float(np.corrcoef(a, b)[0, 1])
    median_difference = float(np.median(difference))
    robust = bool(
        abs(median_difference) <= options.robust_max_median_difference
        and correlation >= options.robust_min_correlation
    )
    return {
        "available": True,
        "sample_requested": int(options.sample_count),
        "sample_used": int(a.size),
        "skipped": skipped,
        "discarded_undefined": discarded,
        "random_seed": int(options.random_seed),
        "patch_km": float(options.patch_km),
        "working_pixel_m": pixel_m,
        "window_km": window_km,
        "full_lags_km": full_lags,
        "reduced_lags_km": reduced_lags,
        "dropped_lag_km": float(options.drop_lag_km),
        "full": {
            "median": float(np.median(a)),
            "p16": float(np.percentile(a, 16)),
            "p84": float(np.percentile(a, 84)),
            "min": float(a.min()),
            "max": float(a.max()),
        },
        "reduced": {
            "median": float(np.median(b)),
            "p16": float(np.percentile(b, 16)),
            "p84": float(np.percentile(b, 84)),
            "min": float(b.min()),
            "max": float(b.max()),
        },
        "median_difference": median_difference,
        "median_abs_difference": float(np.median(np.abs(difference))),
        "pearson_r": correlation,
        "robust": robust,
        "thresholds": {
            "max_median_difference": float(options.robust_max_median_difference),
            "min_correlation": float(options.robust_min_correlation),
        },
        "runtime_seconds": time.perf_counter() - started,
    }
