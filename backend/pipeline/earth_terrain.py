"""Phase 1 terrain pipeline: ETOPO 2022 → search-grid terrain features.

For each configured tile the native 1-arc-minute ETOPO DEM is reprojected to a
local azimuthal-equidistant grid at the configured working pixel size. Every
terrain feature is then computed by the shared registry
(``backend.features.registry``) in kilometre-sized windows and sampled back onto
the search grid.

ETOPO includes bathymetry, so coastal land cells would otherwise see the
continental shelf inside their window and get spurious relief and slope. Ocean
cells are therefore filled with the nearest land elevation before any filtering,
using the WorldClim land mask from the climate store.

Run from ``NASA_Space_Challenge/`` (after ``backend.pipeline.earth_climate``)::

    python -m backend.pipeline.earth_terrain

Output: the configured ``earth_terrain`` store (unmasked; the climate step
supplies the land mask and ``build_earth_features`` writes the final dataset).
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

from backend.config import AppConfig, GridSpec, load_config
from backend.features import registry
from backend.paths import RAW
from backend.pipeline.earth_grid import (
    Tile,
    global_slices,
    iter_tiles,
    local_grid,
    tile_transform,
)
from backend.pipeline.feature_store import GridStore

ETOPO_SOURCE = "ETOPO 2022 v1 60 arc-second surface elevation (NOAA NCEI)"
ETOPO_DOI = "10.25921/fd45-gt74"


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


def read_land_window(
    climate: Dataset, tile: Tile, spec: GridSpec
) -> tuple[np.ndarray, object]:
    """Read the search-grid land-fraction window covering a tile plus halo."""
    lon_min, lat_min, lon_max, lat_max = tile.padded_bounds
    variable = climate.variables["land_fraction"]
    rows, cols = variable.shape
    res = spec.resolution_deg
    row0 = max(0, int(np.floor((spec.lat_max - lat_max) / res)))
    row1 = min(rows, int(np.ceil((spec.lat_max - lat_min) / res)))
    col0 = max(0, int(np.floor((lon_min - spec.lon_min) / res)))
    col1 = min(cols, int(np.ceil((lon_max - spec.lon_min) / res)))
    values = np.asarray(variable[row0:row1, col0:col1], dtype="float32")
    west = spec.lon_min + col0 * res
    north = spec.lat_max - row0 * res
    return values, from_origin(west, north, res, res)


def compute_terrain_features(
    elevation: np.ndarray,
    pixel_m: float,
    land: np.ndarray | None = None,
    config: AppConfig | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, registry.Availability]]:
    """Compute every resolvable terrain feature with the shared registry.

    Returns ``(arrays, availability)``; features the data cannot resolve are
    absent from ``arrays`` and carry a reason in ``availability``.
    """
    config = config or load_config()
    return registry.compute_all(
        config.terrain_features,
        elevation,
        pixel_m,
        config.comparability,
        land=land,
        native_pixel_m=config.earth.native_pixel_m,
    )


def reproject_to_local(
    source: np.ndarray,
    source_transform: object,
    tile: Tile,
    land_threshold: float,
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
        land = fraction >= land_threshold
    return destination, land, destination_transform, destination_crs


def reproject_feature_to_global(
    feature: np.ndarray,
    source_transform: object,
    source_crs: object,
    tile: Tile,
) -> np.ndarray:
    """Sample a local metric feature onto the tile's core window on the search grid."""
    row_slice, col_slice = global_slices(tile)
    height = row_slice.stop - row_slice.start
    width = col_slice.stop - col_slice.start
    destination = np.full((height, width), np.nan, dtype="float32")
    spec = tile.spec

    reproject(
        source=feature,
        destination=destination,
        src_transform=source_transform,
        src_crs=source_crs,
        dst_transform=tile_transform(tile),
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.average,
    )
    return destination


