"""Phase 3 build: global score maps, top sites, validation and sensitivity.

Run from ``NASA_Space_Challenge/``::

    python -m backend.engine.build_scores

Writes:

* ``data/processed/scores_moon.nc`` / ``scores_mars.nc`` — per-group and
  per-preset score grids on the 0.05° Earth grid
* ``data/processed/top_sites.json`` — sites with/without famous analogs,
  validation-site scores, per-feature rank/absolute evidence, sensitivity
* ``docs/phase3_report.md`` — the human-readable Phase 3 report

Weights, presets, normalization, top-N, separation, famous sites and the
qualitative thermal bands all come from ``config/*.yaml``.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from typing import Any

import numpy as np
from netCDF4 import Dataset

from backend.config import AppConfig, Preset, load_config
from backend.engine import similarity, top_sites
from backend.paths import PROJECT_ROOT

TARGETS = ("moon", "mars")
PRESET_ORDER = ("balanced", "rover_mobility", "cold_trap_ice", "thermal_cycling")


def _sanitise(value: Any) -> Any:
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _sanitise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitise(item) for item in value]
    return value


def _preset(config: AppConfig, name: str) -> Preset:
    for preset in config.presets:
        if preset.name == name:
            return preset
    raise KeyError(f"unknown preset {name}")


def create_score_file(
    config: AppConfig,
    store: similarity.EarthStore,
    target: str,
    groups: dict[str, np.ndarray],
) -> Dataset:
    """Open a score NetCDF and define every variable up front."""
    path = config.output(f"scores_{target}")
    path.parent.mkdir(parents=True, exist_ok=True)
    dataset = Dataset(str(path), "w", format="NETCDF4")
    dataset.createDimension("lat", store.lat.size)
    dataset.createDimension("lon", store.lon.size)
    lat = dataset.createVariable("lat", "f8", ("lat",))
    lat[:] = store.lat
    lat.units = "degrees_north"
    lon = dataset.createVariable("lon", "f8", ("lon",))
    lon[:] = store.lon
    lon.units = "degrees_east"
    chunks = (config.grid.chunk_rows, config.grid.chunk_cols)
    for name in groups:
        variable = dataset.createVariable(
            f"group_{name}",
            "f4",
            ("lat", "lon"),
            zlib=True,
            complevel=config.storage.compression_level,
            shuffle=True,
            chunksizes=chunks,
            fill_value=np.float32(np.nan),
        )
        variable.long_name = f"Area-weighted similarity for group {name}"
    for preset in config.presets:
        variable = dataset.createVariable(
            f"score_{preset.name}",
            "f4",
            ("lat", "lon"),
            zlib=True,
            complevel=config.storage.compression_level,
            shuffle=True,
            chunksizes=chunks,
            fill_value=np.float32(np.nan),
        )
        variable.long_name = f"Preset score: {preset.label}"
    coverage = dataset.createVariable(
        "coverage",
        "f4",
        ("lat", "lon"),
        zlib=True,
        complevel=config.storage.compression_level,
        shuffle=True,
        chunksizes=chunks,
        fill_value=np.float32(np.nan),
    )
    coverage.long_name = "Fraction of preset weight with a finite group score"
    dataset.title = f"Earth analog scores for the {target} target"
    dataset.phase = "Phase 3 (similarity engine)"
    dataset.target = target
    dataset.grid = "0.05 degree lon/lat, 7200 x 3600 cells, north-to-south rows"
    dataset.area_weighting = "cos(latitude); count area, not cells"
    dataset.presets = ",".join(preset.name for preset in config.presets)
    return dataset


def feature_site_rows(
    config: AppConfig,
    store: similarity.EarthStore,
    profile: dict[str, Any],
    tables: dict[str, tuple[np.ndarray, np.ndarray]],
    lat_deg: float,
    lon_deg: float,
    radius_km: float,
) -> list[dict[str, Any]]:
    """Per-feature absolute gap, rank similarity and hidden-gap flag at a point."""
    rows: list[dict[str, Any]] = []
    for feature_id, table in tables.items():
        entry = (profile.get("features") or {}).get(feature_id) or {}
        if entry.get("resolution") == "qualitative":
            values = store.window(feature_id, lat_deg, lon_deg, radius_km / 110.574)
            valid = np.isfinite(values)
            mean_value = float(values[valid].mean()) if valid.any() else float("nan")
            bands = np.asarray(entry["bands_c"], dtype=float)
            band = int(np.searchsorted(bands, mean_value, side="right"))
            n_bands = int(entry["n_bands"])
            target_band = int(entry["target_band"])
            lo, hi = (float(v) for v in entry["anchor_range_c"])
            if mean_value < lo:
                gap_c = mean_value - lo
            elif mean_value > hi:
                gap_c = mean_value - hi
            else:
                gap_c = 0.0
            rows.append(
                {
                    "feature": feature_id,
                    "group": entry["group"],
                    "qualitative": True,
                    "label": "qualitative",
                    "value": mean_value,
                    "units": entry["units"],
                    "band": band,
                    "target_band": target_band,
                    "band_similarity": 1.0
                    - abs(band - target_band) / max(n_bands - 1, 1),
                    "anchor_range_c": entry["anchor_range_c"],
                    "absolute_gap": gap_c,
                    "absolute_gap_note": (
                        "gap to the cited anchor range in °C; a qualitative "
                        "comparison, not a measurement of the same quantity"
                    ),
                    "anchor_label": entry.get("anchor_label", ""),
                }
            )
            continue
        if entry.get("resolution") not in {"resolved", "marginal"}:
            continue
        values = store.window(feature_id, lat_deg, lon_deg, radius_km / 110.574)
        valid = np.isfinite(values)
        if not valid.any():
            continue
        value = float(values[valid].mean())
        median = float(entry["median"])
        p16 = entry.get("p16")
        p84 = entry.get("p84")
        sigma = (float(p84) - float(p16)) / 2.0 if p16 is not None else float("nan")
        floor = max(
            abs(median) * config.scoring.spread_floor_fraction,
            float(config.scoring.spread_floor_units.get(feature_id, 0.0)),
        )
        scale = max(sigma, floor) if math.isfinite(sigma) else floor
        gap = value - median
        absolute = float(
            math.exp(-0.5 * (gap / scale) ** 2)
            if config.scoring.absolute_kernel == "gaussian"
            else math.exp(-abs(gap / scale))
        )
        earth_percentile = float(np.interp(value, table[1], table[0]))
        q = float(np.interp(median, table[1], table[0]))
        rank_similarity = 1.0 - abs(earth_percentile - q)
        hidden = (
            rank_similarity >= config.scoring.hidden_gap_rank_similarity
            and absolute <= config.scoring.hidden_gap_absolute_similarity
        )
        rows.append(
            {
                "feature": feature_id,
                "group": entry["group"],
                "qualitative": False,
                "value": value,
                "units": entry["units"],
                "target_median": median,
                "absolute_gap": gap,
                "target_spreads": gap / scale if scale else float("nan"),
                "absolute_similarity": absolute,
                "earth_percentile": earth_percentile,
                "target_percentile": q,
                "rank_similarity": rank_similarity,
                "hidden_real_unit_gap": bool(hidden),
                "note": (
                    "rank similarity looks good but the real-unit gap is large"
                    if hidden
                    else ""
                ),
            }
        )
    return rows


def score_percentile_table(
    config: AppConfig, score: np.ndarray, store: similarity.EarthStore
) -> tuple[np.ndarray, np.ndarray]:
    valid = store.land & np.isfinite(score)
    return similarity.weighted_cdf_table(
        score[valid].astype(np.float64),
        store.cell_weight[valid],
        config.scoring.cdf_quantiles,
    )


def build_site_list(
    config: AppConfig,
    store: similarity.EarthStore,
    profile: dict[str, Any],
    tables: dict[str, tuple[np.ndarray, np.ndarray]],
    score: np.ndarray,
    groups: dict[str, np.ndarray],
    preset: Preset,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """NMS sites, then the same list filtered to exclude famous analogs."""
    separation = preset.min_separation_km
    candidates = top_sites.select_sites(
        score, store.lat, store.lon, separation, max_sites=preset.top_n * 8
    )
    enriched: list[dict[str, Any]] = []
    for candidate in candidates:
        site = top_sites.site_aggregate(
            config,
            score,
            groups,
            store.lat,
            store.lon,
            candidate,
            store.land,
            separation,
        )
        famous, famous_name = top_sites.is_famous(
            config, site["lat"], site["lon"]
        )
        site["famous"] = famous
        site["famous_name"] = famous_name
        enriched.append(site)
    enriched.sort(key=lambda entry: entry["site_score"], reverse=True)
    top = enriched[: preset.top_n]
    without_famous = [site for site in enriched if not site["famous"]][
        : preset.top_n
    ]
    # Per-feature evidence is only needed for the sites that are reported.
    reported = {id(site): site for site in top}
    reported.update({id(site): site for site in without_famous})
    for site in reported.values():
        site["features"] = feature_site_rows(
            config,
            store,
            profile,
            tables,
            site["lat"],
            site["lon"],
            site["aggregation_radius_km"],
        )
    return top, without_famous


def validate_sites(
    config: AppConfig,
    store: similarity.EarthStore,
    profile: dict[str, Any],
    tables: dict[str, tuple[np.ndarray, np.ndarray]],
    score: np.ndarray,
    percentile_table: tuple[np.ndarray, np.ndarray],
    target: str,
) -> list[dict[str, Any]]:
    """Score the configured spot checks and proposed analogs on this target."""
    rows: list[dict[str, Any]] = []
    for site in list(config.validation_sites) + list(config.analogs):
        if site.targets and target not in site.targets:
            continue
        row, col = top_sites.nearest_cell(
            store.lat, store.lon, site.lat, site.lon
        )
        value = float(score[row, col])
        percentile = float(np.interp(value, percentile_table[1], percentile_table[0]))
        rows.append(
            {
                "name": site.name,
                "lat": float(store.lat[row]),
                "lon": float(store.lon[col]),
                "requested_lat": site.lat,
                "requested_lon": site.lon,
                "score": value,
                "land_percentile": percentile,
                "notes": site.notes,
                "source": site.source,
                "reviewed": site.reviewed,
                "features": feature_site_rows(
                    config,
                    store,
                    profile,
                    tables,
                    float(store.lat[row]),
                    float(store.lon[col]),
                    config.grid.resolution_deg,
                ),
            }
        )
    return rows


def _rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="stable")
    ranks = np.empty(values.size, dtype=np.float64)
    ranks[order] = np.arange(values.size, dtype=np.float64)
    return ranks


def thermal_sensitivity(
    config: AppConfig,
    store: similarity.EarthStore,
    target: str,
    profile: dict[str, Any],
    groups: dict[str, np.ndarray],
    baseline_score: np.ndarray,
    baseline_sites: list[dict[str, Any]],
) -> dict[str, Any]:
    """Vary band edges and temperature weight; report top-N overlap and rho."""
    scales = similarity.scaled_features(config, profile)
    qualitative = [f for f in scales.values() if f.qualitative]
    if not qualitative:
        return {
            "applicable": False,
            "reason": "no qualitative thermal features for this target",
        }
    settings = config.thermal_sensitivity
    baseline_names = {(round(s["lat"], 6), round(s["lon"], 6)) for s in baseline_sites}
    base_weights = dict(_preset(config, "balanced").weights)
    others = {name: grid for name, grid in groups.items() if name != "temperature"}
    rng = np.random.default_rng(settings.random_seed)
    land_indices = np.flatnonzero(store.land)
    sample = rng.choice(
        land_indices,
        size=min(settings.rank_sample_count, land_indices.size),
        replace=False,
    )
    sample = sample[np.isfinite(baseline_score.ravel()[sample])]
    variants: list[dict[str, Any]] = []
    for shift in settings.band_edge_shifts_c:
        temperature_sum = np.zeros(store.shape, dtype=np.float32)
        count = np.zeros(store.shape, dtype=np.uint8)
        for feature in qualitative:
            values = store.read(feature.id)
            valid = store.land & np.isfinite(values)
            shifted = similarity.ScaledFeature(
                id=feature.id,
                group=feature.group,
                units=feature.units,
                qualitative=True,
                bands_c=tuple(float(edge) + shift for edge in feature.bands_c),
                n_bands=feature.n_bands,
                target_band=feature.target_band,
                anchor_lo=feature.anchor_lo,
                anchor_hi=feature.anchor_hi,
            )
            similarity_grid = similarity.band_similarity(values, shifted)
            temperature_sum[valid] += similarity_grid[valid]
            count[valid] += 1
        temperature = np.full(store.shape, np.nan, dtype=np.float32)
        has = count > 0
        temperature[has] = temperature_sum[has] / count[has]
        for weight in settings.temperature_weights:
            weights = dict(base_weights)
            weights["temperature"] = weight
            grid_map = dict(others)
            if weight > 0:
                grid_map["temperature"] = temperature
            score, _ = similarity.preset_score(config, target, grid_map, weights)
            sites = top_sites.select_sites(
                score,
                store.lat,
                store.lon,
                _preset(config, "balanced").min_separation_km,
                settings.top_n,
            )
            names = {(round(s["lat"], 6), round(s["lon"], 6)) for s in sites}
            overlap = len(names & baseline_names)
            values = score.ravel()[sample]
            if np.isfinite(values).sum() > 2:
                rho = float(
                    np.corrcoef(
                        _rank(values), _rank(baseline_score.ravel()[sample])
                    )[0, 1]
                )
            else:
                rho = float("nan")
            variants.append(
                {
                    "temperature_weight": weight,
                    "band_edge_shift_c": shift,
                    "top_n_overlap_with_baseline": overlap,
                    "top_n_overlap_fraction": overlap / max(len(baseline_names), 1),
                    "spearman_rho_vs_baseline": rho,
                    "n_sites": len(sites),
                }
            )
    finite_rho = [v["spearman_rho_vs_baseline"] for v in variants if math.isfinite(v["spearman_rho_vs_baseline"])]
    min_overlap = min(v["top_n_overlap_fraction"] for v in variants)
    min_rho = min(finite_rho) if finite_rho else float("nan")
    verdict = (
        "rankings are stable enough to read the thermal dimension as a tie-breaker"
        if min_overlap >= 0.6 and min_rho >= 0.95
        else "rankings change materially when the thermal settings change; treat the "
        "thermal contribution as weak evidence, not a ranking driver"
    )
    return {
        "applicable": True,
        "baseline": {
            "temperature_weight": base_weights.get("temperature", 0.25),
            "band_edge_shift_c": 0.0,
            "top_n": len(baseline_names),
        },
        "variants": variants,
        "min_top_n_overlap_fraction": min_overlap,
        "min_spearman_rho": min_rho,
        "verdict": verdict,
    }


def build(config: AppConfig | None = None) -> dict[str, Any]:
    config = config or load_config()
    started = time.perf_counter()
    created_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    profiles = json.loads(
        config.output("target_profiles").read_text(encoding="utf-8")
    )
    store = similarity.EarthStore(config)
    print(
        f"Earth grid {store.shape[0]}x{store.shape[1]}, "
        f"{store.land.sum():,} land cells"
    )

    print("Group scores …")
    group_scores, diagnostics, tables = similarity.compute_group_scores(
        config, profiles, store
    )
    print(f"  groups done in {time.perf_counter() - started:.1f} s")

    payload: dict[str, Any] = {
        "created_utc": created_utc,
        "config": {
            "scoring": {
                "absolute_kernel": config.scoring.absolute_kernel,
                "spread_floor_fraction": config.scoring.spread_floor_fraction,
                "hidden_gap_rank_similarity": config.scoring.hidden_gap_rank_similarity,
                "hidden_gap_absolute_similarity": config.scoring.hidden_gap_absolute_similarity,
                "area_weighting": config.scoring.area_weighting,
                "cdf_quantiles": config.scoring.cdf_quantiles,
                "site_aggregation_fraction_of_separation": (
                    config.scoring.site_aggregation_fraction_of_separation
                ),
            },
            "presets": {
                preset.name: {
                    "label": preset.label,
                    "weights": dict(preset.weights),
                    "top_n": preset.top_n,
                    "min_separation_km": preset.min_separation_km,
                }
                for preset in config.presets
            },
            "famous_radius_km": config.famous_radius_km,
            "thermal_sensitivity": {
                "temperature_weights": list(
                    config.thermal_sensitivity.temperature_weights
                ),
                "band_edge_shifts_c": list(
                    config.thermal_sensitivity.band_edge_shifts_c
                ),
                "top_n": config.thermal_sensitivity.top_n,
            },
        },
        "targets": {},
    }

    for target in TARGETS:
        print(f"{target} …")
        target_payload: dict[str, Any] = {
            "features_used": sorted(diagnostics[target]),
            "feature_evidence": {
                feature_id: diag.as_dict()
                for feature_id, diag in diagnostics[target].items()
            },
            "profiles_created_utc": profiles.get("created_utc"),
            "presets": {},
        }
        groups = group_scores[target]
        dataset = create_score_file(config, store, target, groups)
        sensitivity: dict[str, Any] = {
            "applicable": False,
            "reason": "balanced preset was not evaluated",
        }
        for name, grid in groups.items():
            dataset.variables[f"group_{name}"][:] = grid
        coverage_grid = np.zeros(store.shape, dtype=np.float32)
        # Two presets can collapse to the same ranking for a target when one has
        # no usable feature (Mars has no thermal/dryness data). Detect it so the
        # report does not present identical lists as independent evidence.
        signatures: dict[tuple[Any, ...], str] = {}
        equivalents: dict[str, str | None] = {}
        for preset in config.presets:
            usable = {
                key: value
                for key, value in preset.weights.items()
                if value > 0 and key in groups
            }
            total = sum(usable.values()) or 1.0
            signature = tuple(
                sorted((key, round(value / total, 8)) for key, value in usable.items())
            )
            equivalents[preset.name] = signatures.get(signature)
            signatures.setdefault(signature, preset.name)
        for preset in config.presets:
            order = [p.name for p in config.presets].index(preset.name)
            score, weighting = similarity.preset_score(
                config, target, groups, dict(preset.weights)
            )
            dataset.variables[f"score_{preset.name}"][:] = score
            if order == 0:
                positive = {k: v for k, v in preset.weights.items() if v > 0}
                denominator = sum(positive.values())
                covered = sum(
                    value for key, value in positive.items() if key in groups
                )
                coverage_grid[:] = covered / denominator
                dataset.variables["coverage"][:] = coverage_grid
            finite = np.isfinite(score)
            weights = store.cell_weight[store.land]
            finite_land = finite[store.land]
            mean = (
                float(
                    (score[store.land][finite_land] * weights[finite_land]).sum()
                    / weights[finite_land].sum()
                )
                if finite_land.any()
                else float("nan")
            )
            sites, without_famous = build_site_list(
                config, store, profiles[target], tables[target], score, groups, preset
            )
            percentile_table = score_percentile_table(config, score, store)
            validation = validate_sites(
                config,
                store,
                profiles[target],
                tables[target],
                score,
                percentile_table,
                target,
            )
            target_payload["presets"][preset.name] = {
                "label": preset.label,
                "weights": dict(preset.weights),
                "weighting": weighting,
                "weight_share": {
                    key: value / (weighting["weight_sum"] or 1.0)
                    for key, value in weighting["weights_used"].items()
                },
                "weight_coverage": weighting["weight_sum"]
                / (sum(preset.weights.values()) or 1.0),
                "dominant_group": max(
                    weighting["weights_used"],
                    key=weighting["weights_used"].get,
                    default="",
                ),
                "equivalent_to": equivalents[preset.name],
                "top_n": preset.top_n,
                "min_separation_km": preset.min_separation_km,
                "coverage": similarity.score_coverage(config, score, store),
                "score_stats": {
                    "land_area_weighted_mean": mean,
                    "land_area_weighted_p50": float(
                        np.interp(0.5, percentile_table[0], percentile_table[1])
                    ),
                    "land_area_weighted_p95": float(
                        np.interp(0.95, percentile_table[0], percentile_table[1])
                    ),
                },
                "sites": sites,
                "sites_excluding_famous": without_famous,
                "validation": validation,
            }
            print(
                f"  {target}/{preset.name}: coverage "
                f"{similarity.score_coverage(config, score, store):.4f}, "
                f"{len(sites)} sites"
            )
            if preset.name == "balanced":
                sensitivity = thermal_sensitivity(
                    config,
                    store,
                    target,
                    profiles[target],
                    groups,
                    score,
                    sites,
                )
        dataset.close()
        target_payload["thermal_sensitivity"] = sensitivity
        target_payload["coverage"] = {
            "features_used": len(diagnostics[target]),
            "features_configured": len(config.all_features),
            "feature_fraction": len(diagnostics[target]) / len(config.all_features),
            "groups_scored": len(groups),
            "groups_configured": len(config.groups),
            "group_fraction": len(groups) / len(config.groups),
            "earth_land_area_fraction": max(
                preset_payload["coverage"]
                for preset_payload in target_payload["presets"].values()
            ),
        }
        payload["targets"][target] = target_payload

    store.close()
    payload["total_runtime_seconds"] = time.perf_counter() - started
    json_path = config.output("top_sites")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(_sanitise(payload), indent=2, allow_nan=False), encoding="utf-8"
    )
    report_path = write_phase3_report(config, payload)
    print(f"Wrote {json_path}")
    print(f"Wrote {report_path}")
    print(f"Total {payload['total_runtime_seconds']:.1f} s")
    return payload


def _pct(value: Any) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "—"


def _num(value: Any, digits: int = 3) -> str:
    return f"{value:.{digits}g}" if isinstance(value, (int, float)) else "—"


def _largest_gap(row: dict[str, Any]) -> str:
    """The numeric feature furthest from the target, in real units."""
    best: tuple[float, dict[str, Any]] | None = None
    for feature in row.get("features", []):
        if feature.get("qualitative"):
            continue
        spread = feature.get("target_spreads")
        gap = feature.get("absolute_gap")
        if gap is None or spread is None:
            continue
        magnitude = abs(float(spread))
        if best is None or magnitude > best[0]:
            best = (magnitude, feature)
    if best is None:
        return "—"
    feature = best[1]
    sign = "+" if feature["absolute_gap"] >= 0 else ""
    return (
        f"`{feature['feature']}` {sign}{feature['absolute_gap']:.4g} "
        f"{feature['units']}"
    )


def write_phase3_report(config: AppConfig, payload: dict[str, Any]) -> Any:
    lines: list[str] = [
        "# Phase 3 — similarity engine, score maps and candidate sites",
        "",
        f"Generated by `python -m backend.engine.build_scores` on "
        f"{payload['created_utc']}.",
        "",
        "Every score in this report is **Earth-relative**. A Moon score and a Mars",
        "score are never comparable: they use different feature sets, different",
        "target distributions and different coverage. Read each target on its own.",
        "",
        "## 1. What the engine computes",
        "",
        "For every feature and every Earth land cell:",
        "",
        "* **absolute similarity** — `exp(-0.5 * (gap/scale)^2)`, where",
        "  `gap = Earth value - target median` and `scale` is the target p16–p84",
        "  half-spread floored by config. This is in real units.",
        "* **rank similarity** — `1 - |p_earth - q|`, where `p_earth` is the cell's",
        "  area-weighted percentile of Earth land and `q` is the Earth percentile of",
        "  the target median. Scale-free, so it can look close while the real gap is",
        "  huge.",
        f"* **hidden-gap flag** — set when rank similarity ≥ "
        f"{config.scoring.hidden_gap_rank_similarity:g} **and** absolute similarity ≤ "
        f"{config.scoring.hidden_gap_absolute_similarity:g}. The flag never changes "
        "the score; it warns the reader.",
        "* **area weighting** — every percentile, mean and top-site score is weighted",
        "  by `cos(latitude)`, so area is counted, not cells.",
        "* **qualitative thermal** — Moon temperature is scored by band distance, never",
        "  by a numeric Earth/Moon comparison; every such value is labelled",
        "  `qualitative` and the cited polar anchors are listed with it.",
        "",
        "## 2. Coverage per target",
        "",
        "| Target | Features used | of configured | Groups scored | of configured | Earth land area scored |",
        "|---|---|---|---|---|---|",
    ]
    for target in TARGETS:
        coverage = payload["targets"][target]["coverage"]
        lines.append(
            f"| {target} | {coverage['features_used']} | "
            f"{coverage['features_configured']} | {coverage['groups_scored']} | "
            f"{coverage['groups_configured']} | "
            f"{_pct(coverage['earth_land_area_fraction'])} |"
        )
    lines.extend(
        [
            "",
            "Mars legitimately uses fewer features: MOLA at ~3.7 km/px cannot resolve",
            "the 5 km roughness window or the Hurst lags, and its cited table has",
            "thermal inertia but no temperatures. The renormalised weights below show",
            "what is actually doing the work.",
            "",
            "## 3. Per-feature evidence",
            "",
        ]
    )
    for target in TARGETS:
        lines.extend(
            [
                f"### {target.capitalize()}",
                "",
                "| Feature | Group | Target median | Scale | Floor | Earth %ile of median | Mean abs sim | Mean rank sim | Hidden-gap area |",
                "|---|---|---|---|---|---|---|---|---|",
            ]
        )
        for feature_id, diag in payload["targets"][target]["feature_evidence"].items():
            hidden = (
                "—"
                if diag["qualitative"]
                else _pct(diag["hidden_gap_area_fraction"])
            )
            lines.append(
                f"| `{feature_id}` | {diag['group']} | {_num(diag['target_median'])} | "
                f"{_num(diag['scale'])} | {_num(diag['floor'])} | "
                f"{_num(diag['earth_percentile_of_median'])} | "
                f"{_pct(diag['mean_absolute_similarity'])} | "
                f"{_pct(diag['mean_rank_similarity'])} | {hidden} |"
            )
        lines.append("")
        qualitative = [
            (feature_id, diag)
            for feature_id, diag in payload["targets"][target]["feature_evidence"].items()
            if diag["qualitative"]
        ]
        for feature_id, diag in qualitative:
            bands = ", ".join(_pct(value) for value in diag["band_area_fractions"])
            anchor_lo, anchor_hi = diag["anchor_range_c"]
            anchor_span = (
                f"{anchor_lo:.2f} °C (single cited value)"
                if anchor_lo == anchor_hi
                else f"{anchor_lo:.2f} to {anchor_hi:.2f} °C"
            )
            lines.append(
                f"- `{feature_id}` is **qualitative**: target band {diag['target_band']} "
                f"from cited anchors {anchor_span} — {diag['anchor_label']}. "
                f"Earth band area fractions: {bands}."
            )
        if qualitative:
            lines.append("")

    lines.extend(
        [
            "## 4. Top sites",
            "",
            "Peaks are chosen by greedy non-maximum suppression at the preset's",
            "separation distance, so neighbouring cells cannot appear as separate",
            "sites. Each site score is the area-weighted mean within half that",
            "distance. The full lists (with every feature's gap, percentile and",
            "hidden-gap flag) are in `data/processed/top_sites.json`; these tables show",
            "the first ten.",
            "",
        ]
    )
    for target in TARGETS:
        lines.extend([f"### {target.capitalize()}", ""])
        for preset in config.presets:
            block = payload["targets"][target]["presets"][preset.name]
            lines.extend(
                [
                    f"#### {preset.label} (`{preset.name}`)",
                    "",
                    f"Renormalised weights: "
                    + ", ".join(
                        f"{name}={weight:g}"
                        for name, weight in block["weighting"]["weights_used"].items()
                    )
                    + (f"; dropped: {sorted(block['weighting']['weights_dropped'])}"
                       if block["weighting"]["weights_dropped"] else "")
                    + ".",
                    "",
                    f"Coverage of Earth land: {_pct(block['coverage'])}; "
                    f"mean score {_pct(block['score_stats']['land_area_weighted_mean'])}; "
                    f"{_pct(block['weight_coverage'])} of the preset's weight is available "
                    f"for this target"
                    + (
                        f"; largest share `{block['dominant_group']}` "
                        f"({_pct(block['weight_share'].get(block['dominant_group']))})"
                        if block.get("dominant_group")
                        else ""
                    )
                    + ".",
                    "",
                ]
                + (
                    [
                        f"*This preset reduces to the same ranking as "
                        f"`{block['equivalent_to']}` for this target, because its "
                        "other groups have no usable feature here. It is not "
                        "independent evidence.*",
                        "",
                    ]
                    if block.get("equivalent_to")
                    else []
                )
                + [
                    "| # | Latitude | Longitude | Score | Famous near |",
                    "|---|---|---|---|---|",
                ]
            )
            for index, site in enumerate(block["sites"][:10], start=1):
                lines.append(
                    f"| {index} | {site['lat']:.3f} | {site['lon']:.3f} | "
                    f"{_pct(site['site_score'])} | "
                    f"{site['famous_name'] or '—'} |"
                )
            excluded = block["sites_excluding_famous"][:5]
            if excluded:
                lines.extend(
                    [
                        "",
                        "Top five **not** within the famous-site radius:",
                        "",
                        "| # | Latitude | Longitude | Score |",
                        "|---|---|---|---|",
                    ]
                )
                for index, site in enumerate(excluded, start=1):
                    lines.append(
                        f"| {index} | {site['lat']:.3f} | {site['lon']:.3f} | "
                        f"{_pct(site['site_score'])} |"
                    )
            lines.append("")

    lines.extend(
        [
            "## 5. Known analogs and spot checks",
            "",
            "Scores are reported as found. Weights and band edges were **not** tuned to",
            "improve any analog. `reviewed: false` means the coordinate/source is a",
            "proposal awaiting the team's review.",
            "",
        ]
    )
    for target in TARGETS:
        block = payload["targets"][target]["presets"]["balanced"]
        lines.extend(
            [
                f"### {target.capitalize()} — balanced preset",
                "",
                "`Largest gap` is the numeric feature furthest from the target in "
                "target-spread units, with its real-unit gap. `Hidden` counts "
                "features whose rank similarity looks good while the real-unit gap "
                "is large.",
                "",
                "| Site | Latitude | Longitude | Score | Land percentile | Largest gap | Hidden | Reviewed |",
                "|---|---|---|---|---|---|---|---|",
            ]
        )
        for row in block["validation"]:
            largest = _largest_gap(row)
            hidden = sum(
                1
                for feature in row.get("features", [])
                if feature.get("hidden_real_unit_gap")
            )
            lines.append(
                f"| {row['name']} | {row['lat']:.3f} | {row['lon']:.3f} | "
                f"{_pct(row['score'])} | {_pct(row['land_percentile'])} | "
                f"{largest} | {hidden} | {'yes' if row['reviewed'] else 'no'} |"
            )
        lines.append("")

    lines.extend(["## 6. Thermal sensitivity (Moon)", ""])
    sensitivity = payload["targets"]["moon"]["thermal_sensitivity"]
    if sensitivity.get("applicable"):
        lines.extend(
            [
                "Band edges and the temperature weight were varied as required. "
                "Top-N overlap is measured against the balanced baseline; "
                "Spearman rho is computed on a fixed random sample of Earth land.",
                "",
                "| Temperature weight | Band edge shift | Top-N overlap | Spearman rho |",
                "|---|---|---|---|",
            ]
        )
        for variant in sensitivity["variants"]:
            lines.append(
                f"| {variant['temperature_weight']:g} | "
                f"{variant['band_edge_shift_c']:+g} °C | "
                f"{variant['top_n_overlap_fraction']:.2f} | "
                f"{_num(variant['spearman_rho_vs_baseline'], 4)} |"
            )
        lines.extend(
            [
                "",
                f"**Verdict:** {sensitivity['verdict']}. Minimum overlap "
                f"{sensitivity['min_top_n_overlap_fraction']:.2f}, minimum rho "
                f"{_num(sensitivity['min_spearman_rho'], 4)}.",
                "",
            ]
        )
    else:
        lines.extend([f"Not applicable: {sensitivity.get('reason', '')}.", ""])
    mars_sensitivity = payload["targets"]["mars"]["thermal_sensitivity"]
    if not mars_sensitivity.get("applicable"):
        lines.extend(
            [
                "Mars: no thermal features are available, so the thermal sensitivity",
                "test cannot change the Mars ranking and is reported as not applicable.",
                "",
            ]
        )

    lines.extend(
        [
            "## 7. What does not match",
            "",
            "* **Moon and Mars scores are not comparable** — different feature sets and",
            "  different targets. Never put them on one axis.",
            "* **PSR area fraction is context only.** Earth has no equivalent ice map, so",
            "  the Moon's 9.83% PSR fraction cannot rank Earth sites; it is shown on the",
            "  target card and given weight 0 in every preset.",
            "* **Temperature is qualitative.** The Moon numbers are surface skin",
            "  temperatures from cited polar rows, not 2 m air temperature. The band",
            "  score says 'same qualitative class', never 'same temperature'.",
            "* **The equatorial 400 K / 100 K rows are context.** They do not describe the",
            "  85–90°S target and are not scored.",
            "* **Physical differences Earth cannot represent:** gravity, vacuum or thin",
            "  atmosphere, radiation, and the lunar day length. A high score is a",
            "  terrain/climate analogy, not a habitable environment.",
            "* **Coverage differs by target.** Mars uses 4 of the 13 configured features",
            "  and 3 of the 7 groups; its renormalised weights reflect that, and its",
            "  scores should not be read as 'as well evidenced' as the Moon's.",
            "* **Surface composition is absent.** No Earth substrate, mineralogy or",
            "  thermal-inertia map is in this build, so a smooth ice sheet and a smooth",
            "  rock plain are indistinguishable to these features. The Mars ranking does",
            "  place Antarctic plateau cells at the top for that reason: the terrain",
            "  metrics match, the *material* does not. Read the Mars list as a terrain",
            "  result, and treat composition as a documented gap.",
            "* **Absolute similarity is generous when the target spread is wide.** The",
            "  scale is the target's own p16–p84 half-spread, so a high mean score means",
            "  'many Earth cells lie inside the target's central range', not 'many Earth",
            "  cells are true analogs'. Rank similarity and the hidden-gap flag are the",
            "  discriminators; read them together.",
            "* **Balanced is not the cold preset.** For the Moon the balanced preset gives",
            "  temperature only a small renormalised share, so tropical mountains can",
            "  outrank polar terrain on relief, slope and roughness alone. Use",
            "  `cold_trap_ice` or `thermal_cycling` when the cold environment is the",
            "  point, and say which preset produced a ranking whenever you quote it.",
            "",
        ]
    )
    text = "\n".join(lines)
    path = config.output("phase3_report")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _path_or_none(value: str):
    from pathlib import Path

    return None if value.lower() in {"", "none", "null"} else Path(value)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=_path_or_none,
        default=None,
        help="config override YAML deep-merged over config/*.yaml",
    )
    args = parser.parse_args()
    build(config=load_config(override=args.config))


if __name__ == "__main__":
    main()
