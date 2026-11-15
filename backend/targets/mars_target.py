"""Mars target profile: the configured Jezero crater disc from raw MOLA.

The MOLA MEGDR product (``megt90n000eb.img``) is a header-less big-endian int16
raster, 16 pixels per degree, longitude 0–360°E. It is read directly through a
memory map; no converted ``.npy`` is used.

The disc is reprojected to a local azimuthal-equidistant grid on a Mars sphere.
Resolution is a property of the source, so features whose windows MOLA cannot
resolve are reported as unavailable (or marginal) rather than faked — the same
registry rules that Earth and the Moon use.

Mars has no surface-temperature range in the supplied literature, so the range
features are excluded from its profile and the remaining group weights are
renormalised (reported here, applied in Phase 3).
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from backend.config import AppConfig, load_config
from backend.features import registry
from backend.targets import constraints, thermal
from backend.targets.distribution import profile_entry
from backend.targets.geometry import local_aeqd, sphere_crs


def mola_grid(dem_path) -> tuple[np.memmap, dict[str, Any]]:
    """Open the raw MOLA raster and describe its grid."""
    pixels_per_degree = 16
    height = 180 * pixels_per_degree
    width = 360 * pixels_per_degree
    data = np.memmap(dem_path, dtype=">i2", mode="r", shape=(height, width))
    return data, {
        "path": str(dem_path),
        "height": height,
        "width": width,
        "dtype": ">i2",
        "pixels_per_degree": pixels_per_degree,
        "longitude_convention": "0-360 east",
        "nodata": -32768,
    }


def _lonlat_window(
    lat: float, lon_east: float, radius_km: float, sphere_radius_m: float
) -> tuple[float, float, float, float]:
    """Generous lon/lat box that fully contains the target disc."""
    angular = np.degrees(radius_km * 1000.0 / sphere_radius_m)
    lat_pad = angular * 1.2
    lon_pad = angular * 1.2 / max(np.cos(np.radians(lat)), 0.2)
    return (
        lon_east - lon_pad,
        lat - lat_pad,
        lon_east + lon_pad,
        lat + lat_pad,
    )


def read_world_window(
    data: np.memmap,
    pixels_per_degree: int,
    bounds: tuple[float, float, float, float],
) -> tuple[np.ndarray, Any]:
    """Read a lon/lat window from the 0–360°E grid, wrapping longitude."""
    lon_min, lat_min, lon_max, lat_max = bounds
    height, width = data.shape
    row0 = max(0, int(np.floor((90.0 - lat_max) * pixels_per_degree)))
    row1 = min(height, int(np.ceil((90.0 - lat_min) * pixels_per_degree)))
    col0 = int(np.floor((lon_min % 360.0) * pixels_per_degree))
    col1 = int(np.ceil((lon_max % 360.0) * pixels_per_degree))

    if col1 <= col0:  # window crosses the 0/360 seam
        window = np.concatenate(
            [data[row0:row1, col0:width], data[row0:row1, 0:col1]], axis=1
        )
        start_col = col0
    else:
        window = np.asarray(data[row0:row1, col0:col1])
        start_col = col0

    values = window.astype("float32")
    values[window == -32768] = np.nan
    transform = from_origin(
        start_col / pixels_per_degree,
        90.0 - row0 / pixels_per_degree,
        1.0 / pixels_per_degree,
        1.0 / pixels_per_degree,
    )
    return values, transform


def _to_local_grid(
    values: np.ndarray,
    source_transform,
    source_crs,
    destination_crs,
    radius_m: float,
    pixel_m: float,
) -> tuple[np.ndarray, Any]:
    """Reproject a lon/lat MOLA window onto a local metric grid."""
    half = radius_m
    size = int(np.ceil(2.0 * half / pixel_m)) + 2
    destination_transform = from_origin(-half - pixel_m, half + pixel_m, pixel_m, pixel_m)
    destination = np.full((size, size), np.nan, dtype="float32")
    reproject(
        source=values,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs.to_wkt(),
        dst_transform=destination_transform,
        dst_crs=destination_crs.to_wkt(),
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.bilinear,
    )
    return destination, destination_transform


def _local_coordinates(transform, shape: tuple[int, int]) -> tuple[np.ndarray, np.ndarray]:
    rows = np.arange(shape[0], dtype="float64")[:, None]
    cols = np.arange(shape[1], dtype="float64")[None, :]
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    return xs, ys


def analyse_mars(config: AppConfig | None = None) -> dict[str, Any]:
    """Build the Mars target profile from the raw MOLA raster."""
    config = config or load_config()
    mars = config.targets["mars"]
    site = mars["site"]
    lat = float(site["lat_deg"])
    lon_east = float(site["lon_deg_east"])
    radius_km = float(site["radius_km"])
    sphere_radius_m = float(mars["sphere_radius_m"])
    pixel_m = float(mars["working_pixel_m"])
    native_pixel_m = float(mars["native_pixel_m"])
    started = time.perf_counter()

    dem_path = config.raw_source("mars", "dem")
    data, grid = mola_grid(dem_path)
    bounds = _lonlat_window(lat, lon_east, radius_km, sphere_radius_m)
    values, source_transform = read_world_window(
        data, int(grid["pixels_per_degree"]), bounds
    )

    source_crs = sphere_crs(sphere_radius_m)
    destination_crs = local_aeqd(sphere_radius_m, lat, lon_east)
    local, destination_transform = _to_local_grid(
        values,
        source_transform,
        source_crs,
        destination_crs,
        radius_km * 1000.0,
        pixel_m,
    )

    xs, ys = _local_coordinates(destination_transform, local.shape)
    distance = np.hypot(xs, ys)
    region = distance <= radius_km * 1000.0
    region_cells = int(region.sum())

    features, status = registry.compute_all(
        config.terrain_features,
        local,
        pixel_m,
        config.comparability,
        native_pixel_m=native_pixel_m,
    )

    stride = int(mars.get("sample_stride_px", config.distribution.sample_stride_px))
    sampled_cells = int(region[::stride, ::stride].sum())

    entries: dict[str, Any] = {}
    for definition in config.terrain_features:
        verdict = status.get(
            definition.id,
            registry.availability(
                definition, pixel_m, config.comparability, native_pixel_m
            ),
        )
        if not verdict.available or definition.id not in features:
            entries[definition.id] = {
                "units": definition.units,
                "long_name": definition.long_name,
                "group": definition.group,
                "registry_function": definition.function,
                "resolution": "unavailable",
                "resolution_note": verdict.reason,
                "n_cells": 0,
                "median": float("nan"),
            }
            continue
        values_flat = features[definition.id][::stride, ::stride]
        mask = region[::stride, ::stride]
        entries[definition.id] = profile_entry(
            definition,
            values_flat[mask],
            verdict,
            n_cells=region_cells,
            sampled=sampled_cells < region_cells,
            percentiles=config.distribution.percentiles,
        )

    # Site elevation check: the configured site elevation must match the DEM.
    row = int(np.floor((90.0 - lat) * int(grid["pixels_per_degree"])))
    col = int(np.floor((lon_east % 360.0) * int(grid["pixels_per_degree"])))
    dem_elevation = float(int(data[min(row, grid["height"] - 1), min(col, grid["width"] - 1)]))
    site_check = {
        "configured_elevation_m": float(site["elevation_m"]),
        "dem_elevation_m": dem_elevation,
        "difference_m": dem_elevation - float(site["elevation_m"]),
        "pixel": [row, col],
        "note": "nearest MOLA 16 ppd cell at the configured site coordinate",
    }

    table = thermal.thermal_availability(config, "mars")
    thermal_entries = thermal.match_thermal_features(config, table, mars)
    thermal_entries.update(thermal.qualitative_thermal_features(config, table, mars))
    thermal.apply_thermal_unavailable(thermal_entries, mars)
    entries.update(thermal_entries)
    entries.update(constraints.dryness_constraint_entries(config, mars))
    # Configured exclusions win over the literature table: Mars is documented as
    # having no surface-temperature range, so those features stay unavailable
    # even if a table row ever appears, and the weight is renormalised instead.
    definitions = {definition.id: definition for definition in config.all_features}
    for feature_id in mars.get("unavailable_features") or []:
        definition = definitions.get(feature_id)
        if definition is None:
            raise KeyError(
                f"targets.yaml mars.unavailable_features lists unknown feature {feature_id}"
            )
        entries[feature_id] = {
            "units": definition.units,
            "long_name": definition.long_name,
            "group": definition.group,
            "registry_function": definition.function,
            "resolution": "unavailable",
            "resolution_note": str(
                (mars.get("not_applicable") or {}).get(
                    feature_id, "excluded by target configuration"
                )
            ),
            "n_cells": 0,
            "median": float("nan"),
        }

    return {
        "body": "mars",
        "label": mars["label"],
        "source": {
            "dem": config.source_name("mars", "dem"),
            "pixel_m": pixel_m,
            "native_pixel_m": native_pixel_m,
            "crs": f"local azimuthal equidistant, sphere R={sphere_radius_m:.0f} m",
            "grid": grid,
        },
        "extent": {
            "site": {
                "lat_deg": lat,
                "lon_deg_east": lon_east,
                "elevation_m": float(site["elevation_m"]),
            },
            "radius_km": radius_km,
            "region_pixels_full": region_cells,
            "region_area_km2": float(region_cells * (pixel_m / 1000.0) ** 2),
            "sampled_pixels": sampled_cells,
            "sample_stride_px": stride,
            "lonlat_window": {
                "lon_min": bounds[0],
                "lat_min": bounds[1],
                "lon_max": bounds[2],
                "lat_max": bounds[3],
            },
        },
        "site_check": site_check,
        "features": entries,
        "ice_proxy": {
            "available": False,
            "reason": "no Mars ice/frost proxy is defined in the supplied data",
        },
        "thermal": {
            "available": table["available"],
            "path": table["path"],
            "reason": table["reason"],
            "schema": table.get("schema"),
            "entries": table["table"],
            "references": table.get("references", []),
            "derived": table.get("derived", []),
            "context_only": thermal.thermal_context(config, table, mars),
        },
        "runtime_seconds": time.perf_counter() - started,
    }
