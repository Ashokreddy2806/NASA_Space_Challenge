"""Moon target profile: lunar south polar region poleward of the configured cap.

Everything here is driven by ``config/targets.yaml`` and the same feature
registry Earth uses. Terrain features are recomputed **from the 80 m LOLA DEM**
over the same physical windows and lags as Earth; the pre-computed LOLA roughness
/ Hurst / spectral-slope rasters are used only as a cross-check, never as the
primary values.

The region is a disc poleward of ``region.lat_min`` (85°S by default). The disc
radius in the DEM projection is computed from the DEM's own CRS, because PROJ
will not transform between Earth and the Moon.

Processing is block-wise with a halo wide enough for the largest configured
window, so features near block edges are computed from real neighbouring data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Iterator

import numpy as np
import rasterio
from rasterio.windows import Window

from backend.config import AppConfig, FeatureDefinition
from backend.features import registry
from backend.targets import thermal
from backend.targets.distribution import profile_entry
from backend.targets.geometry import polar_coordinates, polar_radius_m
from backend.targets.psr import load_psr_table, rasterize_psr


@dataclass(frozen=True)
class MoonGeometry:
    """Region geometry in DEM pixel coordinates."""

    row0: int
    row1: int
    col0: int
    col1: int
    pole: tuple[float, float]
    radius_m: float
    radius_px: float
    pixel_m: float
    shape: tuple[int, int]

    @property
    def window_shape(self) -> tuple[int, int]:
        return (self.row1 - self.row0, self.col1 - self.col0)


def _feature_reach_km(definitions: tuple[FeatureDefinition, ...]) -> float:
    """Largest physical support of any configured feature (window or lag)."""
    reach = 0.0
    for definition in definitions:
        if definition.window_km is not None:
            reach = max(reach, definition.window_km)
        for lag in definition.lags_km:
            reach = max(reach, lag)
    return reach


def region_geometry(config: AppConfig, dataset: rasterio.DatasetReader) -> MoonGeometry:
    """Pixel window and radius of the configured polar cap."""
    moon = config.targets["moon"]
    pixel_m = float(moon["working_pixel_m"])
    # The cap is everything poleward of the edge latitude stored in lat_max
    # (e.g. lat_min=-90, lat_max=-85 means "85°S to the pole").
    edge_lat = float(moon["region"]["lat_max"])
    pole = polar_coordinates(dataset.crs)
    radius_m = polar_radius_m(dataset.crs, edge_lat)
    radius_px = radius_m / pixel_m

    # Pixel position of the pole centre in the raster.
    transform = dataset.transform
    pole_col = (pole[0] - transform.c) / transform.a - 0.5
    pole_row = (pole[1] - transform.f) / transform.e - 0.5

    row0 = max(0, int(np.floor(pole_row - radius_px)))
    row1 = min(dataset.height, int(np.ceil(pole_row + radius_px)) + 1)
    col0 = max(0, int(np.floor(pole_col - radius_px)))
    col1 = min(dataset.width, int(np.ceil(pole_col + radius_px)) + 1)
    return MoonGeometry(
        row0=row0,
        row1=row1,
        col0=col0,
        col1=col1,
        pole=pole,
        radius_m=radius_m,
        radius_px=radius_px,
        pixel_m=pixel_m,
        shape=(dataset.height, dataset.width),
    )


def _blocks(
    geometry: MoonGeometry, core_px: int
) -> Iterator[tuple[tuple[int, int], tuple[int, int]]]:
    """Yield ((core_row0, core_row1), (core_col0, core_col1)) block bounds."""
    for row in range(geometry.row0, geometry.row1, core_px):
        for col in range(geometry.col0, geometry.col1, core_px):
            yield (
                (row, min(geometry.row1, row + core_px)),
                (col, min(geometry.col1, col + core_px)),
            )


def _decimated_pixel_rows(shape: tuple[int, int], pixel_m: float, cells: int) -> np.ndarray:
    """Map DEM pixel rows to a coarser (cross-check) row index."""
    rows = np.arange(shape[0])
    scaled = np.floor((rows + 0.5) * pixel_m / (pixel_m * shape[0] / cells)).astype(int)
    return np.clip(scaled, 0, cells - 1)


def _distance_window(
    geometry: MoonGeometry,
    transform: Any,
    row_slice: slice,
    col_slice: slice,
) -> np.ndarray:
    """Distance of each cell centre from the pole inside a window."""
    rows = np.arange(row_slice.start, row_slice.stop, dtype="float64")[:, None]
    cols = np.arange(col_slice.start, col_slice.stop, dtype="float64")[None, :]
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    return np.hypot(xs - geometry.pole[0], ys - geometry.pole[1])


def _collect_ice_proxy(
    config: AppConfig,
    dataset: rasterio.DatasetReader,
    geometry: MoonGeometry,
) -> tuple[dict[str, Any], np.ndarray]:
    """Rasterise PSR polygons over the region window and return the summary."""
    moon = config.targets["moon"]
    proxy = moon.get("ice_proxy") or {}
    if not proxy:
        return {"available": False, "reason": "no ice proxy configured"}, np.zeros(
            geometry.window_shape, dtype=bool
        )

    entries, table_info = load_psr_table(
        config.raw_source("moon", "psr"),
        float(proxy["min_polygon_area_km2"]),
    )
    transform = dataset.window_transform(
        Window(
            geometry.col0,
            geometry.row0,
            geometry.window_shape[1],
            geometry.window_shape[0],
        )
    )
    mask = rasterize_psr(entries, transform, geometry.window_shape)
    pixel_km2 = (geometry.pixel_m / 1000.0) ** 2

    region = _distance_window(
        geometry, dataset.transform, slice(geometry.row0, geometry.row1), slice(geometry.col0, geometry.col1)
    ) <= geometry.radius_m
    psr_in_region = mask & region
    region_km2 = float(region.sum() * pixel_km2)
    psr_km2 = float(psr_in_region.sum() * pixel_km2)

    in_region = [
        entry
        for entry in entries
        if np.isfinite(entry.max_radius()) and entry.max_radius() <= geometry.radius_m
    ]
    summary = {
        "available": True,
        "kind": proxy.get("kind", "psr_area_fraction"),
        "source_file": config.source_name("moon", "psr"),
        "units": "1",
        "value": float(psr_km2 / region_km2) if region_km2 else float("nan"),
        "region_area_km2": region_km2,
        "psr_area_km2": psr_km2,
        "min_polygon_area_km2": float(proxy["min_polygon_area_km2"]),
        "n_polygons_total": table_info["n_polygons"],
        "n_polygons_in_region": len(in_region),
        "psr_total_area_km2_in_table": table_info["total_area_km2"],
        "note": (
            "area fraction of rasterised permanently shadowed regions inside the "
            "target disc; this is the cold-trap/ice proxy, not a water-ice measurement"
        ),
    }
    return summary, psr_in_region


def _cross_check(
    config: AppConfig,
    dataset: rasterio.DatasetReader,
    geometry: MoonGeometry,
    accumulators: dict[str, np.ndarray],
    counts: np.ndarray,
) -> dict[str, Any]:
    """Correlate recomputed features with the pre-computed LOLA products."""
    moon = config.targets["moon"]
    pairs = moon.get("cross_check_products", {})
    cells = counts.shape

    # Distance at the coarse grid centres.
    coarse_rows = np.arange(cells[0], dtype="float64")[:, None]
    coarse_cols = np.arange(cells[1], dtype="float64")[None, :]
    coarse_size = dataset.transform.a * dataset.width / cells[1]
    xs = dataset.bounds.left + (coarse_cols + 0.5) * coarse_size
    ys = dataset.bounds.top - (coarse_rows + 0.5) * coarse_size
    coarse_region = np.hypot(xs - geometry.pole[0], ys - geometry.pole[1]) <= geometry.radius_m

    results: dict[str, Any] = {}
    for feature_id, source_key in pairs.items():
        sums = accumulators.get(feature_id)
        if sums is None:
            continue
        path = config.raw_source("moon", source_key)
        if not path.exists():
            results[feature_id] = {
                "source": config.source_name("moon", source_key),
                "available": False,
                "reason": f"{path} is not on disk",
            }
            continue
        mean = np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)
        with rasterio.open(path) as reference:
            reference_values = reference.read(1, masked=True).astype("float32")
            reference_values = np.ma.filled(reference_values, np.nan)
        if reference_values.shape != cells:
            reference_values = np.resize(reference_values, cells)
        both = (
            np.isfinite(mean)
            & np.isfinite(reference_values)
            & coarse_region
        )
        n = int(both.sum())
        if n < 10:
            results[feature_id] = {
                "source": config.source_name("moon", source_key),
                "available": False,
                "reason": f"only {n} overlapping cells",
            }
            continue
        a = mean[both].astype("float64")
        b = reference_values[both].astype("float64")
        correlation = float(np.corrcoef(a, b)[0, 1])
        difference = a - b
        results[feature_id] = {
            "source": config.source_name("moon", source_key),
            "available": True,
            "n": n,
            "pearson_r": correlation,
            "median_difference": float(np.median(difference)),
            "median_abs_difference": float(np.median(np.abs(difference))),
            "our_median": float(np.median(a)),
            "our_p16": float(np.percentile(a, 16)),
            "our_p84": float(np.percentile(a, 84)),
            "reference_median": float(np.median(b)),
            "reference_p05": float(np.percentile(b, 5)),
            "reference_p95": float(np.percentile(b, 95)),
            "role": "cross-check only; the profile value above is recomputed from the 80 m DEM",
        }
    return results


def analyse_moon(config: AppConfig | None = None) -> dict[str, Any]:
    """Build the Moon target profile: feature distributions plus ice proxy."""
    config = config or load_config_safe()
    moon = config.targets["moon"]
    dem_path = config.raw_source("moon", "dem")
    pixel_m = float(moon["working_pixel_m"])
    native_pixel_m = float(moon["native_pixel_m"])
    started = time.perf_counter()

    stride = int(config.distribution.sample_stride_px)
    core_px = int(moon["block_core_px"])
    halo_km = _feature_reach_km(config.terrain_features) + float(
        moon["halo_margin_km"]
    )
    halo_px = int(np.ceil(halo_km * 1000.0 / pixel_m))

    samples: dict[str, list[np.ndarray]] = {}
    profile_ids = {definition.id for definition in config.terrain_features}
    status: dict[str, registry.Availability] = {}
    region_cells = 0
    sampled_cells = 0

    with rasterio.open(dem_path) as dataset:
        geometry = region_geometry(config, dataset)
        ice_proxy, psr_mask = _collect_ice_proxy(config, dataset, geometry)

        cross_cells = int(moon["cross_check_cells"])
        accumulators = {
            feature_id: np.zeros((cross_cells, cross_cells), dtype="float64")
            for feature_id in (moon.get("cross_check_products") or {})
        }
        counts = np.zeros((cross_cells, cross_cells), dtype=np.int32)
        coarse_rows = _decimated_pixel_rows(
            (dataset.height, dataset.width), pixel_m, cross_cells
        )

        block_count = 0
        for (core_r0, core_r1), (core_c0, core_c1) in _blocks(geometry, core_px):
            pad_r0 = max(0, core_r0 - halo_px)
            pad_r1 = min(dataset.height, core_r1 + halo_px)
            pad_c0 = max(0, core_c0 - halo_px)
            pad_c1 = min(dataset.width, core_c1 + halo_px)
            window = Window(pad_c0, pad_r0, pad_c1 - pad_c0, pad_r1 - pad_r0)
            dem = dataset.read(1, window=window, masked=True).astype("float32")
            dem = np.ma.filled(dem, np.nan)

            features, block_status = registry.compute_all(
                config.terrain_features,
                dem,
                pixel_m,
                config.comparability,
                native_pixel_m=native_pixel_m,
            )
            for feature_id, verdict in block_status.items():
                status.setdefault(feature_id, verdict)

            baseline_km = moon.get("cross_check_baseline_km")
            slope_baseline_km = moon.get("cross_check_slope_baseline_km")
            cross_products = moon.get("cross_check_products") or {}
            if baseline_km is not None or slope_baseline_km is not None:
                prepared = registry.prepare_dem(dem)
                if baseline_km is not None and "roughness_800m_baseline" in cross_products:
                    features["roughness_800m_baseline"] = registry.roughness(
                        prepared,
                        pixel_m,
                        {
                            "window_km": float(baseline_km),
                            "sigma_fraction": 0.5,
                        },
                        config.comparability,
                    )
                if (
                    slope_baseline_km is not None
                    and "slope_1600m_baseline" in cross_products
                ):
                    features["slope_1600m_baseline"] = registry.slope(
                        prepared,
                        pixel_m,
                        {"window_km": float(slope_baseline_km)},
                        config.comparability,
                    )

            core_distance = _distance_window(
                geometry,
                dataset.transform,
                slice(core_r0, core_r1),
                slice(core_c0, core_c1),
            )
            inside = core_distance <= geometry.radius_m
            region_cells += int(inside.sum())

            offset_r = core_r0 - pad_r0
            offset_c = core_c0 - pad_c0
            local = (
                slice(offset_r, offset_r + (core_r1 - core_r0)),
                slice(offset_c, offset_c + (core_c1 - core_c0)),
            )

            for feature_id, array in features.items():
                if feature_id not in profile_ids:
                    continue  # cross-check-only products are not profile entries
                core = array[local]
                sampled = core[::stride, ::stride]
                sampled_mask = inside[::stride, ::stride]
                samples.setdefault(feature_id, []).append(sampled[sampled_mask])

            # Coarse accumulation is updated once per block and pixel, so the
            # denominator is not multiplied by the number of cross-check features.
            rows = np.arange(core_r0, core_r1)
            cols = np.arange(core_c0, core_c1)
            coarse_r = coarse_rows[rows]
            coarse_c = np.clip(
                np.floor((cols + 0.5) * pixel_m / (pixel_m * dataset.height / cross_cells)).astype(int),
                0,
                cross_cells - 1,
            )
            np.add.at(
                counts,
                (coarse_r[:, None], coarse_c[None, :]),
                inside.astype(np.int32),
            )
            for feature_id in accumulators:
                if feature_id not in features:
                    continue
                core = features[feature_id][local]
                np.add.at(
                    accumulators[feature_id],
                    (coarse_r[:, None], coarse_c[None, :]),
                    np.nan_to_num(np.where(inside, core, 0.0), nan=0.0),
                )

            sampled_cells += int(inside[::stride, ::stride].sum())
            block_count += 1
            if block_count % 4 == 0:
                print(
                    f"  moon: {block_count} blocks, "
                    f"{time.perf_counter() - started:.1f} s"
                )

        cross_check = _cross_check(
            config, dataset, geometry, accumulators, counts
        )

    entries: dict[str, Any] = {}
    for definition in config.terrain_features:
        verdict = status.get(
            definition.id,
            registry.availability(
                definition, pixel_m, config.comparability, native_pixel_m
            ),
        )
        if not verdict.available:
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
        values = (
            np.concatenate(samples[definition.id])
            if samples.get(definition.id)
            else np.array([], dtype="float32")
        )
        entries[definition.id] = profile_entry(
            definition,
            values,
            verdict,
            n_cells=region_cells,
            sampled=values.size < region_cells,
            percentiles=config.distribution.percentiles,
        )
    for feature_id, verdict in status.items():
        if not verdict.available and feature_id not in entries:
            entries[feature_id] = {
                "resolution": "unavailable",
                "resolution_note": verdict.reason,
            }

    table = thermal.thermal_availability(config, "moon")
    thermal_entries = thermal.match_thermal_features(config, table, moon)
    entries.update(thermal_entries)
    definitions = {definition.id: definition for definition in config.all_features}
    for feature_id in moon.get("unavailable_features") or []:
        definition = definitions.get(feature_id)
        if definition is None:
            raise KeyError(
                f"targets.yaml moon.unavailable_features lists unknown feature {feature_id}"
            )
        entries[feature_id] = {
            "units": definition.units,
            "long_name": definition.long_name,
            "group": definition.group,
            "registry_function": definition.function,
            "resolution": "unavailable",
            "resolution_note": str(
                (moon.get("not_applicable") or {}).get(
                    feature_id, "excluded by target configuration"
                )
            ),
            "n_cells": 0,
            "median": float("nan"),
        }

    return {
        "body": "moon",
        "label": moon["label"],
        "source": {
            "dem": config.source_name("moon", "dem"),
            "pixel_m": pixel_m,
            "native_pixel_m": native_pixel_m,
            "crs": "LDEM south polar stereographic (Moon sphere)",
        },
        "extent": {
            "lat_min": float(moon["region"]["lat_min"]),
            "lat_max": float(moon["region"]["lat_max"]),
            "radius_km": geometry.radius_m / 1000.0,
            "radius_px": geometry.radius_px,
            "region_pixels_full": region_cells,
            "region_area_km2": float(
                region_cells * (pixel_m / 1000.0) ** 2
            ),
            "sampled_pixels": sampled_cells,
            "sample_stride_px": stride,
            "blocks": block_count,
            "halo_km": halo_km,
            "halo_px": halo_px,
        },
        "features": entries,
        "ice_proxy": ice_proxy,
        "cross_check": cross_check,
        "thermal": {
            "available": table["available"],
            "path": table["path"],
            "reason": table["reason"],
            "schema": table.get("schema"),
            "entries": table["table"],
            "references": table.get("references", []),
            "derived": table.get("derived", []),
        },
        "runtime_seconds": time.perf_counter() - started,
    }


def load_config_safe() -> AppConfig:
    """Local import wrapper so the module stays importable without a config."""
    from backend.config import load_config

    return load_config()
