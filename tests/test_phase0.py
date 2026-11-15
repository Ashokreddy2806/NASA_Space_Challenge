"""Phase 0 smoke tests: data presence, raster metadata, inventory output.

Every file name comes from ``config/paths.yaml``.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import rasterio

from backend.paths import DATA_ROOT, RAW
from backend.pipeline.inspect_datasets import Layer, inspect_raster


def test_data_root_exists() -> None:
    assert DATA_ROOT.is_dir(), f"data root not found: {DATA_ROOT}"
    for body in ("moon", "mars", "earth"):
        assert RAW[body].is_dir(), f"missing raw folder for {body}"


@pytest.mark.parametrize(
    "body,keys",
    [
        ("moon", ("dem", "hurst", "roughness_800m", "slope_800m")),
        ("earth", ("terrain",)),
    ],
)
def test_primary_rasters_open(config, body: str, keys: tuple[str, ...]) -> None:
    for key in keys:
        path = config.raw_source(body, key)
        assert path.exists(), f"missing source file: {path}"
        with rasterio.open(path) as dataset:
            assert dataset.width > 0 and dataset.height > 0
            assert dataset.crs is not None


def test_earth_climate_rasters_open(config) -> None:
    for file_key in config.sources["earth"]["climate"]:
        path = RAW["earth"] / config.sources["earth"]["climate"][file_key]
        assert path.exists(), f"missing climate layer: {path}"
        with rasterio.open(path) as dataset:
            assert dataset.crs is not None


def test_moon_polar_dem_matches_configured_resolution(config) -> None:
    native = config.targets["moon"]["native_pixel_m"]
    with rasterio.open(config.raw_source("moon", "dem")) as dataset:
        assert dataset.crs is not None and dataset.crs.is_projected
        assert abs(abs(dataset.transform.a) - native) < 1e-6
        assert abs(abs(dataset.transform.e) - native) < 1e-6


def test_worldclim_is_2_5_arcminutes(config) -> None:
    path = RAW["earth"] / config.sources["earth"]["climate"][config.earth.land_mask_source]
    with rasterio.open(path) as dataset:
        assert dataset.crs is not None and dataset.crs.is_geographic
        assert dataset.transform.a * 60 == pytest.approx(2.5, abs=1e-6)


def test_worldclim_land_mask_is_nodata(config) -> None:
    path = RAW["earth"] / config.sources["earth"]["climate"][config.earth.land_mask_source]
    with rasterio.open(path) as dataset:
        sample = dataset.read(1, out_shape=(216, 432), masked=True)
    assert np.ma.getmaskarray(sample).mean() > 0.5, "ocean should be nodata in WorldClim"


def test_mola_grid_matches_configured_resolution(config) -> None:
    path = config.raw_source("mars", "dem")
    assert path.exists()
    # MEGDR 16 pixels per degree: 5760 x 2880 big-endian int16 metres.
    height, width = 180 * 16, 360 * 16
    assert path.stat().st_size == height * width * 2
    data = np.memmap(path, dtype=">i2", mode="r", shape=(height, width))
    assert float(data[0, 0]) >= -32768
    native_km = 2.0 * np.pi * 3396.2 / width
    assert native_km == pytest.approx(config.targets["mars"]["native_pixel_m"] / 1000.0, rel=0.02)


def test_psr_table_columns_and_rows(config) -> None:
    path = config.raw_source("moon", "psr")
    assert path.exists()
    csv.field_size_limit(10**9)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        first = next(reader)
    assert fieldnames == ["gid", "WKT", "area_km2", "name"]
    minimum = config.targets["moon"]["ice_proxy"]["min_polygon_area_km2"]
    assert float(first["area_km2"]) >= minimum
    assert first["WKT"].startswith(("POLYGON", "MULTIPOLYGON"))


def test_inventory_report_is_complete(config) -> None:
    report = config.outputs.docs_dir / "data_inventory.md"
    assert report.exists(), "run python -m backend.pipeline.inspect_datasets"
    text = report.read_text(encoding="utf-8")
    mars_dem = config.raw_source("mars", "dem").name
    for expected in ("M1", "M8", mars_dem, "2.50 arc-minutes", "1,531", "ETOPO"):
        assert expected in text, f"inventory report is missing {expected!r}"


def test_inspect_raster_returns_metadata_without_full_read(config) -> None:
    file_key = config.earth.land_mask_source
    filename = config.sources["earth"]["climate"][file_key]
    layer = Layer("E1", filename, "annual mean temperature", "degC")
    report = inspect_raster(RAW["earth"] / filename, layer, max_dim=512)
    assert report.error is None
    assert report.info["width"] == 8640
    assert report.info["sampled"] is True
    assert report.info["valid_fraction"] < 1.0
    assert -60 < report.info["min"] < report.info["max"] < 40