def build_terrain(
    output: Path,
    config: AppConfig | None = None,
    limit_tiles: int | None = None,
    climate_path: Path | None = None,
) -> dict:
    """Run the terrain pipeline and write the intermediate NetCDF store."""
    config = config or load_config()
    spec = config.grid
    pixel_m = spec.working_pixel_m
    climate_path = climate_path or config.output("earth_climate")
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
    source_path = config.raw_source("earth", "terrain")
    unavailable: dict[str, dict] = {}
    status_by_id: dict[str, registry.Availability] = {}

    with GridStore(
        output, spec, mode="w", compression_level=config.storage.compression_level
    ) as store:
        arrays: dict[str, object] = {}
        with Dataset(climate_path) as climate, rasterio.open(source_path) as dataset:
            for tile in iter_tiles(spec):
                if limit_tiles is not None and tile_count >= limit_tiles:
                    break
                source, source_transform = read_etopo_window(dataset, tile)
                land_source, land_transform = read_land_window(climate, tile, spec)
                local, land, local_transform, local_crs_value = reproject_to_local(
                    source,
                    source_transform,
                    tile,
                    config.earth.land_mask_threshold,
                    land_source,
                    land_transform,
                )
                features, status = compute_terrain_features(
                    local, pixel_m, land=land, config=config
                )
                for feature_id, verdict in status.items():
                    if feature_id not in status_by_id:
                        status_by_id[feature_id] = verdict
                    if not verdict.available:
                        unavailable[feature_id] = verdict.as_dict()
                if not arrays:
                    arrays = {
                        definition.id: store.create_feature(
                            definition.id, registry.attributes(definition)
                        )
                        for definition in config.terrain_features
                        if definition.id in features
                    }
                row_slice, col_slice = global_slices(tile)
                for name, variable in arrays.items():
                    sampled = reproject_feature_to_global(
                        features[name], local_transform, local_crs_value, tile
                    )
                    variable[row_slice, col_slice] = sampled
                tile_count += 1
                if tile_count % 50 == 0:
                    elapsed = time.perf_counter() - started
                    print(f"  terrain: {tile_count} tiles, {elapsed:.1f} s")

        for name, variable in arrays.items():
            verdict = status_by_id.get(name)
            if verdict is not None:
                variable.setncattr("resolution_status", verdict.resolution)
                if verdict.reason:
                    variable.setncattr("resolution_note", verdict.reason)

        store.set_attrs(
            {
                "title": "Earth terrain features on the configured search grid",
                "source": ETOPO_SOURCE,
                "source_doi": ETOPO_DOI,
                "grid": (
                    f"{spec.resolution_deg:g} degree lon/lat, "
                    f"{spec.nx} x {spec.ny} cells, north-to-south rows"
                ),
                "working_grid": (
                    "local azimuthal equidistant, "
                    f"{pixel_m / 1000:.2f} km pixels"
                ),
                "feature_registry": "backend.features.registry",
                "coastal_handling": (
                    "ocean cells filled with the nearest land elevation (WorldClim land "
                    "mask) before filtering, so bathymetry cannot inflate coastal features"
                ),
                "tiles_processed": tile_count,
                "runtime_seconds": round(time.perf_counter() - started, 1),
                "land_mask": "not applied here; see the climate store",
            }
        )
    print(f"Wrote {output} ({tile_count} tiles, {time.perf_counter() - started:.1f} s)")
    return {
        "path": str(output),
        "tiles": tile_count,
        "unavailable": unavailable,
        "runtime_seconds": time.perf_counter() - started,
    }


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--climate", type=Path, default=None)
    parser.add_argument("--limit-tiles", type=int, default=None)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="config override YAML deep-merged over config/*.yaml",
    )
    args = parser.parse_args()
    config = load_config(override=args.config)
    output = args.output or config.output("earth_terrain")
    output.parent.mkdir(parents=True, exist_ok=True)
    build_terrain(
        output,
        config,
        limit_tiles=args.limit_tiles,
        climate_path=args.climate,
    )


if __name__ == "__main__":
    main()
