"""Phase 1 climate pipeline: WorldClim 2.1 → search-grid climate features.

WorldClim 2.1 bioclimatic layers are 2.5 arc-minutes (~4.6 km). They are
resampled to the configured search grid with area averaging. The WorldClim ocean
nodata mask becomes the Earth land mask (majority-valid rule), because ETOPO
includes bathymetry and cannot supply a land mask by itself.

Which layers, their names, units and the land-mask source all come from
``config/features.yaml`` and ``config/config.yaml``.

Run from ``NASA_Space_Challenge/``::

    python -m backend.pipeline.earth_climate

Output: the configured ``earth_climate`` store.
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.warp import reproject

from backend.config import AppConfig, GridSpec, load_config
from backend.features import registry
from backend.paths import RAW
from backend.pipeline.earth_grid import global_transform
from backend.pipeline.feature_store import GridStore

WORLDCLIM_SOURCE = "WorldClim 2.1, 2.5 arc-minute (Fick & Hijmans 2017)"
WORLDCLIM_DOI = "10.1002/joc.5086"


def resample_layer(
    path: Path, spec: GridSpec, resampling: Resampling = Resampling.average
) -> tuple[np.ndarray, np.ndarray]:
    """Resample one WorldClim layer to the search grid; return values and valid fraction."""
    with rasterio.open(path) as dataset:
        source = dataset.read(1, masked=True).astype("float32")
        values = np.ma.filled(source, np.nan)
        valid = (~np.ma.getmaskarray(source)).astype("float32")
        source_transform = dataset.transform

    destination_grid = global_transform(spec)
    destination_values = np.full((spec.ny, spec.nx), np.nan, dtype="float32")
    reproject(
        source=values,
        destination=destination_values,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        dst_transform=destination_grid,
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=resampling,
    )
    destination_valid = np.full((spec.ny, spec.nx), np.nan, dtype="float32")
    reproject(
        source=valid,
        destination=destination_valid,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        dst_transform=destination_grid,
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.average,
    )
    return destination_values, destination_valid


def _climate_layer_path(config: AppConfig, file_key: str) -> Path:
    try:
        filename = config.sources["earth"]["climate"][file_key]
    except KeyError as exc:
        raise KeyError(
            f"no configured Earth climate layer named {file_key!r}; "
            f"known: {sorted(config.sources['earth']['climate'])}"
        ) from exc
    path = RAW["earth"] / str(filename)
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def build_climate(output: Path, config: AppConfig | None = None) -> dict:
    """Run the climate pipeline and write the intermediate NetCDF store."""
    config = config or load_config()
    spec = config.grid
    if output.exists():
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    started = time.perf_counter()

    with GridStore(
        output, spec, mode="w", compression_level=config.storage.compression_level
    ) as store:
        for definition in config.climate_features:
            file_key = str(definition.params["file_key"])
            values, _ = resample_layer(_climate_layer_path(config, file_key), spec)
            attrs = registry.attributes(definition)
            attrs["source"] = WORLDCLIM_SOURCE
            attrs["source_doi"] = WORLDCLIM_DOI
            attrs["measurement"] = (
                "air temperature / precipitation, not surface skin temperature"
            )
            store.create_feature(definition.id, attrs)[:] = values
            print(
                f"  climate: {definition.id} "
                f"({np.nanmin(values):.1f} .. {np.nanmax(values):.1f} {definition.units})"
            )

        # The land mask comes from the configured WorldClim layer's valid fraction:
        # a cell is land when the majority of its source cells are valid.
        _, land_fraction = resample_layer(
            _climate_layer_path(config, config.earth.land_mask_source), spec
        )
        land_fraction = np.nan_to_num(land_fraction, nan=0.0).astype("float32")
        land_mask = (land_fraction >= config.earth.land_mask_threshold).astype("i1")
        store.create_feature(
            "land_fraction",
            {
                "long_name": "Fraction of WorldClim source cells that are land",
                "units": "1",
                "definition": (
                    "area average of the "
                    f"{config.earth.land_mask_source} valid mask at the search-grid "
                    "resolution"
                ),
            },
        )[:] = land_fraction
        store.create_feature(
            "land_mask",
            {
                "long_name": "Earth land mask from WorldClim ocean nodata",
                "units": "1",
                "definition": (
                    f"1 where land_fraction >= {config.earth.land_mask_threshold:g}, else 0"
                ),
            },
            fill_value=-1,
            dtype="i1",
        )[:] = land_mask

        store.set_attrs(
            {
                "title": "Earth climate features and WorldClim land mask",
                "source": WORLDCLIM_SOURCE,
                "source_doi": WORLDCLIM_DOI,
                "grid": (
                    f"{spec.resolution_deg:g} degree lon/lat, "
                    f"{spec.nx} x {spec.ny} cells, north-to-south rows"
                ),
                "resampling": "area average from 2.5 arc-minute",
                "temperature_type": (
                    "air temperature (1970-2000 climatology), not surface skin temperature"
                ),
                "land_mask_rule": (
                    f"{config.earth.land_mask_source} valid fraction >= "
                    f"{config.earth.land_mask_threshold:g}"
                ),
                "runtime_seconds": round(time.perf_counter() - started, 1),
            }
        )
    print(f"Wrote {output} ({time.perf_counter() - started:.1f} s)")
    return {"path": str(output), "runtime_seconds": time.perf_counter() - started}


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="config override YAML deep-merged over config/*.yaml",
    )
    args = parser.parse_args()
    config = load_config(override=args.config)
    output = args.output or config.output("earth_climate")
    output.parent.mkdir(parents=True, exist_ok=True)
    build_climate(output, config)


if __name__ == "__main__":
    main()
