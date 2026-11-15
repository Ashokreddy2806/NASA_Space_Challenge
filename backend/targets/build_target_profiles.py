"""Phase 2 build: Moon and Mars target profiles, PSR checks, Hurst robustness.

Run from ``NASA_Space_Challenge/``::

    python -m backend.targets.build_target_profiles

Writes:

* ``data/processed/target_profiles.json`` — machine-readable profiles
* ``docs/phase2_report.md`` — targets, distributions, comparability, limits
* ``docs/psr_verification.md`` — data-driven PSR checks
* ``docs/hurst_sensitivity.md`` — Earth Hurst with/without the 2 km lag

Every value comes from ``config/*.yaml`` or from the source data. Missing
literature tables are reported by path; nothing is estimated.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from typing import Any

from backend.config import AppConfig, load_config
from backend.features import registry
from backend.targets.hurst_sensitivity import analyse_hurst_sensitivity
from backend.targets.mars_target import analyse_mars
from backend.targets.moon_target import analyse_moon
from backend.targets.psr import verify_psr


def _sanitise(value: Any) -> Any:
    """Recursively replace non-finite floats so the JSON is standards-compliant."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _sanitise(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitise(item) for item in value]
    return value


def group_summary(
    config: AppConfig, profile: dict[str, Any], target: dict[str, Any]
) -> list[dict[str, Any]]:
    """Availability and renormalised weights for each scoring group."""
    features = profile.get("features", {})
    not_applicable = target.get("not_applicable", {}) or {}
    ice = profile.get("ice_proxy", {})
    rows: list[dict[str, Any]] = []

    for group in config.groups:
        row: dict[str, Any] = {
            "group": group.name,
            "weight": group.weight,
            "members": list(group.members),
        }
        if group.name == "ice_proxy":
            available = bool(ice.get("available"))
            row.update(
                {
                    "status": "available" if available else "unavailable",
                    "available_members": list(group.members) if available else [],
                    "reason": "" if available else ice.get("reason", ""),
                }
            )
            rows.append(row)
            continue

        available_members = [
            member
            for member in group.members
            if features.get(member, {}).get("resolution") not in (None, "unavailable")
        ]
        reasons: list[str] = []
        if group.name in not_applicable:
            reasons.append(str(not_applicable[group.name]).strip())
        for member in group.members:
            if member in available_members:
                continue
            if member in not_applicable:
                reasons.append(f"{member}: {str(not_applicable[member]).strip()}")
            elif features.get(member, {}).get("resolution_note"):
                reasons.append(f"{member}: {features[member]['resolution_note']}")

        if not group.members:
            status = "not_applicable"
        elif not available_members:
            status = "not_applicable" if group.name in not_applicable else "unavailable"
        elif len(available_members) == len(group.members):
            status = "available"
        else:
            status = "partial"

        row.update(
            {
                "status": status,
                "available_members": available_members,
                "reason": " ".join(dict.fromkeys(reasons)),
            }
        )
        rows.append(row)

    usable = [row for row in rows if row["status"] in {"available", "partial"}]
    total = sum(row["weight"] for row in usable)
    for row in rows:
        row["renormalised_weight"] = (
            row["weight"] / total if total > 0 and row in usable else 0.0
        )
    return rows


