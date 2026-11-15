"""Merge the Earth terrain and climate stores, apply the land mask, and publish.

Phase 1 final step. Reads the two intermediate NetCDF stores, writes
``data/processed/earth_features.nc`` with every MVP feature masked to land,
then creates one quick-look map per feature and a coverage/limits report.

Run from ``NASA_Space_Challenge/``::

    python -m backend.pipeline.build_earth_features

Use ``--keep-intermediates`` to retain the two source stores.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from netCDF4 import Dataset

from backend.paths import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR, RAW
from backend.pipeline.earth_grid import (
    LAT_MAX,
    LON_MIN,
    NX,
    NY,
    RES_DEG,
    lat_centers,
    lon_centers,
)
from backend.pipeline.feature_store import CHUNK_ROWS, GridStore

TERRAIN_VARIABLES = [
    "relief_20km_m",
    "slope_20km_deg",
    "roughness_5km_m",
    "roughness_10km_m",
    "roughness_20km_m",
    "hurst_2_32km",
]
CLIMATE_VARIABLES = [
    "temp_mean_c",
    "temp_diurnal_range_c",
    "temp_max_warmest_c",
    "temp_min_coldest_c",
    "temp_annual_range_c",
    "precip_annual_mm",
    "precip_driest_month_mm",
]
FEATURE_VARIABLES = TERRAIN_VARIABLES + CLIMATE_VARIABLES

PLOT_STYLE: dict[str, tuple[str, str]] = {
    "relief_20km_m": ("terrain", "Local relief (m)"),
    "slope_20km_deg": ("magma", "Mean slope (degrees)"),
    "roughness_5km_m": ("cividis", "Roughness at 5 km (m)"),
    "roughness_10km_m": ("cividis", "Roughness at 10 km (m)"),
    "roughness_20km_m": ("cividis", "Roughness at 20 km (m)"),
    "hurst_2_32km": ("viridis", "Hurst exponent (2-32 km)"),
    "temp_mean_c": ("RdYlBu_r", "Mean annual air temperature (°C)"),
    "temp_diurnal_range_c": ("plasma", "Mean diurnal range (°C)"),
    "temp_max_warmest_c": ("inferno", "Warmest-month maximum (°C)"),
    "temp_min_coldest_c": ("RdYlBu", "Coldest-month minimum (°C)"),
    "temp_annual_range_c": ("plasma", "Annual temperature range (°C)"),
    "precip_annual_mm": ("YlGnBu", "Annual precipitation (mm)"),
    "precip_driest_month_mm": ("YlGnBu", "Driest-month precipitation (mm)"),
}

VALIDATION_SITES = [
    ("Atacama", -23.5, -68.5),
    ("Dry Valleys", -77.5, 162.0),
    ("Devon Island", 75.4, -89.5),
    ("Death Valley", 36.5, -116.9),
    ("Iceland", 64.9, -19.0),
    ("Sahara", 23.0, 10.0),
]


def _copy_attrs(source, destination) -> None:
    """Copy NetCDF attributes, skipping reserved underscore names."""
    for key in source.ncattrs():
        if key.startswith("_"):
            continue
        setattr(destination, key, getattr(source, key))


def merge_features(
    terrain_path: Path,
    climate_path: Path,
    output: Path,
) -> dict[str, Any]:
    """Merge terrain and climate, apply the land mask, and return metadata."""
    for source_path in (terrain_path, climate_path):
        if not source_path.exists():
            raise FileNotFoundError(
                f"{source_path} not found; run the earth_climate and earth_terrain steps first"
            )
    if output.exists():
        output.unlink()

    started = time.perf_counter()
    with Dataset(terrain_path) as terrain, Dataset(climate_path) as climate:
        land_mask = climate.variables["land_mask"][:].astype(bool)
        land_fraction = climate.variables["land_fraction"][:].astype("float32")

        with GridStore(output, mode="w") as store:
            for name in FEATURE_VARIABLES:
                source = terrain.variables[name] if name in terrain.variables else climate.variables[name]
                destination = store.create_feature(name, {})
                _copy_attrs(source, destination)
                if name == "temp_min_coldest_c":
                    destination.setncattr(
                        "feature_group",
                        "temperature; Earth cold-extreme proxy for lunar cold traps",
                    )
                elif name.startswith("temp"):
                    destination.setncattr("feature_group", "temperature")
                elif name.startswith("precip"):
                    destination.setncattr("feature_group", "dryness")
                else:
                    destination.setncattr("feature_group", "terrain")

                for row0 in range(0, NY, CHUNK_ROWS):
                    row1 = min(NY, row0 + CHUNK_ROWS)
                    values = source[row0:row1, :].astype("float32")
                    mask = land_mask[row0:row1, :]
                    values[~mask] = np.nan
                    destination[row0:row1, :] = values

            fraction_out = store.create_feature(
                "land_fraction",
                {
                    "long_name": "Fraction of WorldClim source cells that are land",
                    "units": "1",
                    "definition": "area average of the WorldClim bio_1 valid mask at 0.05 degrees",
                },
            )
            fraction_out[:] = land_fraction

            mask_out = store.create_feature(
                "land_mask",
                {
                    "long_name": "Earth land mask from WorldClim ocean nodata",
                    "units": "1",
                    "definition": "1 where land_fraction >= 0.5, 0 for ocean; all features are NaN over ocean",
                },
                fill_value=-1,
                dtype="i1",
            )
            mask_out[:] = land_mask.astype("i1")

            store.set_attrs(
                {
                    "title": "Earth analog features for Moon and Mars targets, 0.05 degree grid",
                    "phase": "Phase 1 (Earth grid)",
                    "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "grid": "global 0.05 degree lon/lat, north-to-south rows, cell centres",
                    "terrain_source": "ETOPO 2022 v1 60 arc-second surface elevation (NOAA NCEI)",
                    "terrain_doi": "10.25921/fd45-gt74",
                    "climate_source": "WorldClim 2.1 bioclimatic variables, 2.5 arc-minute (Fick & Hijmans 2017)",
                    "climate_doi": "10.1002/joc.5086",
                    "land_mask_rule": "WorldClim ocean nodata; land where valid fraction >= 0.5",
                    "terrain_method": (
                        "10-degree tiles, local azimuthal-equidistant 2 km grid; "
                        "relief/slope/roughness/Hurst computed in km windows; "
                        "ocean cells filled with nearest land elevation before filtering; "
                        "area-averaged to 0.05 degrees"
                    ),
                    "climate_method": "area average from 2.5 arc-minute, slightly coarser than 0.05 degrees",
                    "limitations": (
                        "WorldClim is air temperature, not surface skin temperature. Earth cannot "
                        "replicate reduced gravity, vacuum/thin atmosphere, or radiation. Terrain "
                        "windows are limited by the 1.85 km ETOPO source. 0.05-degree cells shrink "
                        "in longitude toward the poles; feature values come from the 2 km working grid."
                    ),
                    "runtime_seconds": round(time.perf_counter() - started, 1),
                }
            )
    return {
        "land_mask": land_mask,
        "land_fraction": land_fraction,
        "runtime_seconds": time.perf_counter() - started,
    }


def _plot_panel(
    axis,
    values: np.ndarray,
    title: str,
    cmap: str,
    extent: tuple[float, float, float, float],
) -> None:
    """Draw one global map panel with a robust colour range."""
    masked = np.ma.masked_invalid(values)
    finite = masked.compressed()
    if finite.size:
        vmin, vmax = np.percentile(finite, [2, 98])
    else:
        vmin, vmax = 0.0, 1.0
    image = axis.imshow(
        masked,
        extent=extent,
        origin="upper",
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )
    axis.set_title(title, fontsize=9)
    axis.set_xticks([-120, -60, 0, 60, 120])
    axis.set_yticks([-60, -30, 0, 30, 60])
    axis.tick_params(labelsize=7)
    axis.grid(color="white", alpha=0.15, linewidth=0.3)
    return image


def write_figures(dataset_path: Path, figures_dir: Path) -> list[Path]:
    """Write one quick-look PNG per feature plus a combined overview."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    dataset = xr.open_dataset(dataset_path)
    stride = 4  # 0.2 degree quick-look, ~900 x 1800 pixels
    extent = (-180.0, 180.0, -90.0, 90.0)
    lon = dataset.lon.values[::stride]
    lat = dataset.lat.values[::stride]

    for name in FEATURE_VARIABLES:
        cmap, label = PLOT_STYLE[name]
        values = dataset[name].values[::stride, ::stride]
        figure, axis = plt.subplots(figsize=(14, 7), constrained_layout=True)
        image = _plot_panel(axis, values, label, cmap, extent)
        figure.colorbar(image, ax=axis, orientation="horizontal", pad=0.06, shrink=0.7)
        axis.set_xlabel("Longitude")
        axis.set_ylabel("Latitude")
        figure.suptitle(
            f"Earth analog feature: {label}",
            fontsize=14,
            fontweight="bold",
        )
        figure.text(
            0.5,
            -0.02,
            "0.05° search grid · ETOPO 2022 + WorldClim 2.1 · land mask from WorldClim ocean nodata",
            ha="center",
            fontsize=8,
            color="0.35",
        )
        path = figures_dir / f"earth_{name}.png"
        figure.savefig(path, dpi=160, bbox_inches="tight")
        plt.close(figure)
        written.append(path)

    # Combined overview: 4 x 4 panels, compact labels.
    figure, axes = plt.subplots(4, 4, figsize=(18, 11), constrained_layout=True)
    for axis, name in zip(axes.flat, FEATURE_VARIABLES):
        cmap, label = PLOT_STYLE[name]
        _plot_panel(axis, dataset[name].values[::stride, ::stride], label, cmap, extent)
    for axis in axes.flat[len(FEATURE_VARIABLES):]:
        axis.axis("off")
    figure.suptitle(
        "Earth feature grid for Moon/Mars analog search (0.05°, Phase 1)",
        fontsize=16,
        fontweight="bold",
    )
    figure.text(
        0.5,
        0.005,
        "Sources: ETOPO 2022 (NOAA NCEI) · WorldClim 2.1 (Fick & Hijmans 2017). "
        "Air temperature, not surface temperature.",
        ha="center",
        fontsize=9,
        color="0.35",
    )
    overview = figures_dir / "earth_features_overview.png"
    figure.savefig(overview, dpi=150, bbox_inches="tight")
    plt.close(figure)
    written.append(overview)
    dataset.close()
    return written


