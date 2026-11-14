"""Phase 1 climate pipeline: WorldClim 2.1 → global 0.05° climate features.

WorldClim 2.1 bioclimatic layers are 2.5 arc-minutes (~4.6 km). They are
resampled to the common 0.05° grid with area averaging. The WorldClim ocean
nodata mask becomes the Earth land mask (majority-valid rule), because ETOPO
includes bathymetry and cannot supply a land mask by itself.

Run from ``NASA_Space_Challenge/``::

    python -m backend.pipeline.earth_climate

Output: ``data/processed/earth_climate.nc``.
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject

from backend.paths import PROCESSED_DIR, RAW
from backend.pipeline.earth_grid import LAT_MAX, LON_MIN, NX, NY, RES_DEG
from backend.pipeline.feature_store import GridStore

# (variable name, WorldClim file, units, long name, definition)
CLIMATE_FEATURES = [
    (
        "temp_mean_c",
        "wc2.1_2.5m_bio_1.tif",
        "degC",
        "Annual mean air temperature",
        "WorldClim bio_1, 1970-2000 climatology",
    ),
    (
        "temp_diurnal_range_c",
        "wc2.1_2.5m_bio_2.tif",
        "degC",
        "Mean diurnal air-temperature range",
        "WorldClim bio_2 (mean monthly max-min), day/night swing proxy",
    ),
    (
        "temp_max_warmest_c",
        "wc2.1_2.5m_bio_5.tif",
        "degC",
        "Maximum air temperature of the warmest month",
        "WorldClim bio_5",
    ),
    (
        "temp_min_coldest_c",
        "wc2.1_2.5m_bio_6.tif",
        "degC",
        "Minimum air temperature of the coldest month",
        "WorldClim bio_6; also the Earth cold-extreme/ice proxy",
    ),
    (
        "temp_annual_range_c",
        "wc2.1_2.5m_bio_7.tif",
        "degC",
        "Annual air-temperature range",
        "WorldClim bio_7 (bio_5 - bio_6)",
    ),
    (
        "precip_annual_mm",
        "wc2.1_2.5m_bio_12.tif",
        "mm",
        "Annual precipitation",
        "WorldClim bio_12",
    ),
    (
        "precip_driest_month_mm",
        "wc2.1_2.5m_bio_14.tif",
        "mm",
        "Precipitation of the driest month",
        "WorldClim bio_14",
    ),
]


def _destination_transform():
    """Affine transform of the 0.05° output grid."""
    return from_origin(LON_MIN, LAT_MAX, RES_DEG, RES_DEG)


def resample_layer(path: Path, resampling: Resampling = Resampling.average) -> tuple[np.ndarray, np.ndarray]:
    """Resample one WorldClim layer to 0.05°; return values and valid fraction."""
    with rasterio.open(path) as dataset:
        source = dataset.read(1, masked=True).astype("float32")
        values = np.ma.filled(source, np.nan)
        valid = (~np.ma.getmaskarray(source)).astype("float32")
        source_transform = dataset.transform

    destination_values = np.full((NY, NX), np.nan, dtype="float32")
    reproject(
        source=values,
        destination=destination_values,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        dst_transform=_destination_transform(),
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=resampling,
    )
    destination_valid = np.full((NY, NX), np.nan, dtype="float32")
    reproject(
        source=valid,
        destination=destination_valid,
        src_transform=source_transform,
        src_crs="EPSG:4326",
        dst_transform=_destination_transform(),
        dst_crs="EPSG:4326",
        src_nodata=np.nan,
        dst_nodata=np.nan,
        resampling=Resampling.average,
    )
    return destination_values, destination_valid


def build_climate(output: Path) -> None:
    """Run the climate pipeline and write the intermediate NetCDF store."""
    if output.exists():
        if output.is_dir():
            shutil.rmtree(output)
        else:
            output.unlink()
    started = time.perf_counter()

    with GridStore(output, mode="w") as store:
        arrays = {}
        for name, filename, units, long_name, definition in CLIMATE_FEATURES:
            path = RAW["earth"] / filename
            if not path.exists():
                raise FileNotFoundError(path)
            values, valid = resample_layer(path)
            attrs = {
                "long_name": long_name,
                "units": units,
                "definition": definition,
                "source": "WorldClim 2.1, 2.5 arc-minute",
                "source_doi": "10.1002/joc.5086",
                "measurement": "air temperature / precipitation, not surface skin temperature",
            }
            if name == "temp_min_coldest_c":
                attrs["role"] = "Earth ice/cold-trap proxy (cold extremes); not radiation or vacuum"
            arrays[name] = store.create_feature(name, attrs)
            arrays[name][:] = values
            print(f"  climate: {name} ({np.nanmin(values):.1f} .. {np.nanmax(values):.1f} {units})")

        # The land mask comes from the bio_1 valid fraction. A cell is land when
        # the majority of its 2.5' source cells are valid (not ocean nodata).
        _, land_fraction = resample_layer(RAW["earth"] / "wc2.1_2.5m_bio_1.tif")
        land_fraction = np.nan_to_num(land_fraction, nan=0.0).astype("float32")
        land_mask = (land_fraction >= 0.5).astype("i1")
        store.create_feature(
            "land_fraction",
            {
                "long_name": "Fraction of WorldClim source cells that are land",
                "units": "1",
                "definition": "area average of the bio_1 valid mask at 0.05 degrees",
            },
        )[:] = land_fraction
        store.create_feature(
            "land_mask",
            {
                "long_name": "Earth land mask from WorldClim ocean nodata",
                "units": "1",
                "definition": "1 where land_fraction >= 0.5, else 0",
            },
            fill_value=-1,
            dtype="i1",
        )[:] = land_mask

        store.set_attrs(
            {
                "title": "Earth climate features and WorldClim land mask on a 0.05 degree grid",
                "source": "WorldClim 2.1 bioclimatic variables, 2.5 arc-minute (Fick & Hijmans 2017)",
                "source_doi": "10.1002/joc.5086",
                "grid": "global 0.05 degree lon/lat, north-to-south rows",
                "resampling": "area average from 2.5 arc-minute; 0.05 deg is slightly coarser",
                "temperature_type": "air temperature (1970-2000 climatology), not surface skin temperature",
                "land_mask_rule": "land_fraction >= 0.5 from WorldClim ocean nodata",
                "runtime_seconds": round(time.perf_counter() - started, 1),
            }
        )
    print(f"Wrote {output} ({time.perf_counter() - started:.1f} s)")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROCESSED_DIR / "earth_climate.nc"
    )
    args = parser.parse_args()
    build_climate(args.output)


if __name__ == "__main__":
    main()