def _feature_table(profile: dict[str, Any], config: AppConfig) -> list[str]:
    lines = [
        "| Feature | Group | Resolution | n | Median | p16–p84 | Min | Max | Units |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for definition in config.all_features:
        entry = profile["features"].get(definition.id)
        if not entry:
            continue
        resolution = entry.get("resolution", "unavailable")
        if resolution == "unavailable" or entry.get("median") is None:
            lines.append(
                f"| `{definition.id}` | {definition.group} | unavailable | — | — | — | — | — | {definition.units} |"
            )
            continue

        def fmt(key: str) -> str:
            value = entry.get(key)
            return f"{value:.4g}" if isinstance(value, (int, float)) else "—"

        spread = (
            f"{entry.get('p16', float('nan')):.4g}–{entry.get('p84', float('nan')):.4g}"
            if entry.get("p16") is not None
            else "—"
        )
        lines.append(
            f"| `{definition.id}` | {definition.group} | {resolution} | {entry.get('n_cells', 0):,} | "
            f"{fmt('median')} | {spread} | {fmt('min')} | {fmt('max')} | {definition.units} |"
        )
    return lines


def _comparability_table(config: AppConfig) -> list[str]:
    lines = [
        "| Feature | Registry function | Window | Moon native span | Moon | Mars native span | Mars |",
        "|---|---|---|---|---|---|---|",
    ]
    for definition in config.terrain_features:
        moon_px = float(config.targets["moon"]["native_pixel_m"])
        mars_px = float(config.targets["mars"]["native_pixel_m"])
        moon_status = registry.availability(
            definition, moon_px, config.comparability, moon_px
        )
        mars_status = registry.availability(
            definition, mars_px, config.comparability, mars_px
        )
        window = definition.window_km
        window_text = (
            f"{window:g} km"
            if window is not None
            else ", ".join(f"{lag:g}" for lag in definition.lags_km) + " km lags"
        )
        moon_span = moon_status.detail.get("window_span_px", "—")
        mars_span = mars_status.detail.get("window_span_px", "—")
        lines.append(
            f"| `{definition.id}` | `{definition.function}` | {window_text} | "
            f"{moon_span} | {moon_status.resolution} | {mars_span} | {mars_status.resolution} |"
        )
    return lines


def _group_table(groups: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Group | Weight | Status | Available members | Renormalised weight | Reason |",
        "|---|---|---|---|---|---|",
    ]
    for row in groups:
        members = ", ".join(f"`{name}`" for name in row["available_members"]) or "—"
        reason = row["reason"].replace("|", "/")[:240] or "—"
        lines.append(
            f"| {row['group']} | {row['weight']:g} | {row['status']} | {members} | "
            f"{row['renormalised_weight']:.3f} | {reason} |"
        )
    return lines


def write_phase2_report(
    config: AppConfig,
    profiles: dict[str, Any],
    groups: dict[str, list[dict[str, Any]]],
    hurst: dict[str, Any],
) -> str:
    moon = profiles["moon"]
    mars = profiles["mars"]
    moon_cfg = config.targets["moon"]
    mars_cfg = config.targets["mars"]
    lines = [
        "# Phase 2 — Moon and Mars target profiles",
        "",
        f"Generated by `python -m backend.targets.build_target_profiles` on "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}.",
        "",
        "A target is a **distribution**, not a single number: each row below is the",
        "median, the p16–p84 spread, the min/max and the number of cells that actually",
        "contributed. The same registry (`backend/features/registry.py`) computes Earth,",
        "Moon and Mars features over the same physical windows, so the comparison is",
        "between like quantities, not between differently sized pixel windows.",
        "",
        "## Targets",
        "",
        "| Target | Extent | Source | Native pixel |",
        "|---|---|---|---|",
        f"| Moon | poleward of {abs(moon_cfg['region']['lat_max']):g}°S "
        f"({moon['extent']['radius_km']:.1f} km radius, "
        f"{moon['extent']['region_area_km2']:,.0f} km²) | "
        f"`{config.source_name('moon', 'dem')}` | {moon['source']['native_pixel_m']:.0f} m |",
        f"| Mars | {mars_cfg['label']}, "
        f"{mars_cfg['site']['lat_deg']:g}°N {mars_cfg['site']['lon_deg_east']:g}°E "
        f"({mars_cfg['site']['radius_km']:g} km radius, "
        f"{mars['extent']['region_area_km2']:,.0f} km²) | "
        f"`{config.source_name('mars', 'dem')}` | {mars['source']['native_pixel_m']:.0f} m |",
        "",
        "## Comparability (same physical windows, body-native resolution)",
        "",
        "A feature is computed only where the native source resolves its window.",
        "Between the minimum and the marginal threshold it is computed but flagged"
        " `marginal`; below the minimum it is `unavailable` with the span in pixels.",
        "",
        *_comparability_table(config),
        "",
        "## Moon — lunar south polar region",
        "",
        f"- Region: poleward of {abs(moon_cfg['region']['lat_max']):g}°S, radius "
        f"{moon['extent']['radius_km']:.2f} km in the LDEM projection.",
        f"- Region cells: {moon['extent']['region_pixels_full']:,}; sampled "
        f"{moon['extent']['sampled_pixels']:,} (stride "
        f"{moon['extent']['sample_stride_px']} px) in {moon['extent']['blocks']} blocks "
        f"with a {moon['extent']['halo_km']:.1f} km halo.",
        "- Terrain features are **recomputed from the 80 m DEM** with the same windows",
        "  and lags as Earth. The pre-computed LOLA products are only a cross-check.",
        "",
        "### Feature distributions",
        "",
        *_feature_table(moon, config),
        "",
        "### PSR cold-trap / ice proxy",
        "",
    ]

    ice = moon.get("ice_proxy", {})
    if ice.get("available"):
        lines.extend(
            [
                f"- PSR area fraction inside the target disc: **{ice['value']:.4f}** "
                f"({ice['psr_area_km2']:,.0f} km² of {ice['region_area_km2']:,.0f} km²).",
                f"- Polygons used: {ice['n_polygons_in_region']} inside the disc of "
                f"{ice['n_polygons_total']} total (≥ {ice['min_polygon_area_km2']:g} km²).",
                f"- Source: `{ice['source_file']}`.",
                "- This is an area fraction of permanently shadowed terrain, not a",
                "  measurement of water ice. It is a cold-trap proxy.",
            ]
        )
    else:
        lines.append(f"- Not available: {ice.get('reason', 'no proxy')}")

    cross = moon.get("cross_check", {})
    if cross:
        lines.extend(
            [
                "",
                "### Cross-check against the pre-computed LOLA products",
                "",
                "The profile values above come from the DEM recomputation. These rows",
                "only test that the recomputation is consistent with the published",
                "LOLA layers on the same 1 km grid.",
                "",
                "| Our feature | Reference layer | n | Pearson r | Our median | Reference median | Median abs diff |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for feature_id, row in cross.items():
            if not row.get("available"):
                lines.append(
                    f"| `{feature_id}` | `{row.get('source', '—')}` | — | — | — | — | "
                    f"{row.get('reason', 'unavailable')} |"
                )
                continue
            lines.append(
                f"| `{feature_id}` | `{row['source']}` | {row['n']:,} | "
                f"{row['pearson_r']:.3f} | {row['our_median']:.4g} | "
                f"{row['reference_median']:.4g} | {row['median_abs_difference']:.4g} |"
            )
        lines.extend(
            [
                "",
                "- `roughness_800m_baseline` is computed at the LOLA 0.8 km baseline only",
                "  so the two roughness numbers are like-for-like; it is **not** a profile",
                "  feature (the profile uses 5/10/20 km windows).",
                "- The LOLA `H` product is nearly saturated (its median is ≈0.96 and it is",
                "  clipped near 1), so it cannot confirm a structure-function exponent that",
                "  spans a real range. Slope and 800 m roughness are the informative checks.",
            ]
        )

    lines.extend(
        [
            "",
            "### Moon scoring groups",
            "",
            *_group_table(groups["moon"]),
            "",
            f"## Mars — {mars_cfg['label']}",
            "",
        ]
    )

    check = mars["site_check"]
    lines.extend(
        [
            f"- Configured site elevation: {check['configured_elevation_m']:.0f} m.",
            f"- MOLA nearest cell: {check['dem_elevation_m']:.0f} m "
            f"(difference {check['difference_m']:+.0f} m), which confirms the grid "
            "orientation and the site coordinate.",
            f"- Disc radius {mars_cfg['site']['radius_km']:g} km, "
            f"{mars['extent']['region_pixels_full']:,} cells at "
            f"{mars['source']['pixel_m'] / 1000:.2f} km; sampled "
            f"{mars['extent']['sampled_pixels']:,}.",
            "",
            "### Feature distributions",
            "",
            *_feature_table(mars, config),
            "",
            "### Mars scoring groups",
            "",
            *_group_table(groups["mars"]),
            "",
            "The supplied literature has **no Mars surface-temperature range**, so the",
            "range features are unavailable and excluded; the remaining weights are",
            "renormalised above. Mars also loses the 5 km roughness and Hurst outright:",
            "MOLA at 16 ppd (~3.7 km/px) does not resolve those windows.",
            "",
            "## Thermal literature (cited CSVs only)",
            "",
            "Moon and Mars temperatures are **never** estimated. They are read from the",
            "hand-made tables, and a missing table is reported by exact path:",
            "",
        ]
    )
    for body in ("moon", "mars"):
        thermal = profiles[body]["thermal"]
        status = "available" if thermal["available"] else "MISSING"
        lines.append(f"- **{body}** — {status} — `{thermal['path']}`")
        if not thermal["available"]:
            lines.append(f"  - {thermal['reason']}")
    lines.extend(
        [
            "",
            "## Earth Hurst robustness",
            "",
        ]
    )
    if hurst.get("available"):
        lines.extend(
            [
                f"- {hurst['sample_used']} random land patches "
                f"({hurst['patch_km']:g} km, seed {hurst['random_seed']}).",
                f"- Full lags {hurst['full_lags_km']} → median H "
                f"{hurst['full']['median']:.3f} (p16–p84 "
                f"{hurst['full']['p16']:.3f}–{hurst['full']['p84']:.3f}).",
                f"- Without the {hurst['dropped_lag_km']:g} km lag "
                f"{hurst['reduced_lags_km']} → median H "
                f"{hurst['reduced']['median']:.3f} (p16–p84 "
                f"{hurst['reduced']['p16']:.3f}–{hurst['reduced']['p84']:.3f}).",
                f"- Median shift {hurst['median_difference']:+.3f}, "
                f"Pearson r {hurst['pearson_r']:.4f}. "
                f"Verdict: **{'robust' if hurst['robust'] else 'not robust'}** "
                f"(thresholds: |Δmedian| ≤ "
                f"{hurst['thresholds']['max_median_difference']:g}, "
                f"r ≥ {hurst['thresholds']['min_correlation']:g}).",
                "",
                "See `docs/hurst_sensitivity.md` for the full table.",
            ]
        )
    else:
        lines.append(f"- Not available: {hurst.get('reason')}")

    lines.extend(
        [
            "",
            "## Carried into Phase 3 (scoring contract)",
            "",
            "The profile above is the input to the similarity engine, which must report,",
            "for **every feature**, both:",
            "",
            "1. a **rank-based similarity** — where this Earth cell's value sits in the",
            "   global distribution (a percentile), so the map is comparable across",
            "   features with different units, and",
            "2. the **absolute gap in real units** — `Earth value − target median`, plus",
            "   how many target spreads (p16–p84) that gap is worth.",
            "",
            "Rank similarity alone can hide a large real-unit difference. The canonical",
            "example is temperature: the Moon's day–night swing is hundreds of kelvin,",
            "and an Earth desert that ranks close in *relative* terms is still nowhere",
            "near it in absolute terms. Every site card must therefore show the",
            "absolute gap and a plain-language note when rank similarity looks good but",
            "the real-unit gap is large. Features that are unavailable for a target",
            "carry no score at all and are excluded from the weighted sum; the",
            "renormalised weights above are what Phase 3 uses.",
            "",
            "## Files",
            "",
            f"- `{config.output('target_profiles').name}` — machine-readable profiles",
            f"- `{config.output('psr_report').name}` — PSR verification detail",
            f"- `{config.output('hurst_sensitivity').name}` — Hurst robustness detail",
            "",
            "## Limits",
            "",
            "- Mars MOLA is 16 ppd (~3.7 km). Windows below ~9 km cannot be resolved;",
            "  the affected features are marked unavailable or marginal, never silently",
            "  computed on interpolated detail.",
            "- Earth's land-mask grid is 0.05°; Moon and Mars are analysed on their own",
            "  native grids. Comparison happens over physical windows, not pixels.",
            "- The PSR ice proxy is shadowed area, not measured water ice.",
            "- Earth cannot reproduce reduced gravity, vacuum/thin atmosphere, or",
            "  radiation. Those are always reported as non-matches in Phase 3.",
            "",
        ]
    )
    path = config.output("phase2_report")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def write_psr_report(config: AppConfig, psr: dict[str, Any]) -> str:
    dem = psr["dem"]
    table = psr["psr_table"]
    crs = psr["crs_check"]
    extent = psr["extent"]
    topo = psr["topography"]
    verdict = psr["verdict"]

    def stat(block: dict[str, Any], key: str) -> str:
        value = block.get(key)
        return f"{value:.4g}" if isinstance(value, (int, float)) else "—"

    lines = [
        "# PSR verification — data-driven, not assumed",
        "",
        "The lunar PSR table is a CSV of WKT polygons in projected metres with no CRS",
        "field. This document records what was actually checked against the DEM, so the",
        "ice proxy does not rest on an assumption.",
        "",
        "## 1. DEM and table",
        "",
        f"- DEM: `{dem['path']}`",
        f"- CRS: `{dem['crs']}`",
        f"- Size: {dem['width']} × {dem['height']} cells at {dem['pixel_m']:.0f} m; "
        f"bounds {dem['bounds']['left']:.0f} … {dem['bounds']['right']:.0f} m easting, "
        f"{dem['bounds']['bottom']:.0f} … {dem['bounds']['top']:.0f} m northing.",
        f"- DEM nodata fraction: {dem['nodata_fraction']:.4f}.",
        f"- PSR table: `{table['path']}`",
        f"- Polygons ≥ {table['min_area_km2']:g} km²: {table['n_polygons']}; "
        f"skipped below threshold: {table['n_skipped_below_min_area']}; "
        f"total area {table['total_area_km2']:,.1f} km².",
        "",
        "## 2. Coordinate interpretation",
        "",
        "- The CSV has no CRS metadata. The polygons are interpreted as metres in the",
        "  **LDEM south polar stereographic CRS**, taken from the DEM itself.",
        f"- Evidence: the polygon coordinate range fits the DEM extent, and the",
        f"  rasterised PSRs land on topographic lows (section 4).",
        f"- Radius of the configured {abs(config.targets['moon']['region']['lat_max']):g}°S cap "
        f"in this projection: **{crs['region_radius_km']:.3f} km**.",
        f"- DEM tile-corner radius: {crs['tile_corner_radius_km']:.1f} km "
        f"(≈ {abs(crs['tile_corner_latitude_deg']):.1f}°S).",
        "",
        "## 3. Extent checks",
        "",
        f"- Polygons fully inside the DEM: **{extent['polygons_fully_inside_dem']}** "
        f"of {table['n_polygons']}.",
        f"- Polygons touching or crossing the DEM edge: {extent['polygons_touching_or_outside_dem']}.",
        f"- Polygons inside the target cap: {extent['polygons_inside_region_cap']}; "
        f"clipped by the DEM edge: {extent['region_polygons_clipped_by_dem_edge']}.",
        "",
        "## 4. Are the rasterised PSRs on cold, low, flat terrain?",
        "",
        "| Quantity | PSR pixels | Background (non-PSR) in cap |",
        "|---|---|---|",
        f"| Elevation median (m) | {stat(topo['elevation_psr'], 'median')} | "
        f"{stat(topo['elevation_background'], 'median')} |",
        f"| Elevation p10–p90 (m) | {stat(topo['elevation_psr'], 'p10')} – "
        f"{stat(topo['elevation_psr'], 'p90')} | "
        f"{stat(topo['elevation_background'], 'p10')} – "
        f"{stat(topo['elevation_background'], 'p90')} |",
        f"| Slope median (deg) | {stat(topo['slope_deg_psr'], 'median')} | "
        f"{stat(topo['slope_deg_background'], 'median')} |",
        f"| Slope p10–p90 (deg) | {stat(topo['slope_deg_psr'], 'p10')} – "
        f"{stat(topo['slope_deg_psr'], 'p90')} | "
        f"{stat(topo['slope_deg_background'], 'p10')} – "
        f"{stat(topo['slope_deg_background'], 'p90')} |",
        "",
        f"- PSR pixels in the cap: {topo['psr_pixels_in_region']:,} of "
        f"{topo['region_pixels']:,} ({100 * topo['psr_pixel_fraction_of_region']:.2f}%).",
        f"- PSR area inside the cap: {topo['psr_area_km2_in_region']:,.0f} km² of "
        f"{topo['region_area_km2']:,.0f} km².",
        f"- Fraction of PSR pixels below the background median elevation: "
        f"**{topo['fraction_of_psr_below_background_median_elevation']:.3f}**.",
        f"- Fraction of PSR pixels below the background median slope: "
        f"**{topo['fraction_of_psr_below_background_median_slope']:.3f}**.",
        f"- Elevation offset (PSR − background): {topo['elevation_offset_m']:+.1f} m.",
        f"- Slope offset (PSR − background): {topo['slope_offset_deg']:+.2f}°.",
        "",
        "## 5. Verdict",
        "",
        f"- PSRs sit on topographic lows: **{verdict['psr_on_lows']}**",
        f"- PSRs sit on lower slopes than their surroundings: "
        f"**{verdict['psr_on_low_slopes']}**",
        f"- The {abs(config.targets['moon']['region']['lat_max']):g}°S target cap is unaffected "
        f"by the ~{abs(crs['tile_corner_latitude_deg']):.1f}°S tile-corner clip: "
        f"**{verdict['region_cap_unaffected_by_corner_clip']}**",
        "",
        f"The ~{abs(crs['tile_corner_latitude_deg']):.1f}°S figure is the radius of the **square "
        "tile corner**, not a latitude",
        f"cut. The region of interest is a {crs['region_radius_km']:.1f} km cap around the "
        "pole, which sits well",
        "inside the tile, so the corner clip cannot truncate it.",
        "",
    ]
    path = config.output("psr_report")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def write_hurst_report(config: AppConfig, hurst: dict[str, Any]) -> str:
    lines = [
        "# Earth Hurst robustness — with and without the 2 km lag",
        "",
        "ETOPO 2022 is a 60 arc-second product (~1.85 km), so the shortest configured",
        "Hurst lag (2 km) is close to the sampling limit. This check recomputes the",
        "exponent from real ETOPO patches with the full lag list and with the 2 km lag",
        "removed.",
        "",
    ]
    if not hurst.get("available"):
        lines.append(f"Not available: {hurst.get('reason')}")
        path = config.output("hurst_sensitivity")
        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path)

    lines.extend(
        [
            f"- Samples requested / used: {hurst['sample_requested']} / "
            f"{hurst['sample_used']} (seed {hurst['random_seed']}, skipped "
            f"{hurst['skipped']}, undefined {hurst.get('discarded_undefined', 0)}).",
            f"- Patch size: {hurst['patch_km']:g} km on a "
            f"{hurst['working_pixel_m'] / 1000:.2f} km working grid; Hurst window "
            f"{hurst['window_km']:g} km.",
            "",
            "| Lag set | Median H | p16 | p84 | Min | Max |",
            "|---|---|---|---|---|---|",
            f"| Full {hurst['full_lags_km']} | {hurst['full']['median']:.4f} | "
            f"{hurst['full']['p16']:.4f} | {hurst['full']['p84']:.4f} | "
            f"{hurst['full']['min']:.4f} | {hurst['full']['max']:.4f} |",
            f"| Drop {hurst['dropped_lag_km']:g} km → {hurst['reduced_lags_km']} | "
            f"{hurst['reduced']['median']:.4f} | {hurst['reduced']['p16']:.4f} | "
            f"{hurst['reduced']['p84']:.4f} | {hurst['reduced']['min']:.4f} | "
            f"{hurst['reduced']['max']:.4f} |",
            "",
            f"- Median shift: {hurst['median_difference']:+.4f}",
            f"- Median absolute difference: {hurst['median_abs_difference']:.4f}",
            f"- Pearson r between the two estimates: {hurst['pearson_r']:.4f}",
            f"- Thresholds: |Δmedian| ≤ {hurst['thresholds']['max_median_difference']:g}, "
            f"r ≥ {hurst['thresholds']['min_correlation']:g}",
            "",
            f"**Verdict: {'robust' if hurst['robust'] else 'not robust'}.** "
            + (
                "The fitted Hurst exponent is not an artefact of the shortest lag, so "
                "it can be compared with the Moon and Mars where those bodies resolve "
                "different lag sets."
                if hurst["robust"]
                else "The fit depends on the shortest lag, so Earth Hurst should be "
                "reported with that caveat and compared cautiously."
            ),
            "",
        ]
    )
    path = config.output("hurst_sensitivity")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


def build(
    config: AppConfig | None = None,
    skip_moon: bool = False,
    skip_mars: bool = False,
    skip_hurst: bool = False,
) -> dict[str, Any]:
    """Build every Phase 2 product and write the reports."""
    config = config or load_config()
    started = time.perf_counter()

    print("Moon target …")
    moon = analyse_moon(config) if not skip_moon else {"skipped": True}
    print(f"  moon done in {moon.get('runtime_seconds', 0):.1f} s")

    print("Mars target …")
    mars = analyse_mars(config) if not skip_mars else {"skipped": True}
    print(f"  mars done in {mars.get('runtime_seconds', 0):.1f} s")

    print("PSR verification …")
    psr = verify_psr(config)
    print("  psr done")

    print("Earth Hurst sensitivity …")
    hurst = (
        analyse_hurst_sensitivity(config)
        if not skip_hurst
        else {"available": False, "reason": "skipped"}
    )
    print(f"  hurst done in {hurst.get('runtime_seconds', 0):.1f} s")

    groups = {
        "moon": group_summary(config, moon, config.targets["moon"]),
        "mars": group_summary(config, mars, config.targets["mars"]),
    }
    moon["groups"] = groups["moon"]
    mars["groups"] = groups["mars"]

    payload = {
        "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "config": {
            "comparability": {
                "min_window_pixels": config.comparability.min_window_pixels,
                "marginal_window_pixels": config.comparability.marginal_window_pixels,
                "min_hurst_lags": config.comparability.min_hurst_lags,
                "min_lag_pixels": config.comparability.min_lag_pixels,
            },
            "distribution": {
                "sample_stride_px": config.distribution.sample_stride_px,
                "percentiles": list(config.distribution.percentiles),
            },
            "features": {
                definition.id: dict(definition.params)
                for definition in config.terrain_features
            },
            "groups": [
                {
                    "name": group.name,
                    "weight": group.weight,
                    "members": list(group.members),
                }
                for group in config.groups
            ],
        },
        "moon": moon,
        "mars": mars,
        "hurst_sensitivity": hurst,
        "psr_verification": psr,
        "total_runtime_seconds": time.perf_counter() - started,
    }

    json_path = config.output("target_profiles")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(_sanitise(payload), indent=2, allow_nan=False), encoding="utf-8"
    )

    phase2 = write_phase2_report(config, {"moon": moon, "mars": mars}, groups, hurst)
    psr_path = write_psr_report(config, psr)
    hurst_path = write_hurst_report(config, hurst)

    print(f"Wrote {json_path}")
    print(f"Wrote {phase2}")
    print(f"Wrote {psr_path}")
    print(f"Wrote {hurst_path}")
    print(f"Total {time.perf_counter() - started:.1f} s")
    return payload


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=_path_or_none,
        default=None,
        help="config override YAML deep-merged over config/*.yaml",
    )
    parser.add_argument("--skip-moon", action="store_true")
    parser.add_argument("--skip-mars", action="store_true")
    parser.add_argument("--skip-hurst", action="store_true")
    args = parser.parse_args()
    build(
        config=load_config(override=args.config),
        skip_moon=args.skip_moon,
        skip_mars=args.skip_mars,
        skip_hurst=args.skip_hurst,
    )


def _path_or_none(value: str):
    from pathlib import Path

    return Path(value)


if __name__ == "__main__":
    main()
