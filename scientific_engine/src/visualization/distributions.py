"""Distribution plotting module.

Generates publication-quality distribution plots comparing Moon, Mars,
and Earth analog distributions in compatible units.
Outputs saved to scientific_engine/outputs/plots/.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile
from scientific_engine.src.similarity.normalization import EARTH_REFERENCE_DISTRIBUTIONS

OUTPUT_PLOTS_DIR = ENGINE_DIR / "outputs" / "plots"


def generate_distribution_plots(output_dir: Optional[Path] = None) -> List[Path]:
    """Generate distribution comparison plots comparing Earth, Moon, and Mars."""
    out_dir = output_dir or OUTPUT_PLOTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    moon = build_moon_target_profile()["features"]
    jezero = build_jezero_profile()["features"]
    oxia = build_oxia_planum_profile()["features"]

    features_to_plot = [
        ("relief_20km_m", "Local Relief in 20 km Window", "m"),
        ("slope_20km_deg", "Terrain Slope in 20 km Window", "degrees"),
        ("roughness_10km_m", "High-Pass Roughness at 10 km Baseline", "m"),
        ("hurst_2_32km", "Scale-Robust Roughness (Hurst Exponent)", "unitless"),
        ("temp_mean_c", "Annual Mean Temperature", "deg C"),
        ("temp_diurnal_range_c", "Diurnal Temperature Range (Delta T)", "deg C"),
        ("temp_min_coldest_c", "Cold Extreme / Minimum Temperature", "deg C"),
    ]

    saved_plots: List[Path] = []

    # Try matplotlib if available
    has_plt = False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        has_plt = True
    except ImportError:
        has_plt = False

    for feat_id, feat_title, units in features_to_plot:
        svg_file = out_dir / f"dist_{feat_id}.svg"

        earth_dist = EARTH_REFERENCE_DISTRIBUTIONS.get(feat_id, (0, 0, 0, 0, 0, 0, 0))
        e_min, e_p25, e_med, e_p75, e_max, e_mean, e_std = earth_dist

        moon_val = moon[feat_id]["value"]
        moon_spread = (moon[feat_id]["q25"], moon[feat_id]["q75"])

        jezero_val = jezero[feat_id]["value"]
        jezero_spread = (jezero[feat_id]["q25"], jezero[feat_id]["q75"])

        oxia_val = oxia[feat_id]["value"]
        oxia_spread = (oxia[feat_id]["q25"], oxia[feat_id]["q75"])

        if has_plt:
            png_file = out_dir / f"dist_{feat_id}.png"
            _plot_matplotlib(
                png_file, feat_title, units,
                earth_dist, (moon_val, moon_spread),
                (jezero_val, jezero_spread), (oxia_val, oxia_spread)
            )
            saved_plots.append(png_file)

        # Generate robust SVG representation
        _plot_svg(
            svg_file, feat_title, units,
            earth_dist, (moon_val, moon_spread),
            (jezero_val, jezero_spread), (oxia_val, oxia_spread)
        )
        saved_plots.append(svg_file)

    # Master overview dashboard
    dashboard_svg = out_dir / "planetary_features_distribution_dashboard.svg"
    _generate_dashboard_svg(dashboard_svg, features_to_plot, moon, jezero, oxia)
    saved_plots.append(dashboard_svg)

    return saved_plots


def _plot_svg(
    filepath: Path,
    title: str,
    units: str,
    earth_stats: Tuple[float, ...],
    moon_data: Tuple[float, Tuple[float, float]],
    jezero_data: Tuple[float, Tuple[float, float]],
    oxia_data: Tuple[float, Tuple[float, float]],
) -> None:
    """Generate high-resolution vector SVG distribution chart."""
    e_min, e_p25, e_med, e_p75, e_max, _, _ = earth_stats
    m_val, m_spr = moon_data
    j_val, j_spr = jezero_data
    o_val, o_spr = oxia_data

    # Find common axis bounds
    all_vals = [e_min, e_max, m_val, m_spr[0], m_spr[1], j_val, j_spr[0], j_spr[1], o_val, o_spr[0], o_spr[1]]
    min_x = min(all_vals)
    max_x = max(all_vals)
    span = max_x - min_x if max_x > min_x else 1.0
    min_x -= span * 0.05
    max_x += span * 0.05
    span = max_x - min_x

    def scale_x(val: float) -> float:
        return 140.0 + 580.0 * ((val - min_x) / span)

    svg = f"""<svg width="800" height="380" xmlns="http://www.w3.org/2000/svg" style="background:#0f172a;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <rect width="800" height="380" fill="#0f172a" rx="12"/>
  <text x="400" y="36" text-anchor="middle" fill="#f8fafc" font-size="17" font-weight="bold">{title}</text>
  <text x="400" y="58" text-anchor="middle" fill="#94a3b8" font-size="12">Units: {units} | Earth 0.05° Land vs. Moon South Pole vs. Mars Landing Sites</text>

  <!-- Grid lines -->
  <line x1="140" y1="80" x2="140" y2="300" stroke="#334155" stroke-width="1"/>
  <line x1="720" y1="80" x2="720" y2="300" stroke="#334155" stroke-width="1"/>
  <line x1="140" y1="300" x2="720" y2="300" stroke="#64748b" stroke-width="2"/>

  <!-- Axis ticks -->
  <text x="140" y="322" fill="#94a3b8" font-size="11" text-anchor="middle">{min_x:.1f}</text>
  <text x="430" y="322" fill="#94a3b8" font-size="11" text-anchor="middle">{(min_x + max_x)/2:.1f}</text>
  <text x="720" y="322" fill="#94a3b8" font-size="11" text-anchor="middle">{max_x:.1f}</text>

  <!-- Row 1: Earth Land (0.05 deg Grid) -->
  <text x="25" y="115" fill="#38bdf8" font-size="13" font-weight="600">Earth Land (Global)</text>
  <line x1="{scale_x(e_min)}" y1="110" x2="{scale_x(e_max)}" y2="110" stroke="#38bdf8" stroke-width="2"/>
  <rect x="{scale_x(e_p25)}" y="98" width="{max(4, scale_x(e_p75) - scale_x(e_p25))}" height="24" fill="#0284c7" opacity="0.4" rx="4"/>
  <line x1="{scale_x(e_med)}" y1="94" x2="{scale_x(e_med)}" y2="126" stroke="#bae6fd" stroke-width="3"/>
  <text x="{scale_x(e_med)}" y="90" fill="#bae6fd" font-size="11" text-anchor="middle">Med: {e_med:.1f}</text>

  <!-- Row 2: Moon South Pole (85S-90S) -->
  <text x="25" y="165" fill="#e2e8f0" font-size="13" font-weight="600">Moon South Pole</text>
  <line x1="{scale_x(m_spr[0])}" y1="160" x2="{scale_x(m_spr[1])}" y2="160" stroke="#e2e8f0" stroke-width="2"/>
  <circle cx="{scale_x(m_val)}" cy="160" r="7" fill="#f8fafc" stroke="#38bdf8" stroke-width="2"/>
  <text x="{scale_x(m_val)}" y="148" fill="#f8fafc" font-size="11" text-anchor="middle">{m_val:.1f}</text>

  <!-- Row 3: Mars Jezero Crater -->
  <text x="25" y="215" fill="#f97316" font-size="13" font-weight="600">Mars Jezero Crater</text>
  <line x1="{scale_x(j_spr[0])}" y1="210" x2="{scale_x(j_spr[1])}" y2="210" stroke="#f97316" stroke-width="2"/>
  <circle cx="{scale_x(j_val)}" cy="210" r="7" fill="#ea580c" stroke="#ffedd5" stroke-width="2"/>
  <text x="{scale_x(j_val)}" y="198" fill="#ffedd5" font-size="11" text-anchor="middle">{j_val:.1f}</text>

  <!-- Row 4: Mars Oxia Planum -->
  <text x="25" y="265" fill="#ef4444" font-size="13" font-weight="600">Mars Oxia Planum</text>
  <line x1="{scale_x(o_spr[0])}" y1="260" x2="{scale_x(o_spr[1])}" y2="260" stroke="#ef4444" stroke-width="2"/>
  <circle cx="{scale_x(o_val)}" cy="260" r="7" fill="#dc2626" stroke="#fee2e2" stroke-width="2"/>
  <text x="{scale_x(o_val)}" y="248" fill="#fee2e2" font-size="11" text-anchor="middle">{o_val:.1f}</text>

  <!-- Legend -->
  <rect x="220" y="340" width="360" height="26" fill="#1e293b" rx="6"/>
  <rect x="235" y="348" width="14" height="10" fill="#0284c7" opacity="0.6"/>
  <text x="255" y="357" fill="#cbd5e1" font-size="10">Earth IQR (p25-p75)</text>
  <circle cx="390" cy="353" r="5" fill="#f8fafc"/>
  <text x="402" y="357" fill="#cbd5e1" font-size="10">Moon Pole</text>
  <circle cx="485" cy="353" r="5" fill="#f97316"/>
  <text x="497" y="357" fill="#cbd5e1" font-size="10">Mars Sites</text>