def _zone_stats(
    land_mask: np.ndarray, lat: np.ndarray, feature: np.ndarray | None = None
) -> dict[str, Any]:
    """Compute cell-count and area-weighted coverage in polar/temperate zones."""
    ny, nx = land_mask.shape
    weights = np.cos(np.deg2rad(lat))[:, None] * np.ones((1, nx))
    zones = {
        "global": np.broadcast_to(np.ones((ny, 1), dtype=bool), land_mask.shape),
        "arctic_ge_66.5N": np.broadcast_to(lat[:, None] >= 66.5, land_mask.shape),
        "temperate": np.broadcast_to(
            (lat[:, None] > -66.5) & (lat[:, None] < 66.5), land_mask.shape
        ),
        "antarctic_le_66.5S": np.broadcast_to(lat[:, None] <= -66.5, land_mask.shape),
    }
    stats: dict[str, Any] = {}
    for zone_name, zone in zones.items():
        zone_cells = int(zone.sum())
        zone_weight = float(weights[zone].sum())
        land_cells = int((land_mask & zone).sum())
        land_weight = float(weights[land_mask & zone].sum())
        row: dict[str, Any] = {
            "cells": zone_cells,
            "land_cells": land_cells,
            "land_cell_fraction": float(land_cells / zone_cells) if zone_cells else float("nan"),
            "land_area_fraction": land_weight / zone_weight if zone_weight else float("nan"),
        }
        if feature is not None:
            valid = np.isfinite(feature) & land_mask & zone
            row["valid_land_cells"] = int(valid.sum())
            row["valid_of_land"] = float(valid.sum() / land_cells) if land_cells else float("nan")
        stats[zone_name] = row
    return stats


