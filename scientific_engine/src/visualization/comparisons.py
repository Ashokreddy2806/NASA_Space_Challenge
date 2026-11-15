"""Comparison charts module.

Generates radar and bar chart comparisons between candidate Earth analog sites
and target planetary profiles.
Outputs saved to scientific_engine/outputs/plots/.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile
from scientific_engine.src.similarity.ranking import GLOBAL_CANDIDATE_POOL
from scientific_engine.src.similarity.scoring import SimilarityScorer

OUTPUT_PLOTS_DIR = ENGINE_DIR / "outputs" / "plots"


def generate_comparison_charts(output_dir: Optional[Path] = None) -> List[Path]:
    """Generate radar comparison cards for top matching Earth sites."""
    out_dir = output_dir or OUTPUT_PLOTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    scorer = SimilarityScorer()

    targets = [
        ("moon_south_pole", "Lunar South Pole", build_moon_target_profile()),
        ("mars_jezero_crater", "Mars Jezero Crater", build_jezero_profile()),
        ("mars_oxia_planum", "Mars Oxia Planum", build_oxia_planum_profile()),
    ]

    saved_charts: List[Path] = []

    for target_id, target_name, target_prof in targets:
        chart_file = out_dir / f"radar_comparison_{target_id}.svg"

        # Pick top 3 matching sites for this target
        scored = []
        for site in GLOBAL_CANDIDATE_POOL:
            res = scorer.score_cell(site["features"], target_prof, preset_name="balanced_default")
            scored.append((site, res))
        scored.sort(key=lambda x: x[1].overall_score, reverse=True)
        top3 = scored[:3]

        _render_radar_svg(chart_file, target_name, target_id, top3)
        saved_charts.append(chart_file)

    return saved_charts


def _render_radar_svg(
    filepath: Path,
    target_name: str,
    target_id: str,
    top_sites: List[Tuple[Dict[str, Any], Any]],
) -> None:
    """Render 6-axis radar comparison chart in SVG."""
    # 6 core dimensions: Relief, Slope, Roughness, Mean Temp, Diurnal Temp, Dryness
    dimensions = [
        ("Relief", "relief_20km_m"),
        ("Slope", "slope_20km_deg"),
        ("Roughness", "roughness_10km_m"),
        ("Mean Temp", "temp_mean_c"),
        ("Diurnal Range", "temp_diurnal_range_c"),
        ("Dryness", "precip_annual_mm"),
    ]

    cx, cy, radius = 300.0, 240.0, 160.0
    num_axes = len(dimensions)

    # Calculate axis endpoints
    axes_coords = []
    for i in range(num_axes):
        angle = (i * 2.0 * math.pi / num_axes) - (math.pi / 2.0)
        ax_x = cx + radius * math.cos(angle)
        ax_y = cy + radius * math.sin(angle)
        axes_coords.append((ax_x, ax_y, angle))

    # Grid rings (0.25, 0.5, 0.75, 1.0)
    rings_svg = ""
    for r_frac in (0.25, 0.50, 0.75, 1.0):
        r_pts = []
        for i in range(num_axes):
            angle = (i * 2.0 * math.pi / num_axes) - (math.pi / 2.0)
            rx = cx + (radius * r_frac) * math.cos(angle)
            ry = cy + (radius * r_frac) * math.sin(angle)
            r_pts.append(f"{rx:.1f},{ry:.1f}")
        rings_svg += f'<polygon points="{" ".join(r_pts)}" fill="none" stroke="#334155" stroke-width="1"/>'

    # Radial spokes & labels
    spokes_svg = ""
    for i, (ax_x, ax_y, angle) in enumerate(axes_coords):
        spokes_svg += f'<line x1="{cx}" y1="{cy}" x2="{ax_x}" y2="{ax_y}" stroke="#475569" stroke-width="1.2"/>'
        # Label offset
        lx = cx + (radius + 24.0) * math.cos(angle)
        ly = cy + (radius + 24.0) * math.sin(angle) + 4.0
        anchor = "middle" if abs(math.cos(angle)) < 0.3 else ("start" if math.cos(angle) > 0 else "end")
        spokes_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" fill="#cbd5e1" font-size="11" font-weight="600" text-anchor="{anchor}">{dimensions[i][0]}</text>'

    # Plot top site polygons
    site_colors = ["#38bdf8", "#f97316", "#22c55e"]
    polys_svg = ""
    legend_svg = ""

    for s_idx, (site, res) in enumerate(top_sites):
        color = site_colors[s_idx % len(site_colors)]
        pts = []
        for i, (_, feat_id) in enumerate(dimensions):
            # Subscore in [0, 100] converted to fraction [0, 1]
            sub = res.feature_subscores.get(feat_id, 50.0) / 100.0
            angle = (i * 2.0 * math.pi / num_axes) - (math.pi / 2.0)
            px = cx + (radius * max(0.1, min(1.0, sub))) * math.cos(angle)
            py = cy + (radius * max(0.1, min(1.0, sub))) * math.sin(angle)
            pts.append(f"{px:.1f},{py:.1f}")

        polys_svg += f"""
    <!-- Site: {site['name']} -->
    <polygon points="{" ".join(pts)}" fill="{color}" fill-opacity="0.25" stroke="{color}" stroke-width="2.2"/>
"""
        legend_y = 120 + s_idx * 40
        short_name = site["name"].split(" (")[0]
        legend_svg += f"""
    <g transform="translate(600, {legend_y})">
      <rect width="18" height="18" fill="{color}" rx="3"/>
      <text x="28" y="14" fill="#f8fafc" font-size="12" font-weight="600">{short_name}</text>
      <text x="28" y="28" fill="#94a3b8" font-size="10.5">Score: {res.overall_score:.1f}% | {site['country']}</text>
    </g>
"""

    svg = f"""<svg width="860" height="480" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <rect width="860" height="480" fill="#0f172a" rx="12"/>
  <text x="430" y="34" fill="#f8fafc" font-size="16" font-weight="bold" text-anchor="middle">Top Candidate Multi-Feature Radar: {target_name}</text>
  <text x="430" y="54" fill="#94a3b8" font-size="11.5" text-anchor="middle">Feature Match Subscores (100% = Identical to Target Profile) | Balanced Preset</text>

  <!-- Radar Grid -->
  {rings_svg}
  {spokes_svg}
  {polys_svg}

  <!-- Legend Panel -->
  <rect x="580" y="80" width="250" height="240" fill="#1e293b" rx="8" stroke="#334155"/>
  <text x="600" y="105" fill="#f8fafc" font-size="12" font-weight="bold">Top Matching Candidates</text>
  {legend_svg}

  <!-- Note -->
  <text x="430" y="455" fill="#64748b" font-size="10" text-anchor="middle">Generated by scientific_engine/src/visualization/comparisons.py</text>
</svg>"""
    filepath.write_text(svg, encoding="utf-8")
