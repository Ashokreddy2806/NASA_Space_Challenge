"""Merge the Earth terrain and climate stores, apply the land mask, and publish.

Phase 1 final step. Reads the two intermediate NetCDF stores, writes the
configured ``earth_features`` dataset with every MVP feature masked to land,
then creates one quick-look map per feature and a coverage/limits report.

Every feature id, plot style, validation site, figure setting and output path
comes from ``config/*.yaml``.

Run from ``NASA_Space_Challenge/``::

    python -m backend.pipeline.build_earth_features

Use ``--keep-intermediates`` to retain the two source stores, ``--refresh`` to
regenerate figures and the report from an existing dataset, and ``--config`` to
run a proof override.
"""

from __future__ import annotations

import argparse
import json
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

from backend.config import AppConfig, ValidationSite, load_config
from backend.features import registry
from backend.paths import PROJECT_ROOT
from backend.pipeline.earth_grid import sample_point_rowcol
from backend.pipeline.feature_store import GridStore


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
    config: AppConfig,
) -> dict[str, Any]:
    """Merge terrain and climate, apply the land mask, and return metadata."""
    for source_path in (terrain_path, climate_path):
        if not source_path.exists():
            raise FileNotFoundError(
                f"{source_path} not found; run the earth_climate and earth_terrain steps first"
            )
    if output.exists():
        output.unlink()

    spec = config.grid
    started = time.perf_counter()
    with Dataset(terrain_path) as terrain, Dataset(climate_path) as climate:
        land_mask = climate.variables["land_mask"][:].astype(bool)
        land_fraction = climate.variables["land_fraction"][:].astype("float32")

        with GridStore(
            output,
            spec,
            mode="w",
            compression_level=config.storage.compression_level,
        ) as store:
            for definition in config.all_features:
                if definition.id in terrain.variables:
                    source = terrain.variables[definition.id]
                elif definition.id in climate.variables:
                    source = climate.variables[definition.id]
                else:
                    raise KeyError(
                        f"feature {definition.id!r} is configured but missing from both "
                        "intermediate stores"
                    )
                destination = store.create_feature(definition.id, {})
                _copy_attrs(source, destination)
                destination.setncattr("feature_group", definition.group)
                destination.setncattr("registry_function", definition.function)

                for row0 in range(0, spec.ny, spec.chunk_rows):
                    row1 = min(spec.ny, row0 + spec.chunk_rows)
                    values = source[row0:row1, :].astype("float32")
                    mask = land_mask[row0:row1, :]
                    values[~mask] = np.nan
                    destination[row0:row1, :] = values

            fraction_out = store.create_feature(
                "land_fraction",
                {
                    "long_name": "Fraction of WorldClim source cells that are land",
                    "units": "1",
                    "definition": (
                        "area average of the WorldClim ocean-nodata valid mask at the "
                        "search-grid resolution"
                    ),
                },
            )
            fraction_out[:] = land_fraction

            mask_out = store.create_feature(
                "land_mask",
                {
                    "long_name": "Earth land mask from WorldClim ocean nodata",
                    "units": "1",
                    "definition": (
                        "1 where land_fraction is at least the configured threshold, "
                        "0 for ocean; all features are NaN over ocean"
                    ),
                },
                fill_value=-1,
                dtype="i1",
            )
            mask_out[:] = land_mask.astype("i1")

            store.set_attrs(
                {
                    "title": "Earth analog features for Moon and Mars targets",
                    "phase": "Phase 1 (Earth grid)",
                    "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                    "grid": (
                        f"{spec.resolution_deg:g} degree lon/lat, {spec.nx} x {spec.ny} cells, "
                        "north-to-south rows, cell centres"
                    ),
                    "bounds": (
                        f"lon {spec.lon_min:g}..{spec.lon_max:g}, "
                        f"lat {spec.lat_min:g}..{spec.lat_max:g}"
                    ),
                    "feature_registry": "backend.features.registry (shared by Earth, Moon, Mars)",
                    "terrain_source": "ETOPO 2022 v1 60 arc-second surface elevation (NOAA NCEI)",
                    "terrain_doi": "10.25921/fd45-gt74",
                    "climate_source": (
                        "WorldClim 2.1 bioclimatic variables, 2.5 arc-minute "
                        "(Fick & Hijmans 2017)"
                    ),
                    "climate_doi": "10.1002/joc.5086",
                    "land_mask_rule": (
                        "WorldClim ocean nodata; land where valid fraction >= "
                        f"{config.earth.land_mask_threshold:g}"
                    ),
                    "terrain_method": (
                        f"{spec.tile_deg:g} degree tiles with a {spec.halo_deg:g} degree halo, "
                        f"local azimuthal-equidistant {spec.working_pixel_m / 1000:.2f} km grid; "
                        "relief/slope/roughness/Hurst computed in km windows; "
                        "ocean cells filled with nearest land elevation before filtering; "
                        "area-averaged to the search grid"
                    ),
                    "climate_method": "area average from 2.5 arc-minute",
                    "limitations": (
                        "WorldClim is air temperature, not surface skin temperature. Earth cannot "
                        "replicate reduced gravity, vacuum/thin atmosphere, or radiation. Terrain "
                        "windows are limited by the "
                        f"{config.earth.native_pixel_m / 1000:.2f} km ETOPO source. Search-grid "
                        "cells shrink in longitude toward the poles; feature values come from the "
                        f"local {spec.working_pixel_m / 1000:.2f} km working grid."
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
    label: str,
    cmap: str,
    extent: tuple[float, float, float, float],
    config: AppConfig,
) -> Any:
    """Draw one map panel with a robust colour range."""
    masked = np.ma.masked_invalid(values)
    finite = masked.compressed()
    if finite.size:
        vmin, vmax = (float(v) for v in np.percentile(finite, config.figures.percentile_stretch))
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
    axis.set_title(label, fontsize=9)
    axis.set_xticks(config.report.plot_xticks)
    axis.set_yticks(config.report.plot_yticks)
    axis.tick_params(labelsize=7)
    axis.grid(color="white", alpha=0.15, linewidth=0.3)
    return image


def write_figures(dataset_path: Path, config: AppConfig) -> list[Path]:
    """Write one quick-look PNG per feature plus a combined overview."""
    figures_dir = config.outputs.figures_dir
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    dataset = xr.open_dataset(dataset_path)
    stride = config.figures.stride_cells
    spec = config.grid
    extent = (spec.lon_min, spec.lon_max, spec.lat_min, spec.lat_max)
    prefix = config.outputs.figure_prefix

    for definition in config.all_features:
        values = dataset[definition.id].values[::stride, ::stride]
        figure, axis = plt.subplots(figsize=(14, 7), constrained_layout=True)
        image = _plot_panel(
            axis, values, definition.label, definition.cmap, extent, config
        )
        figure.colorbar(image, ax=axis, orientation="horizontal", pad=0.06, shrink=0.7)
        axis.set_xlabel("Longitude")
        axis.set_ylabel("Latitude")
        figure.suptitle(
            f"Earth analog feature: {definition.label}",
            fontsize=14,
            fontweight="bold",
        )
        figure.text(
            0.5,
            -0.02,
            "ETOPO 2022 + WorldClim 2.1 · land mask from WorldClim ocean nodata",
            ha="center",
            fontsize=8,
            color="0.35",
        )
        path = figures_dir / f"{prefix}{definition.id}.png"
        figure.savefig(path, dpi=config.figures.dpi_single, bbox_inches="tight")
        plt.close(figure)
        written.append(path)

    features = config.all_features
    columns = config.figures.overview_columns
    rows = max(1, int(np.ceil(len(features) / columns)))
    figure, axes = plt.subplots(rows, columns, figsize=(18, 3 * rows + 2), constrained_layout=True)
    flat = np.atleast_1d(axes).ravel()
    for axis, definition in zip(flat, features):
        _plot_panel(
            axis,
            dataset[definition.id].values[::stride, ::stride],
            definition.label,
            definition.cmap,
            extent,
            config,
        )
    for axis in flat[len(features):]:
        axis.axis("off")
    figure.suptitle(
        "Earth feature grid for Moon/Mars analog search",
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
    overview = figures_dir / config.outputs.overview_figure
    figure.savefig(overview, dpi=config.figures.dpi_overview, bbox_inches="tight")
    plt.close(figure)
    written.append(overview)
    dataset.close()
    return written


def _zone_stats(
    land_mask: np.ndarray,
    lat: np.ndarray,
    config: AppConfig,
    feature: np.ndarray | None = None,
) -> dict[str, Any]:
    """Compute cell-count and area-weighted coverage in polar/temperate zones."""
    ny, nx = land_mask.shape
    weights = np.cos(np.deg2rad(lat))[:, None] * np.ones((1, nx))
    polar = config.report.polar_circle_deg
    zones = {
        "grid": np.broadcast_to(np.ones((ny, 1), dtype=bool), land_mask.shape),
        f"arctic_ge_{polar:g}N": np.broadcast_to(lat[:, None] >= polar, land_mask.shape),
        "temperate": np.broadcast_to(
            (lat[:, None] > -polar) & (lat[:, None] < polar), land_mask.shape
        ),
        f"antarctic_le_{polar:g}S": np.broadcast_to(lat[:, None] <= -polar, land_mask.shape),
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


def sample_site(dataset, site: ValidationSite, config: AppConfig) -> dict[str, Any]:
    """Read every configured feature at one validation site.

    Sites outside the configured grid are reported as out of bounds instead of
    being silently clamped to the nearest edge cell.
    """
    spec = config.grid
    inside = (
        spec.lon_min <= site.lon <= spec.lon_max
        and spec.lat_min <= site.lat <= spec.lat_max
    )
    if not inside:
        return {
            "site": site.name,
            "lat": site.lat,
            "lon": site.lon,
            "row": None,
            "col": None,
            "inside_grid": False,
            "values": {definition.id: None for definition in config.all_features},
        }
    row, col = sample_point_rowcol(spec, site.lat, site.lon)
    values: dict[str, Any] = {}
    for definition in config.all_features:
        values[definition.id] = float(dataset[definition.id].values[row, col])
    return {
        "site": site.name,
        "lat": site.lat,
        "lon": site.lon,
        "row": row,
        "col": col,
        "inside_grid": True,
        "values": values,
    }


def write_report(
    dataset_path: Path,
    figures: list[Path],
    intermediates: list[Path],
    config: AppConfig,
    refresh_only: bool = False,
) -> dict[str, Any]:
    """Write the coverage/limits report and a machine-readable metadata file."""
    spec = config.grid
    report_path = config.output("earth_report")
    meta_path = config.output("earth_meta")
    dataset = xr.open_dataset(dataset_path)
    lat = dataset.lat.values
    lon = dataset.lon.values
    land_mask = dataset.land_mask.values.astype(bool)
    coverage = _zone_stats(land_mask, lat, config)
    global_run = (
        spec.lon_min <= -180.0
        and spec.lon_max >= 180.0
        and spec.lat_min <= -90.0
        and spec.lat_max >= 90.0
    )
    arctic_name = f"arctic_ge_{config.report.polar_circle_deg:g}N"
    antarctic_name = f"antarctic_le_{config.report.polar_circle_deg:g}S"
    reaches_arctic = coverage[arctic_name]["cells"] > 0
    reaches_antarctic = coverage[antarctic_name]["cells"] > 0

    feature_rows = []
    for definition in config.all_features:
        values = dataset[definition.id].values
        valid = np.isfinite(values) & land_mask
        feature_rows.append(
            {
                "name": definition.id,
                "group": definition.group,
                "function": definition.function,
                "units": definition.units,
                "long_name": definition.long_name,
                "min": float(np.nanmin(values[valid])) if valid.any() else float("nan"),
                "median": float(np.nanmedian(values[valid])) if valid.any() else float("nan"),
                "max": float(np.nanmax(values[valid])) if valid.any() else float("nan"),
                "valid_land_cells": int(valid.sum()),
                "valid_of_land": float(valid.sum() / max(1, land_mask.sum())),
            }
        )

    site_rows = [sample_site(dataset, site, config) for site in config.validation_sites]

    sizes = {
        path.name: path.stat().st_size / 1e6
        for path in [dataset_path, *intermediates]
        if path.exists()
    }
    metadata = {
        "grid": {
            "resolution_deg": spec.resolution_deg,
            "nx": spec.nx,
            "ny": spec.ny,
            "lon_min": spec.lon_min,
            "lon_max": spec.lon_max,
            "lat_min": spec.lat_min,
            "lat_max": spec.lat_max,
            "lat_order": "north_to_south",
            "tile_deg": spec.tile_deg,
            "halo_deg": spec.halo_deg,
            "working_pixel_m": spec.working_pixel_m,
        },
        "config": {
            "comparability": {
                "min_window_pixels": config.comparability.min_window_pixels,
                "min_hurst_lags": config.comparability.min_hurst_lags,
                "min_lag_pixels": config.comparability.min_lag_pixels,
                "exact_percentile_max_px": config.comparability.exact_percentile_max_px,
                "approx_percentile_window_px": config.comparability.approx_percentile_window_px,
            },
            "feature_ids": [definition.id for definition in config.all_features],
            "terrain_parameters": {
                definition.id: dict(definition.params)
                for definition in config.terrain_features
            },
            "groups": [
                {"name": group.name, "weight": group.weight, "members": list(group.members)}
                for group in config.groups
            ],
        },
        "sources": {
            "terrain": "ETOPO 2022 v1 60 arc-second surface elevation, NOAA NCEI, doi:10.25921/fd45-gt74",
            "climate": "WorldClim 2.1 bio layers, 2.5 arc-minute, Fick & Hijmans 2017, doi:10.1002/joc.5086",
        },
        "features": feature_rows,
        "coverage": coverage,
        "spot_checks": site_rows,
        "file_sizes_mb": sizes,
        "figures": [str(path.relative_to(PROJECT_ROOT).as_posix()) for path in figures],
        "limitations": [
            "WorldClim is air temperature (1970-2000 climatology), not surface skin temperature.",
            "WorldClim Antarctic values are interpolated from sparse stations; treat as weak evidence.",
            (
                f"ETOPO native sampling is {config.earth.native_pixel_m / 1000:.2f} km; search-grid "
                f"cells are ~{spec.resolution_deg * 111.32:.1f} km at the equator and much narrower "
                "in longitude near the poles."
            ),
            "Coastal terrain uses the nearest land elevation for ocean cells, so shelf bathymetry does not inflate relief.",
            "Earth cannot reproduce reduced gravity, vacuum/thin atmosphere, or radiation.",
            "Moon and Mars temperatures are literature values and are not part of this Earth grid.",
        ],
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    lines = [
        "# Earth feature grid — Phase 1 report",
        "",
        f"Generated by `python -m backend.pipeline.build_earth_features` on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        "## Grid",
        "",
        f"- **{spec.resolution_deg:g}° lon/lat** grid, {spec.nx} × {spec.ny} cells, "
        f"north-to-south rows, cell centres.",
        f"- Bounds: lon {spec.lon_min:g} → {spec.lon_max:g}, "
        f"lat {spec.lat_min:g} → {spec.lat_max:g}.",
        f"- Tiling: {spec.tile_deg:g}° tiles with a {spec.halo_deg:g}° halo, reprojected to a "
        f"local {spec.working_pixel_m / 1000:.2f} km azimuthal-equidistant grid; features "
        "computed in km windows by the shared registry; ocean cells filled with the nearest "
        "land elevation before filtering; sampled back with area averaging.",
        "- Climate: WorldClim 2.1 2.5 arc-minute (~4.6 km) area-averaged to the search grid; "
        "this is a slight coarsening, not added detail.",
        f"- Land mask: WorldClim ocean nodata; a cell is land when its valid fraction is at "
        f"least {config.earth.land_mask_threshold:g}. Every feature is NaN over ocean.",
        "",
        "## Features",
        "",
        "All twelve MVP features are computed by one registry "
        "(`backend/features/registry.py`) from parameters in `config/features.yaml`.",
        "",
        "| Variable | Group | Registry function | Units | Land min | Land median | Land max | Valid land cells |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in feature_rows:
        lines.append(
            f"| `{row['name']}` | {row['group']} | `{row['function']}` | {row['units']} | "
            f"{row['min']:.4g} | {row['median']:.4g} | {row['max']:.4g} | "
            f"{row['valid_land_cells']:,} ({100 * row['valid_of_land']:.1f}%) |"
        )
    lines.extend(["", "## Coverage", ""])
    lines.append("| Zone | Cells | Land cells | Land share of cells | Area-weighted land share |")
    lines.append("|---|---|---|---|---|")
    for zone, row in coverage.items():
        cell_share = (
            f"{100 * row['land_cell_fraction']:.1f}%"
            if row["cells"]
            else "n/a (outside grid)"
        )
        area_share = (
            f"{100 * row['land_area_fraction']:.1f}%"
            if row["cells"]
            else "n/a (outside grid)"
        )
        lines.append(
            f"| {zone} | {row['cells']:,} | {row['land_cells']:,} | "
            f"{cell_share} | {area_share} |"
        )
    lines.append("")
    if global_run:
        lines.append(
            "The area-weighted global land share should be close to Earth's ~29% land area; "
            "the cell-count share is higher because polar cells are over-represented in a "
            "lon/lat grid."
        )
    else:
        lines.append(
            "This is a regional proof run of the same pipeline; the shares describe the "
            "configured bounding box only, not the whole planet."
        )
    lines.extend(["", "## Polar coverage notes", ""])
    if reaches_antarctic:
        lines.extend(
            [
                "- **Antarctica** is present in the land mask (WorldClim has data over the ice "
                "sheet), so polar-desert sites are searchable. WorldClim Antarctic values come "
                "from sparse stations.",
            ]
        )
    else:
        lines.append(
            f"- The configured grid does not reach {config.report.polar_circle_deg:g}°S, so "
            "Antarctic coverage is not exercised by this run."
        )
    if reaches_arctic:
        lines.append(
            "- **Arctic** land is present, but ocean/ice-shelf cells are correctly excluded by "
            "the WorldClim nodata mask; this is a real coverage boundary, not missing data."
        )
    else:
        lines.append(
            f"- The configured grid does not reach {config.report.polar_circle_deg:g}°N, so "
            "Arctic coverage is not exercised by this run."
        )
    lines.append(
        "- At high latitude a search-grid cell is only a fraction of a kilometre wide in "
        "longitude; terrain features come from the local working grid, so adjacent polar cells "
        "repeat the same terrain sample. This is documented rather than hidden."
    )
    lines.extend(
        [
            "",
            "## Effective configuration",
            "",
            "These values come from `config/*.yaml`; nothing below is a code literal.",
            "",
            "| Feature | Group | Registry function | Parameters | Resolution on this body |",
            "|---|---|---|---|---|",
        ]
    )
    for definition in config.all_features:
        verdict = registry.availability(
            definition,
            spec.working_pixel_m,
            config.comparability,
            config.earth.native_pixel_m,
        )
        params = ", ".join(f"{key}={value}" for key, value in definition.params.items())
        status = verdict.resolution
        lines.append(
            f"| `{definition.id}` | {definition.group} | `{definition.function}` | "
            f"{params or '—'} | {status} |"
        )
    lines.extend(
        [
            "",
            "## Spot checks",
            "",
        ]
    )
    sample_ids = [d.id for d in config.all_features]
    header = "| Site | Lat | Lon | " + " | ".join(f"`{name}`" for name in sample_ids) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (3 + len(sample_ids)))
    for row in site_rows:
        if not row["inside_grid"]:
            cells = " | ".join("outside" for _ in sample_ids)
            lines.append(
                f"| {row['site']} | {row['lat']:.1f} | {row['lon']:.1f} | {cells} |"
            )
            continue
        cells = " | ".join(f"{row['values'][name]:.4g}" for name in sample_ids)
        lines.append(f"| {row['site']} | {row['lat']:.1f} | {row['lon']:.1f} | {cells} |")
    lines.append("")
    lines.append("Sites are defined in `config/validation_sites.yaml`, not in code.")
    lines.extend(["", "## Files and figures", ""])
    for name, size in sizes.items():
        note = " *(intermediate)*" if name != dataset_path.name else ""
        lines.append(f"- `{name}` — {size:.1f} MB{note}")
    lines.append(f"- `{meta_path.name}` — machine-readable metadata")
    for path in figures:
        lines.append(f"- `{path.relative_to(PROJECT_ROOT).as_posix()}`")
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "- WorldClim is **air temperature**, not surface skin temperature, and its Antarctic values are weakly constrained.",
            "- ETOPO includes bathymetry; the WorldClim land mask removes ocean cells, and ocean cells are filled with the nearest land elevation before filtering so coastal relief is not inflated by the shelf.",
            "- The lon/lat grid is not equal-area. At high latitudes, longitude cells are much narrower than at the equator; area weighting is reported above.",
            "- Earth cannot reproduce reduced gravity, vacuum or the thin Martian atmosphere, or the radiation environment.",
            "- Moon and Mars temperatures are literature values, added in Phase 2; no synthetic temperature raster is used.",
            "",
        ]
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    dataset.close()
    return metadata


def build(
    terrain_path: Path | None = None,
    climate_path: Path | None = None,
    output: Path | None = None,
    config: AppConfig | None = None,
    keep_intermediates: bool = False,
    refresh: bool = False,
) -> None:
    """Run the merge, figures and report (or just figures/report with ``refresh``)."""
    config = config or load_config()
    started = time.perf_counter()
    terrain_path = terrain_path or config.output("earth_terrain")
    climate_path = climate_path or config.output("earth_climate")
    output = output or config.output("earth_features")
    if refresh:
        if not output.exists():
            raise FileNotFoundError(f"{output} not found; cannot refresh figures")
        figures = write_figures(output, config)
        write_report(output, figures, [], config, refresh_only=True)
        print(f"Refreshed {len(figures)} figures for {output}")
        print(f"Wrote {config.output('earth_report')}")
        return

    merge_features(terrain_path, climate_path, output, config)
    figures = write_figures(output, config)
    intermediates = [] if keep_intermediates else [terrain_path, climate_path]
    write_report(output, figures, intermediates, config)
    if not keep_intermediates:
        for path in (terrain_path, climate_path):
            if path.exists():
                path.unlink()
    print(f"Wrote {output}")
    print(f"Wrote {config.output('earth_report')}")
    print(f"Wrote {len(figures)} figures to {config.outputs.figures_dir}")
    print(f"Total {time.perf_counter() - started:.1f} s")


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terrain", type=Path, default=None)
    parser.add_argument("--climate", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--keep-intermediates", action="store_true")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="regenerate figures and report from an existing features dataset",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="config override YAML deep-merged over config/*.yaml",
    )
    args = parser.parse_args()
    build(
        args.terrain,
        args.climate,
        args.output,
        config=load_config(override=args.config),
        keep_intermediates=args.keep_intermediates,
        refresh=args.refresh,
    )


if __name__ == "__main__":
    main()
