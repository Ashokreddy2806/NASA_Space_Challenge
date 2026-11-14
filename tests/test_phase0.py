"""Phase 0 smoke tests: data presence, raster metadata, inventory output."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest
import rasterio

from backend.paths import DATA_ROOT, DOCS_DIR, RAW
from backend.pipeline.inspect_datasets import inspect_raster, Layer

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_data_root_exists() -> None:
    assert DATA_ROOT.is_dir(), f"data root not found: {DATA_ROOT}"
    for body in ("moon", "mars", "earth"):
        assert RAW[body].is_dir(), f"missing raw folder for {body}"


@pytest.mark.parametrize(
    "path",
    [
        RAW["moon"] / "LDEM_80S_80MPP_ADJ.tiff",
        RAW["moon"] / "LDRM_80S_1000MPP_ADJ_ROUGH_800M.tiff",
        RAW["moon"] / "LDRM_80S_1000MPP_ADJ_H.tiff",
        RAW["earth"] / "ETOPO_2022_v1_60s_N90W180_surface.tif",
        RAW["earth"] / "wc2.1_2.5m_bio_1.tif",
    ],
)
def test_primary_rasters_open(path: Path) -> None:
    assert path.exists(), f"missing source file: {path}"
    with rasterio.open(path) as ds:
        assert ds.width > 0 and ds.height > 0
        assert ds.crs is not None


def test_moon_polar_dem_is_80m_stereographic() -> None:
    with rasterio.open(RAW["moon"] / "LDEM_80S_80MPP_ADJ.tiff") as ds:
        assert ds.crs is not None and ds.crs.is_projected
        assert abs(abs(ds.transform.a) - 80.0) < 1e-6
        assert abs(abs(ds.transform.e) - 80.0) < 1e-6


def test_worldclim_is_2_5_arcminutes() -> None:
    with rasterio.open(RAW["earth"] / "wc2.1_2.5m_bio_1.tif") as ds:
        assert ds.crs is not None and ds.crs.is_geographic
        assert ds.transform.a * 60 == pytest.approx(2.5, abs=1e-6)


def test_worldclim_land_mask_is_nodata() -> None:
    with rasterio.open(RAW["earth"] / "wc2.1_2.5m_bio_1.tif") as ds:
        sample = ds.read(1, out_shape=(216, 432), masked=True)
    assert np.ma.getmaskarray(sample).mean() > 0.5, "ocean should be nodata in WorldClim"


def test_mola_raw_grid_is_2880x5760_int16() -> None:
    path = RAW["mars"] / "megt90n000eb.img"
    assert path.exists()
    assert path.stat().st_size == 2880 * 5760 * 2
    data = np.memmap(path, dtype=">i2", mode="r", shape=(2880, 5760))
    assert float(data[0, 0]) >= -32768


def test_psr_table_columns_and_rows() -> None:
    path = RAW["moon"] / "LPSR_80S_20MPP_ADJ_1km2.csv"
    assert path.exists()
    csv.field_size_limit(10**9)
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == ["gid", "WKT", "area_km2", "name"]
        first = next(reader)
    assert float(first["area_km2"]) >= 1.0
    assert first["WKT"].startswith(("POLYGON", "MULTIPOLYGON"))


def test_inventory_report_is_complete() -> None:
    report = DOCS_DIR / "data_inventory.md"
    assert report.exists(), "run python -m backend.pipeline.inspect_datasets"
    text = report.read_text(encoding="utf-8")
    for expected in ("M1", "M8", "megt90n000eb.img", "2.50 arc-minutes", "1,531", "ETOPO"):
        assert expected in text, f"inventory report is missing {expected!r}"


def test_inspect_raster_returns_metadata_without_full_read() -> None:
    layer = Layer("E1-bio1", "wc2.1_2.5m_bio_1.tif", "annual mean temperature", "degC")
    report = inspect_raster(RAW["earth"] / "wc2.1_2.5m_bio_1.tif", layer, max_dim=512)
    assert report.error is None
    assert report.info["width"] == 8640
    assert report.info["sampled"] is True
    assert report.info["valid_fraction"] < 1.0
    assert -60 < report.info["min"] < report.info["max"] < 40
