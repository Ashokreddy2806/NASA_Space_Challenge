"""Phase 0 data inventory.

Opens every downloaded raster once, reports its CRS, native resolution, nodata
value, sampled value range and units, and inspects the lunar PSR polygon CSV.
Writes a human-readable report to ``docs/data_inventory.md``.

Run from the project root (``NASA_Space_Challenge/``)::

    python -m backend.pipeline.inspect_datasets

The script never loads a full large raster: large files are read through a
decimated window (default <= 2048 px on the long side) and the report labels
which statistics are sampled.
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio
from pyproj import CRS
from rasterio.enums import Resampling

from backend.paths import DATA_ROOT, DOCS_DIR, RAW

NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


@dataclass
class Layer:
    """A downloaded source file and the feature it is expected to provide."""

    layer_id: str
    filename: str
    feature: str
    documented_units: str
    notes: str = ""
    status: str = "downloaded"


@dataclass
class RasterReport:
    """Everything the inventory records about one raster."""

    path: Path
    layer: Layer
    info: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


MOON_LAYERS = [
    Layer("M1", "LDEM_80S_80MPP_ADJ.tiff", "relief, derived slope", "m", "80 m/pixel LOLA south polar DEM"),
    Layer("M2", "LDRM_80S_1000MPP_ADJ_ROUGH_800M.tiff", "roughness (800 m baseline)", "m", "1 km/pixel"),
    Layer("M3", "LDRM_80S_1000MPP_ADJ_ROUGH_1600M.tiff", "roughness (1600 m baseline)", "m", "1 km/pixel"),
    Layer("M4", "LDRM_80S_1000MPP_ADJ_SLP_800M.tiff", "slope (800 m baseline)", "degree", "1 km/pixel"),
    Layer("M5", "LDRM_80S_1000MPP_ADJ_SLP_1600M.tiff", "slope (1600 m baseline)", "degree", "1 km/pixel"),
    Layer("M6", "LDRM_80S_1000MPP_ADJ_H.tiff", "Hurst exponent", "unitless", "1 km/pixel"),
    Layer("M7", "LDRM_80S_1000MPP_ADJ_SPSLP.tiff", "spectral slope", "sigma/km", "1 km/pixel"),
    Layer("M9", "ldem_16.tif", "global context elevation (not for polar slope)", "km", "5760x2880 global, optional"),
]

MARS_LAYERS = [
    Layer(
        "R1",
        "mars_elev.npy",
        "relief, slope, roughness",
        "m",
        "expected int16 2880x5760 MOLA 16 ppd; NOT PRESENT on disk",
        status="missing",
    ),
]

WORLDCLIM_LAYERS = [
    Layer("E1-bio1", "wc2.1_2.5m_bio_1.tif", "annual mean temperature", "degC"),
    Layer("E1-bio2", "wc2.1_2.5m_bio_2.tif", "mean diurnal range", "degC"),
    Layer("E1-bio3", "wc2.1_2.5m_bio_3.tif", "isothermality", "%"),
    Layer("E1-bio4", "wc2.1_2.5m_bio_4.tif", "temperature seasonality", "degC"),
    Layer("E1-bio5", "wc2.1_2.5m_bio_5.tif", "max temperature of warmest month", "degC"),
    Layer("E1-bio6", "wc2.1_2.5m_bio_6.tif", "min temperature of coldest month", "degC"),
    Layer("E1-bio7", "wc2.1_2.5m_bio_7.tif", "annual temperature range", "degC"),
    Layer("E1-bio8", "wc2.1_2.5m_bio_8.tif", "mean temperature of wettest quarter", "degC"),
    Layer("E1-bio9", "wc2.1_2.5m_bio_9.tif", "mean temperature of driest quarter", "degC"),
    Layer("E1-bio10", "wc2.1_2.5m_bio_10.tif", "mean temperature of warmest quarter", "degC"),
    Layer("E1-bio11", "wc2.1_2.5m_bio_11.tif", "mean temperature of coldest quarter", "degC"),
    Layer("E1-bio12", "wc2.1_2.5m_bio_12.tif", "annual precipitation", "mm"),
    Layer("E1-bio13", "wc2.1_2.5m_bio_13.tif", "precipitation of wettest month", "mm"),
    Layer("E1-bio14", "wc2.1_2.5m_bio_14.tif", "precipitation of driest month", "mm"),
    Layer("E1-bio15", "wc2.1_2.5m_bio_15.tif", "precipitation seasonality", "%"),
    Layer("E1-bio16", "wc2.1_2.5m_bio_16.tif", "precipitation of wettest quarter", "mm"),
    Layer("E1-bio17", "wc2.1_2.5m_bio_17.tif", "precipitation of driest quarter", "mm"),
    Layer("E1-bio18", "wc2.1_2.5m_bio_18.tif", "precipitation of warmest quarter", "mm"),
    Layer("E1-bio19", "wc2.1_2.5m_bio_19.tif", "precipitation of coldest quarter", "mm"),
]

EARTH_LAYERS = [
    Layer("E2", "ETOPO_2022_v1_60s_N90W180_surface.tif", "relief, slope, roughness, Hurst-like", "m", "60 arc-second global"),
]


def _find_case_insensitive(directory: Path, filename: str) -> Path | None:
    """Return the file in ``directory`` matching ``filename`` ignoring case."""
    direct = directory / filename
    if direct.exists():
        return direct
    wanted = filename.lower()
    for candidate in directory.iterdir():
        if candidate.is_file() and candidate.name.lower() == wanted:
            return candidate
    return None


def _crs_name(ds: rasterio.DatasetReader) -> str:
    """Return a readable CRS name with an authority code when available."""
    if ds.crs is None:
        return "none (plain TIFF, no georeferencing)"
    wkt = ds.crs.to_string()
    if ds.crs.to_epsg() is None and "Polar_Stereographic" in wkt and "Moon" in wkt:
        return "Moon 2015 south polar stereographic (custom)"
    try:
        crs = CRS.from_user_input(ds.crs)
        name = crs.name
    except Exception:  # pragma: no cover - defensive for exotic CRS
        name = wkt
    authority = ds.crs.to_authority()
    if authority:
        return f"{name} ({authority[0]}:{authority[1]})"
    return name


def _pixel_size_km(ds: rasterio.DatasetReader) -> tuple[float, float] | None:
    """Approximate native pixel size in km (x, y) at the raster centre.

    Returns ``None`` for images with no georeferencing (the source resolution
    must then be taken from the dataset documentation).
    """
    res_x, res_y = abs(ds.transform.a), abs(ds.transform.e)
    if ds.crs is None:
        return None
    if ds.crs.is_projected:
        unit_factor = 1.0
        try:
            unit_factor = ds.crs.linear_units_factor[1]
        except Exception:  # pragma: no cover - older PROJ behaviour
            if ds.crs.linear_units.lower() not in {"metre", "meter", "m"}:
                unit_factor = 1000.0
        return res_x * unit_factor / 1000.0, res_y * unit_factor / 1000.0
    centre_lat = (ds.bounds.top + ds.bounds.bottom) / 2.0
    km_per_deg_lat = 110.57
    km_per_deg_lon = 111.32 * max(math.cos(math.radians(centre_lat)), 0.01)
    return res_x * km_per_deg_lon, res_y * km_per_deg_lat


def _finite_stats(values: np.ndarray) -> dict[str, float]:
    """Return min/percentiles/max/mean for finite values only."""
    values = values[np.isfinite(values)]
    if values.size == 0:
        return {}
    p01, p50, p99 = np.percentile(values, [1, 50, 99])
    return {
        "min": float(values.min()),
        "p01": float(p01),
        "median": float(p50),
        "p99": float(p99),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "std": float(values.std()),
    }


def inspect_raster(path: Path, layer: Layer, max_dim: int = 2048) -> RasterReport:
    """Open a raster and collect metadata plus a memory-safe value sample."""
    report = RasterReport(path=path, layer=layer)
    try:
        with rasterio.open(path) as ds:
            native_px = ds.width * ds.height
            decimation = max(1, math.ceil(max(ds.width, ds.height) / max_dim))
            out_height = max(1, ds.height // decimation)
            out_width = max(1, ds.width // decimation)
            sampled = native_px > out_height * out_width

            array = ds.read(1, out_shape=(out_height, out_width), resampling=Resampling.nearest, masked=True)
            data = np.ma.asarray(array, dtype="float64")
            mask = np.ma.getmaskarray(data) | ~np.isfinite(np.ma.filled(data, np.nan))
            values = np.asarray(np.ma.filled(data, np.nan))[~mask]
            stats = _finite_stats(values)

            tags = {k: v for k, v in ds.tags().items() if v not in (None, "")}
            band_tags = {k: v for k, v in ds.tags(1).items() if v not in (None, "")}
            units = None
            for key in ("units", "unit", "UNITS"):
                if key in band_tags:
                    units = band_tags[key]
                    break
            if units is None and ds.descriptions and ds.descriptions[0]:
                units = ds.descriptions[0]

            px_km = _pixel_size_km(ds)
            report.info = {
                "driver": ds.driver,
                "crs": _crs_name(ds),
                "is_geographic": bool(ds.crs is not None and ds.crs.is_geographic),
                "width": ds.width,
                "height": ds.height,
                "count": ds.count,
                "dtype": ds.dtypes[0] if ds.dtypes else "unknown",
                "nodata": ds.nodata,
                "pixel_native": (abs(ds.transform.a), abs(ds.transform.e)),
                "pixel_km": px_km,
                "bounds": tuple(ds.bounds),
                "overviews": ds.overviews(1),
                "compression": ds.compression.value if ds.compression else None,
                "units": units,
                "tags": tags,
                "band_tags": band_tags,
                "sample_shape": (out_height, out_width),
                "sample_decimation": decimation,
                "sampled": sampled,
                "valid_fraction": float(values.size / (out_height * out_width)),
                "n_valid": int(values.size),
                **stats,
            }
    except Exception as exc:  # pragma: no cover - only on corrupt files
        report.error = f"{type(exc).__name__}: {exc}"
    return report


def inspect_psr_csv(path: Path) -> dict[str, Any]:
    """Summarise the lunar permanently-shadowed-region polygon table."""
    csv.field_size_limit(10**9)
    out: dict[str, Any] = {
        "columns": [],
        "n_rows": 0,
        "area_km2": {},
        "vertex_count": {},
        "bbox_m": None,
        "radial_m": None,
        "indicative_lat_range": None,
        "polygons_touching_tile_edge": 0,
        "error": None,
    }
    try:
        with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            out["columns"] = list(reader.fieldnames or [])
            areas: list[float] = []
            vertices: list[int] = []
            xs: list[float] = []
            ys: list[float] = []
            for row in reader:
                out["n_rows"] += 1
                try:
                    areas.append(float(row["area_km2"]))
                except (TypeError, ValueError):
                    pass
                coords = [float(value) for value in NUMBER_RE.findall(row.get("WKT") or "")]
                if len(coords) >= 4:
                    vertices.append(len(coords) // 2)
                    xs.extend(coords[0::2])
                    ys.extend(coords[1::2])
                    if any(abs(value) >= 303_980 for value in coords):
                        out["polygons_touching_tile_edge"] += 1
        if areas:
            out["area_km2"] = {
                "min": min(areas),
                "median": float(np.median(areas)),
                "max": max(areas),
                "sum": float(np.sum(areas)),
            }
        if vertices:
            out["vertex_count"] = {
                "min": min(vertices),
                "median": float(np.median(vertices)),
                "max": max(vertices),
            }
        if xs and ys:
            out["bbox_m"] = (min(xs), min(ys), max(xs), max(ys))
            radii = np.hypot(np.asarray(xs), np.asarray(ys))
            out["radial_m"] = (float(radii.min()), float(radii.max()))
            # Convert radial distance to indicative latitude (spherical Moon).
            out["indicative_lat_range"] = tuple(
                -90.0 + math.degrees(radius / 1_737_400.0) for radius in out["radial_m"]
            )
    except Exception as exc:  # pragma: no cover - only on corrupt CSV
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _format_value(value: Any) -> str:
    """Format a scalar for the markdown report."""
    if value is None:
        return "—"
    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        return f"{value:.6g}"
    return str(value)


def _layer_table(reports: Iterable[RasterReport]) -> list[str]:
    """Render a compact per-body markdown table."""
    lines = [
        "| ID | File | Feature | CRS | Native pixel | Size (px) | dtype | Nodata | Valid range (sampled) | Valid % | Units |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for report in reports:
        layer = report.layer
        if report.error:
            lines.append(
                f"| {layer.layer_id} | `{report.path.name}` | {layer.feature} | — | — | — | — | — | — | — | **FAILED: {report.error}** |"
            )
            continue
        info = report.info
        px = info["pixel_km"]
        if px is None:
            pixel = "no CRS"
        elif info.get("is_geographic"):
            pixel = f"{px[0]:.3f}×{px[1]:.3f} km (approx)"
        else:
            pixel = f"{px[0]:.3f}×{px[1]:.3f} km"
        value_range = "—"
        if "min" in info:
            value_range = f"{info['min']:.4g} … {info['max']:.4g}"
        lines.append(
            "| {id} | `{name}` | {feature} | {crs} | {pixel} | {w}×{h} | {dtype} | {nodata} | {range} | {valid:.1f}% | {units} |".format(
                id=layer.layer_id,
                name=report.path.name,
                feature=layer.feature,
                crs=info["crs"],
                pixel=pixel,
                w=info["width"],
                h=info["height"],
                dtype=info["dtype"],
                nodata=_format_value(info["nodata"]),
                range=value_range,
                valid=100.0 * info["valid_fraction"],
                units=info["units"] or layer.documented_units,
            )
        )
    return lines


def _coverage_by_zone(path: Path, zone_rows: dict[str, np.ndarray]) -> dict[str, float]:
    """Fraction of valid (land) pixels in each latitude zone for a raster."""
    with rasterio.open(path) as ds:
        decimation = max(1, math.ceil(max(ds.width, ds.height) / 2048))
        out_height = max(1, ds.height // decimation)
        out_width = max(1, ds.width // decimation)
        data = ds.read(1, out_shape=(out_height, out_width), resampling=Resampling.nearest, masked=True)
        valid = ~np.ma.getmaskarray(data)
        result: dict[str, float] = {}
        for zone, rows in zone_rows.items():
            subset = valid[rows, :]
            result[zone] = float(subset.mean()) if subset.size else float("nan")
        return result


def _latitude_zones(ds: rasterio.DatasetReader, height: int) -> dict[str, np.ndarray]:
    """Return row indices for Arctic, temperate and Antarctic zones."""
    if ds.crs is not None and ds.crs.is_geographic:
        rows = np.arange(height)
        # Row centres of the decimated raster; transform is for sampled grid,
        # but the latitude ordering is what matters here, so interpolate bounds.
        top = ds.bounds.top
        lat = top - (rows + 0.5) * (top - ds.bounds.bottom) / height
    else:
        lat = np.linspace(90.0, -90.0, height)
    return {
        "arctic >=66.5N": lat >= 66.5,
        "temperate": (lat > -66.5) & (lat < 66.5),
        "antarctic <=66.5S": lat <= -66.5,
    }


def _manifest_reconciliation() -> tuple[list[str], list[str]]:
    """List files missing from the manifest download and extra files found."""
    missing: list[str] = []
    extra: list[str] = []

    expected_moon = {layer.filename.lower() for layer in MOON_LAYERS}
    expected_moon.update({
        "ldrm_80s_1000mpp_adj_rough_800m.tiff",
        "ldrm_80s_1000mpp_adj_rough_1600m.tiff",
        "ldrm_80s_1000mpp_adj_slp_800m.tiff",
        "ldrm_80s_1000mpp_adj_slp_1600m.tiff",
        "ldrm_80s_1000mpp_adj_h.tiff",
        "ldrm_80s_1000mpp_adj_spslp.tiff",
        "lpsr_80s_20mpp_adj_1km2.csv",
        "moon_thermal_literature.csv",
    })
    for path in RAW["moon"].iterdir():
        if path.is_file() and path.name.lower() not in expected_moon:
            extra.append(f"moon/{path.name}")

    for known in ("moon_thermal_literature.csv",):
        if not (RAW["moon"] / known).exists():
            missing.append(f"moon/{known} (HAND-MADE, must be authored from literature)")

    expected_mars = {
        "mars_elev.npy",
        "mars_thermal_literature.csv",
    }
    mars_known_raw = {"megt90n000eb.img", "mega90n000cb.img", "nmap2003.tif"}
    for known in sorted(expected_mars):
        if not (RAW["mars"] / known).exists():
            missing.append(f"mars/{known}" + (" (HAND-MADE)" if "literature" in known else " (raw MOLA .img is present instead)"))
    for path in RAW["mars"].iterdir():
        if path.is_file() and path.name.lower() not in expected_mars and path.name.lower() not in mars_known_raw:
            extra.append(f"mars/{path.name}")

    earth_expected_prefixes = ("wc2.1_", "etopo_")
    for path in RAW["earth"].iterdir():
        if path.is_file() and not path.name.lower().startswith(earth_expected_prefixes):
            extra.append(f"earth/{path.name}")

    # A few Moon global products sit one level above the per-body folders.
    known_root = {"datasets.md"}
    for path in DATA_ROOT.iterdir():
        if path.is_file() and path.name.lower() not in known_root:
            extra.append(f"{path.name} (Datasets root, not in per-body folder)")
    return missing, extra


def build_report(max_dim: int = 2048) -> str:
    """Run the full inventory and return the markdown document."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: list[str] = [
        "# Data inventory",
        "",
        f"Generated by `python -m backend.pipeline.inspect_datasets` on {now}.",
        "",
        "This is the Phase 0 verification of every dataset listed in `docs/DATASETS.md`.",
        "All rasters were opened read-only. Large rasters were sampled through a decimated",
        f"window (long side <= {max_dim} px); sampled value ranges are labelled below.",
        "",
        "**Source note.** The raw data live outside the project folder in `../Datasets/`",
        "(`Moon/`, `Mars/`, `Earth/`), mapped by `backend/paths.py`. They are git-ignored.",
        "",
        "---",
        "",
        "## 1. Moon (`Datasets/Moon/`)",
        "",
    ]

    moon_reports = [
        inspect_raster(_find_case_insensitive(RAW["moon"], layer.filename), layer, max_dim)
        if _find_case_insensitive(RAW["moon"], layer.filename)
        else RasterReport(path=RAW["moon"] / layer.filename, layer=layer, error="file not found")
        for layer in MOON_LAYERS
    ]
    lines.extend(_layer_table(moon_reports))
    lines.extend([
        "",
        "All Moon GeoTIFFs except M9 use the same custom **Moon 2015 south polar "
        "stereographic** projection (sphere R = 1737.4 km, true scale at 90°S, "
        "central meridian 0°). The square grid spans ±303.99 km: this is 80°S at the "
        "edge midpoints, but the corners reach roughly 76°S. M9 (`ldem_16.tif`) is a "
        "plain 16 ppd context image with **no CRS or geotransform** and must not be used for slope.",
        "",
    ])

    psr_path = _find_case_insensitive(RAW["moon"], "LPSR_80S_20MPP_ADJ_1km2.csv")
    lines.extend(["### M8 — permanently shadowed regions (PSR) polygon table", ""])
    if psr_path is None:
        lines.append("**File not found.**")
    else:
        psr = inspect_psr_csv(psr_path)
        if psr["error"]:
            lines.append(f"**Failed to parse:** {psr['error']}")
        else:
            lines.append(f"- File: `{psr_path.name}` ({psr_path.stat().st_size / 1e6:.1f} MB)")
            lines.append(f"- Columns: `{', '.join(psr['columns'])}`")
            lines.append(f"- Rows (polygons): **{psr['n_rows']:,}**")
            if psr["area_km2"]:
                area = psr["area_km2"]
                lines.append(
                    f"- Polygon area (km²): min {area['min']:.3g}, median {area['median']:.3g}, "
                    f"max {area['max']:.3g}, total {area['sum']:.6g}"
                )
            if psr["vertex_count"]:
                vc = psr["vertex_count"]
                lines.append(
                    f"- Vertices per polygon: min {vc['min']:.0f}, median {vc['median']:.0f}, max {vc['max']:.0f}"
                )
            if psr["bbox_m"]:
                bbox = psr["bbox_m"]
                lines.append(
                    "- Coordinate bounding box (metres, as stored): "
                    f"x [{bbox[0]:.0f}, {bbox[2]:.0f}], y [{bbox[1]:.0f}, {bbox[3]:.0f}]"
                )
                lines.append(
                    f"- Polygons touching the ±303.99 km tile edge: {psr['polygons_touching_tile_edge']} "
                    "(their footprint is clipped at 80°S, so areas are lower bounds there)"
                )
            if psr["radial_m"]:
                r_min, r_max = psr["radial_m"]
                lat_min, lat_max = psr["indicative_lat_range"]
                lines.append(
                    f"- Radial distance from the pole (metres, as stored): {r_min:.0f} … {r_max:.0f}. "
                    f"Indicative latitudes **{lat_min:.2f}° to {lat_max:.2f}°** under an assumed spherical "
                    "south-polar stereographic projection (R = 1737.4 km). The CSV carries no CRS metadata, "
                    "so this is a sanity check, not a georeference. The ~76°S minimum comes from the "
                    "corners of the square tile, not from a latitude cut."
                )
            lines.append(
                "- Interpretation: one row per permanently shadowed region > 1 km², with its "
                "polygon footprint, area and LOLA granule identifier. This is the cold-trap/ice proxy."
            )
    lines.append("")

    lines.extend(["## 2. Mars (`Datasets/Mars/`)", ""])
    mars_elev = RAW["mars"] / "mars_elev.npy"
    if not mars_elev.exists():
        lines.extend([
            "**Manifest mismatch:** `mars_elev.npy` is not on disk.",
            "",
            "The equivalent source is present as the raw PDS product "
            "`megt90n000eb.img` (MOLA MEGDR topography, 16 ppd). It is a header-less",
            "big-endian int16 raster: file size 33,177,600 bytes = 2880 × 5760 × 2.",
            "Phase 2 can read it directly with `numpy.memmap`; no re-download is needed.",
            "",
        ])
        raw_report = _inspect_raw_mola(RAW["mars"] / "megt90n000eb.img")
        lines.extend(_raw_mola_table(raw_report))
        lines.append("")

    mars_extras = [
        ("megt90n000eb.img", "MOLA MEGDR topography, raw int16 big-endian, 2880×5760 (16 ppd)"),
        ("mega90n000cb.img", "MOLA shaded-relief image, auxiliary; no PDS label on disk, not used"),
        ("nmap2003.tif", "Mars Viking color mosaic, auxiliary basemap (not in manifest)"),
    ]
    lines.extend(["### Additional Mars files found", ""])
    for filename, description in mars_extras:
        path = RAW["mars"] / filename
        if path.exists():
            lines.append(f"- `{filename}` — {path.stat().st_size / 1e6:.1f} MB — {description}")
        else:
            lines.append(f"- `{filename}` — not found")
    lines.extend([
        "",
        "- Optional TES thermal-inertia TIF — **not present** (manifest marks it OPTIONAL). "
        "`nmap2003.tif` above is a Viking colour mosaic, not TES, and is not a numeric thermal layer.",
        "",
    ])

    lines.extend(["## 3. Earth (`Datasets/Earth/`)", ""])
    earth_reports: list[RasterReport] = []
    for layer in EARTH_LAYERS:
        path = _find_case_insensitive(RAW["earth"], layer.filename)
        earth_reports.append(
            inspect_raster(path, layer, max_dim) if path else RasterReport(path=RAW["earth"] / layer.filename, layer=layer, error="file not found")
        )
    lines.extend(_layer_table(earth_reports))
    lines.extend([
        "",
        "ETOPO's CRS is the compound **WGS 84 + EGM2008 height** (EPSG:9518): horizontal "
        "coordinates are lon/lat, elevations are metres above the EGM2008 geoid. No vertical "
        "datum conversion is needed for relative terrain features.",
        "",
    ])

    lines.extend(["### WorldClim 2.1 bioclimatic layers", ""])
    wc_reports: list[RasterReport] = []
    for layer in WORLDCLIM_LAYERS:
        path = _find_case_insensitive(RAW["earth"], layer.filename)
        wc_reports.append(
            inspect_raster(path, layer, max_dim) if path else RasterReport(path=RAW["earth"] / layer.filename, layer=layer, error="file not found")
        )
    lines.extend(_layer_table(wc_reports))
    lines.append("")

    bio1_path = _find_case_insensitive(RAW["earth"], "wc2.1_2.5m_bio_1.tif")
    if bio1_path:
        with rasterio.open(bio1_path) as ds:
            res_deg = abs(ds.transform.a)
            resolution = res_deg * 60.0
            lines.append(
                f"**Detected resolution: {resolution:.2f} arc-minutes ({res_deg:.4f}°)** — "
                f"the 2.5 arc-minute product (≈{res_deg * 111.32:.1f} km at the equator). "
                "This is close to the 0.05° target grid, so it will be lightly aggregated, not invented."
            )
    else:
        lines.append("**WorldClim bio_1 not found in the expected location.**")
    lines.append("")

    zip_path = _find_case_insensitive(RAW["earth"], "wc2.1_10m_bio.zip")
    if zip_path:
        with zipfile.ZipFile(zip_path) as archive:
            members = archive.namelist()
        lines.append(
            f"Fallback archive `{zip_path.name}` contains {len(members)} entries; "
            "10 arc-minute data will only be used if the 2.5-minute layers fail."
        )
        lines.append("")

    lines.extend(["### Polar coverage check (WorldClim land mask)", ""])
    lines.append(
        "WorldClim ocean cells are nodata, so these fractions are *land* coverage, not "
        "missing-data coverage. A low Antarctic/Arctic fraction can be a real ocean/ice-shelf gap."
    )
    lines.append("")
    lines.append("| Layer | Arctic ≥66.5°N valid | Temperate valid | Antarctic ≤66.5°S valid |")
    lines.append("|---|---|---|---|")
    zone_table: dict[str, dict[str, float]] = {}
    for layer, report in zip(WORLDCLIM_LAYERS, wc_reports):
        if report.error:
            continue
        with rasterio.open(report.path) as ds:
            zones = _latitude_zones(ds, max(1, ds.height // max(1, math.ceil(max(ds.width, ds.height) / 2048))))
        coverage = _coverage_by_zone(report.path, zones)
        zone_table[layer.layer_id] = coverage
        lines.append(
            f"| {layer.layer_id} | {100 * coverage['arctic >=66.5N']:.1f}% | "
            f"{100 * coverage['temperate']:.1f}% | {100 * coverage['antarctic <=66.5S']:.1f}% |"
        )
    lines.append("")

    etopo_report = earth_reports[0] if earth_reports else None
    if etopo_report and not etopo_report.error:
        with rasterio.open(etopo_report.path) as ds:
            height = max(1, ds.height // max(1, math.ceil(max(ds.width, ds.height) / 2048)))
            zones = _latitude_zones(ds, height)
        coverage = _coverage_by_zone(etopo_report.path, zones)
        lines.append(
            "ETOPO includes bathymetry, so its valid fraction is ~100% everywhere "
            f"(Arctic {100 * coverage['arctic >=66.5N']:.1f}%, temperate "
            f"{100 * coverage['temperate']:.1f}%, Antarctic {100 * coverage['antarctic <=66.5S']:.1f}%). "
            "The WorldClim land mask must therefore be applied before terrain features are ranked."
        )
        lines.append("")

    lines.extend(["## 4. Manifest reconciliation", ""])
    missing, extra = _manifest_reconciliation()
    lines.append("### Missing or different from `docs/DATASETS.md`")
    lines.append("")
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- none")
    lines.extend(["", "### Additional files found (not in the manifest)", ""])
    if extra:
        lines.extend(f"- `{item}`" for item in extra)
    else:
        lines.append("- none")
    lines.extend([
        "",
        "### Naming inconsistencies",
        "",
        "- The Moon GeoTIFFs are stored with lowercase `.tiff`, while the manifest lists `.TIF`. Same files.",
        "- The Mars raster is the original PDS `.img`, not the manifest's converted `mars_elev.npy`.",
        "- Both the 2.5 arc-minute individual bio layers and their zip archives are present; the",
        "  individual layers are the ones actually inspected and will be used.",
        "",
        "## 5. Known limitations carried into later phases",
        "",
        "- WorldClim is **air temperature** (1970–2000 climatology), not surface skin temperature.",
        "- WorldClim Antarctic values are interpolated from sparse stations; treat them as weak evidence.",
        "- Moon rasters cover only poleward of 80°S, in polar stereographic metres; never treat the",
        "  projected grid as lon/lat or compute slope directly in pixel units without the transform.",
        "- Mars MOLA is 16 ppd (~3.7 km); ETOPO is 60 arc-sec (~1.85 km); Moon DEMs are 80 m–1 km.",
        "  Features must be compared in km-sized windows, not in pixel windows.",
        "- Moon and Mars temperatures are literature values (hand-made CSVs), not rasters.",
        "- Earth cannot reproduce gravity, vacuum/thin atmosphere, or radiation.",
        "",
    ])
    return "\n".join(lines)


def _inspect_raw_mola(path: Path) -> dict[str, Any]:
    """Sample the header-less MOLA int16 raster without loading it fully."""
    expected_shape = (2880, 5760)
    result: dict[str, Any] = {"path": path, "shape": expected_shape, "dtype": ">i2", "nodata": -32768}
    if not path.exists():
        result["error"] = "file not found"
        return result
    data = np.memmap(path, dtype=">i2", mode="r", shape=expected_shape)
    sample = np.asarray(data[::8, ::8], dtype="float64")
    valid = sample[sample != -32768]
    stats = _finite_stats(valid)
    result.update(stats)
    result["valid_fraction"] = float(valid.size / sample.size)
    result["sample"] = "every 8th row/column"

    def elevation(lat: float, lon_east: float) -> int:
        row = int(round((90.0 - lat) * 16.0 - 0.5))
        col = int(round(lon_east * 16.0 - 0.5))
        return int(data[row, col])

    # Orientation check: these published sites must land at the right sign/altitude.
    result["checks"] = {
        "Jezero (18.4N, 77.5E)": elevation(18.4, 77.5),
        "Olympus Mons (18.65N, 226.2E)": elevation(18.65, 226.2),
        "Hellas (42.4S, 70.5E)": elevation(-42.4, 70.5),
    }
    return result


def _raw_mola_table(report: dict[str, Any]) -> list[str]:
    """Render the raw MOLA sample as a small table."""
    if "error" in report:
        return [f"Raw MOLA check failed: {report['error']}"]
    return [
        "| File | Shape | dtype | Nodata | Valid range (sampled) | Valid % |",
        "|---|---|---|---|---|---|",
        f"| `{report['path'].name}` | {report['shape'][0]}×{report['shape'][1]} | {report['dtype']} | "
        f"{report['nodata']} | {report.get('min', float('nan')):.1f} … {report.get('max', float('nan')):.1f} m | "
        f"{100 * report['valid_fraction']:.1f}% |",
        "",
        f"Sample: {report['sample']}. This confirms the file is the MOLA 16 ppd topography grid.",
        "",
        "**Orientation check** (values sampled at published coordinates):",
        "",
        *[f"- {name}: {value:,} m" for name, value in report.get("checks", {}).items()],
        "",
        "The grid is simple cylindrical, **north-up, with longitude running 0–360°E** "
        "(not −180…180). Coordinates must be converted before sampling in Phase 2. "
        "The file has no embedded PDS label or CRS; latitude convention (planetocentric "
        "vs planetographic) still needs confirmation.",
    ]


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DOCS_DIR / "data_inventory.md", help="output markdown file")
    parser.add_argument("--max-dim", type=int, default=2048, help="maximum sampled raster dimension")
    args = parser.parse_args()

    report = build_report(max_dim=args.max_dim)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Data root: {RAW['moon'].parent}")


if __name__ == "__main__":
    main()