</svg>"""
    filepath.write_text(svg, encoding="utf-8")


def _plot_matplotlib(png_path: Path, title: str, units: str, earth_stats, moon_d, jezero_d, oxia_d):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4), facecolor="#0f172a")
    ax.set_facecolor("#1e293b")
    # Simple horizontal comparison
    e_med = earth_stats[2]
    m_val = moon_d[0]
    j_val = jezero_d[0]
    o_val = oxia_d[0]

    y = [3, 2, 1, 0]
    vals = [e_med, m_val, j_val, o_val]
    labels = ["Earth (Median)", "Moon South Pole", "Mars Jezero", "Mars Oxia Planum"]
    colors = ["#38bdf8", "#e2e8f0", "#f97316", "#ef4444"]

    ax.barh(y, vals, color=colors, height=0.5, edgecolor="none")
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color="#f8fafc", fontsize=10)
    ax.tick_params(colors="#94a3b8")
    ax.set_xlabel(f"{title} ({units})", color="#f8fafc", fontsize=11)
    ax.set_title(f"Target Distribution Comparison: {title}", color="#f8fafc", fontsize=13, pad=12)
    plt.tight_layout()
    plt.savefig(png_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close()


def _generate_dashboard_svg(filepath: Path, features_list, moon, jezero, oxia) -> None:
    """Generate high-density master distribution comparison card."""
    rows = ""
    y = 90
    for feat_id, feat_title, units in features_list:
        e_dist = EARTH_REFERENCE_DISTRIBUTIONS.get(feat_id, (0, 0, 0, 0, 0, 0, 0))
        m_val = moon[feat_id]["value"]
        j_val = jezero[feat_id]["value"]
        o_val = oxia[feat_id]["value"]

        rows += f"""
    <tr style="border-bottom:1px solid #334155;height:32px;">
      <td style="padding:6px;color:#f8fafc;font-weight:500;">{feat_title}</td>
      <td style="padding:6px;color:#94a3b8;">{units}</td>
      <td style="padding:6px;color:#38bdf8;text-align:right;">{e_dist[2]:.1f}</td>
      <td style="padding:6px;color:#e2e8f0;text-align:right;">{m_val:.1f}</td>
      <td style="padding:6px;color:#f97316;text-align:right;">{j_val:.1f}</td>
      <td style="padding:6px;color:#ef4444;text-align:right;">{o_val:.1f}</td>
    </tr>"""

    html = f"""<svg width="840" height="420" xmlns="http://www.w3.org/2000/svg">
  <foreignObject width="840" height="420">
    <div xmlns="http://www.w3.org/1999/xhtml" style="background:#0f172a;color:#f8fafc;padding:20px;border-radius:12px;font-family:-apple-system,sans-serif;font-size:12px;">
      <h2 style="margin:0 0 4px 0;font-size:16px;color:#f8fafc;">Master Target Profile Distribution Matrix</h2>
      <p style="margin:0 0 12px 0;color:#94a3b8;font-size:11px;">Phase 2 Verified Target Feature Distributions vs. Earth Land Global Median (docs/FEATURES.md contract)</p>
      <table style="width:100%;border-collapse:collapse;font-size:11px;">
        <thead>
          <tr style="border-bottom:2px solid #475569;color:#cbd5e1;text-align:left;">
            <th style="padding:6px;">Feature</th>
            <th style="padding:6px;">Units</th>
            <th style="padding:6px;text-align:right;color:#38bdf8;">Earth Land (Median)</th>
            <th style="padding:6px;text-align:right;color:#e2e8f0;">Moon South Pole</th>
            <th style="padding:6px;text-align:right;color:#f97316;">Mars Jezero</th>
            <th style="padding:6px;text-align:right;color:#ef4444;">Mars Oxia Planum</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </div>
  </foreignObject>
</svg>"""
    filepath.write_text(html, encoding="utf-8")