def write_report(
    dataset_path: Path,
    figures: list[Path],
    intermediates: list[Path],
    report_path: Path,
    meta_path: Path,
) -> dict[str, Any]:
    """Write the Phase 1 coverage/limits report and a machine-readable metadata file."""
    dataset = xr.open_dataset(dataset_path)
    lat = dataset.lat.values
    lon = dataset.lon.values
    land_mask = dataset.land_mask.values.astype(bool)
    coverage = _zone_stats(land_mask, lat)

    feature_rows = []
    for name in FEATURE_VARIABLES:
        values = dataset[name].values
        valid = np.isfinite(values) & land_mask
        feature_rows.append(
            {
                "name": name,
                "units": str(dataset[name].attrs.get("units", "")),
                "long_name": str(dataset[name].attrs.get("long_name", name)),
                "min": float(np.nanmin(values[valid])) if valid.any() else float("nan"),
                "median": float(np.nanmedian(values[valid])) if valid.any() else float("nan"),
                "max": float(np.nanmax(values[valid])) if valid.any() else float("nan"),
                "valid_land_cells": int(valid.sum()),
                "valid_of_land": float(valid.sum() / land_mask.sum()),
            }
        )

    # Spot checks at well-known analog / non-analog sites.
    site_rows = []
    for label, site_lat, site_lon in VALIDATION_SITES:
        row = int(round((LAT_MAX - site_lat) / RES_DEG - 0.5))
        col = int(round((site_lon - LON_MIN) / RES_DEG - 0.5))
        row = min(max(row, 0), NY - 1)
        col = min(max(col, 0), NX - 1)
        site_rows.append(
            {
                "site": label,
                "lat": site_lat,
                "lon": site_lon,
                "temp_mean_c": float(dataset.temp_mean_c.values[row, col]),
                "temp_min_coldest_c": float(dataset.temp_min_coldest_c.values[row, col]),
                "precip_annual_mm": float(dataset.precip_annual_mm.values[row, col]),
                "relief_20km_m": float(dataset.relief_20km_m.values[row, col]),
                "slope_20km_deg": float(dataset.slope_20km_deg.values[row, col]),
                "land_mask": int(land_mask[row, col]),
            }
        )

    sizes = {path.name: path.stat().st_size / 1e6 for path in [dataset_path, *intermediates] if path.exists()}
    metadata = {
        "grid": {
            "resolution_deg": RES_DEG,
            "nx": NX,
            "ny": NY,
            "lon_min": float(LON_MIN),
            "lat_max": float(LAT_MAX),
            "lat_order": "north_to_south",
        },
        "sources": {
            "terrain": "ETOPO 2022 v1 60 arc-second surface elevation, NOAA NCEI, doi:10.25921/fd45-gt74",
            "climate": "WorldClim 2.1 bio layers, 2.5 arc-minute, Fick & Hijmans 2017, doi:10.1002/joc.5086",
        },
        "features": feature_rows,
        "coverage": coverage,
        "spot_checks": site_rows,
        "file_sizes_mb": sizes,
        "figures": [str(path.relative_to(report_path.parent.parent)) for path in figures],
        "limitations": [
            "WorldClim is air temperature (1970-2000 climatology), not surface skin temperature.",
            "WorldClim Antarctic values are interpolated from sparse stations; treat as weak evidence.",
            "ETOPO is 1.85 km; the 0.05 degree grid is ~5.6 km at the equator but much smaller in longitude near the poles.",
            "Coastal terrain uses the nearest land elevation for ocean cells, so shelf bathymetry does not inflate relief.",
            "Earth cannot reproduce reduced gravity, vacuum/thin atmosphere, or radiation.",
            "Moon and Mars temperatures are literature values and are not part of this Earth grid.",
        ],
    }
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    lines = [
        "# Earth feature grid — Phase 1 report",
        "",
        f"Generated by `python -m backend.pipeline.build_earth_features` on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        "## Grid",
        "",
        f"- Global **0.05° lon/lat** grid, {NX} × {NY} cells, north-to-south rows, cell centres.",
        f"- Terrain: ETOPO 2022 60 arc-second (1.85 km) reprojected in 10° tiles to a local 2 km azimuthal-equidistant grid; features computed in km windows; ocean cells filled with the nearest land elevation before filtering; sampled back with area averaging.",
        "- Climate: WorldClim 2.1 2.5 arc-minute (~4.6 km) area-averaged to 0.05°; this is a slight coarsening, not added detail.",
        "- Land mask: WorldClim ocean nodata; a 0.05° cell is land when the majority of its source cells are valid. Every feature is NaN over ocean.",
        "",
        "## Features",
        "",
        "| Variable | Long name | Units | Land min | Land median | Land max | Valid land cells |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in feature_rows:
        lines.append(
            f"| `{row['name']}` | {row['long_name']} | {row['units']} | "
            f"{row['min']:.4g} | {row['median']:.4g} | {row['max']:.4g} | "
            f"{row['valid_land_cells']:,} ({100 * row['valid_of_land']:.1f}%) |"
        )
    lines.extend(["", "## Coverage", ""])
    lines.append("| Zone | Cells | Land cells | Land share of cells | Area-weighted land share |")
    lines.append("|---|---|---|---|---|")
    for zone, row in coverage.items():
        lines.append(
            f"| {zone} | {row['cells']:,} | {row['land_cells']:,} | "
            f"{100 * row['land_cell_fraction']:.1f}% | {100 * row['land_area_fraction']:.1f}% |"
        )
    lines.extend(
        [
            "",
            "The area-weighted global land share should be close to Earth's ~29% land area; the "
            "cell-count share is higher because polar cells are over-represented in a lon/lat grid.",
            "",
            "## Polar coverage notes",
            "",
            "- **Antarctica** is present in the land mask (WorldClim has data over the ice sheet), so "
            "Dry Valleys-type sites are searchable. WorldClim Antarctic values come from sparse stations.",
            "- **Arctic** land is present, but ocean/ice-shelf cells are correctly excluded by the "
            "WorldClim nodata mask; this is a real coverage boundary, not missing data.",
            "- At 0.05°, a cell is only ~0.5 km wide in longitude at 85° latitude; terrain features come "
            "from the 2 km working grid, so adjacent polar cells repeat the same terrain sample. This "
            "is documented rather than hidden.",
            "",
            "## Spot checks",
            "",
            "| Site | Lat | Lon | Mean air T (°C) | Coldest min (°C) | Annual precip (mm) | Relief 20 km (m) | Slope 20 km (°) | Land |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for row in site_rows:
        lines.append(
            f"| {row['site']} | {row['lat']:.1f} | {row['lon']:.1f} | {row['temp_mean_c']:.1f} | "
            f"{row['temp_min_coldest_c']:.1f} | {row['precip_annual_mm']:.1f} | "
            f"{row['relief_20km_m']:.0f} | {row['slope_20km_deg']:.1f} | {row['land_mask']} |"
        )
    lines.extend(["", "## Files and figures", ""])
    for name, size in sizes.items():
        note = " *(intermediate)*" if name != dataset_path.name else ""
        lines.append(f"- `data/processed/{name}` — {size:.1f} MB{note}")
    lines.append(f"- `data/processed/{meta_path.name}` — machine-readable metadata")
    for path in figures:
        lines.append(f"- `{path.relative_to(report_path.parent.parent).as_posix()}`")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- WorldClim is **air temperature**, not surface skin temperature, and its Antarctic values are weakly constrained.",
            "- ETOPO includes bathymetry; the WorldClim land mask removes ocean cells, and ocean cells are filled with the nearest land elevation before filtering so coastal relief is not inflated by the shelf.",
            "- The 0.05° grid is not equal-area. At high latitudes, longitude cells are much narrower than at the equator; area weighting is reported above.",
            "- Earth cannot reproduce reduced gravity, vacuum or the thin Martian atmosphere, or the radiation environment.",
            "- Moon and Mars temperatures are literature values, added in Phase 2; no synthetic temperature raster is used.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    dataset.close()
    return metadata


def build(
    terrain_path: Path,
    climate_path: Path,
    output: Path,
    keep_intermediates: bool = False,
    refresh: bool = False,
) -> None:
    """Run the merge, figures and report (or just figures/report with ``refresh``)."""
    started = time.perf_counter()
    meta_path = PROCESSED_DIR / "earth_features_meta.json"
    report_path = DOCS_DIR / "earth_grid_report.md"
    if refresh:
        if not output.exists():
            raise FileNotFoundError(f"{output} not found; cannot refresh figures")
        figures = write_figures(output, FIGURES_DIR)
        write_report(output, figures, [], report_path, meta_path)
        print(f"Refreshed {len(figures)} figures for {output}")
        print(f"Wrote {report_path}")
        return

    merge_features(terrain_path, climate_path, output)
    figures = write_figures(output, FIGURES_DIR)
    intermediates = [terrain_path, climate_path] if not keep_intermediates else []
    write_report(output, figures, intermediates, report_path, meta_path)
    if not keep_intermediates:
        for path in (terrain_path, climate_path):
            if path.exists():
                path.unlink()
    print(f"Wrote {output}")
    print(f"Wrote {report_path}")
    print(f"Wrote {len(figures)} figures to {FIGURES_DIR}")
    print(f"Total {time.perf_counter() - started:.1f} s")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terrain", type=Path, default=PROCESSED_DIR / "earth_terrain.nc")
    parser.add_argument("--climate", type=Path, default=PROCESSED_DIR / "earth_climate.nc")
    parser.add_argument("--output", type=Path, default=PROCESSED_DIR / "earth_features.nc")
    parser.add_argument("--keep-intermediates", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="regenerate figures and report from an existing earth_features.nc",
    )
    args = parser.parse_args()
    build(
        args.terrain,
        args.climate,
        args.output,
        args.keep_intermediates,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    main()
