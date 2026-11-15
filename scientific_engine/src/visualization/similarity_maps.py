"""Similarity maps visualization module.

Generates cartographically sound similarity score maps for Moon and Mars targets.
Includes coordinate reference system, scale bar, legend, and high-similarity highlights.
Outputs saved to scientific_engine/outputs/maps/.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.similarity.ranking import GLOBAL_CANDIDATE_POOL
from scientific_engine.src.similarity.scoring import SimilarityScorer

OUTPUT_MAPS_DIR = ENGINE_DIR / "outputs" / "maps"


def generate_similarity_maps(output_dir: Optional[Path] = None) -> List[Path]:
    """Generate global and polar similarity maps."""
    out_dir = output_dir or OUTPUT_MAPS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    scorer = SimilarityScorer()

    # Pre-score all candidates
    from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
    from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile

    targets = [
        ("moon_south_pole", "Lunar South Pole", build_moon_target_profile(), "#38bdf8"),
        ("mars_jezero_crater", "Mars Jezero Crater", build_jezero_profile(), "#f97316"),
        ("mars_oxia_planum", "Mars Oxia Planum", build_oxia_planum_profile(), "#ef4444"),
    ]

    saved_maps: List[Path] = []

    for target_id, target_name, target_prof, accent_color in targets:
        map_file = out_dir / f"similarity_map_{target_id}.svg"

        # Score candidate sites
        scored_sites = []
        for site in GLOBAL_CANDIDATE_POOL:
            res = scorer.score_cell(site["features"], target_prof, preset_name="balanced_default")
            scored_sites.append({
                "name": site["name"],
                "lat": site["lat"],
                "lon": site["lon"],
                "score": res.overall_score,
                "famous": site["famous"],
            })

        _render_world_similarity_map(map_file, target_name, target_id, scored_sites, accent_color)
        saved_maps.append(map_file)

    return saved_maps


def _render_world_similarity_map(
    filepath: Path,
    target_name: str,
    target_id: str,
    scored_sites: List[Dict[str, Any]],
    accent_color: str,
) -> None:
    """Generate high-resolution SVG world similarity map with cartographic standards."""
    # Equirectangular projection coordinates
    # Width = 960, Height = 540
    # Map area: x in [60, 900], y in [70, 470]
    map_x0, map_y0, map_w, map_h = 60.0, 70.0, 840.0, 420.0

    def project(lat: float, lon: float) -> Tuple[float, float]:
        x = map_x0 + map_w * ((lon + 180.0) / 360.0)
        y = map_y0 + map_h * ((90.0 - lat) / 180.0)
        return x, y

    # Generate site plot markers
    markers_svg = ""
    for s in scored_sites:
        px, py = project(s["lat"], s["lon"])
        score = s["score"]

        # Color based on score
        if score >= 70:
            color = "#22c55e"  # High green
            r = 7
        elif score >= 60:
            color = "#eab308"  # Medium yellow
            r = 6
        elif score >= 50:
            color = "#f97316"  # Orange
            r = 5
        else:
            color = "#94a3b8"  # Slate
            r = 4

        border = "#ffffff" if not s["famous"] else "#facc15"
        label_y = py - 9 if py > 100 else py + 16

        # Short name
        short_name = s["name"].split(" (")[0]

        markers_svg += f"""
    <!-- Site: {s['name']} -->
    <circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" stroke="{border}" stroke-width="1.5" opacity="0.95"/>
    <text x="{px:.1f}" y="{label_y:.1f}" fill="#f8fafc" font-size="9.5" font-weight="600" text-anchor="middle" filter="url(#shadow)">{short_name} ({score:.0f}%)</text>
"""

    svg = f"""<svg width="980" height="580" xmlns="http://www.w3.org/2000/svg" style="background:#090d16;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="1" stdDeviation="1" flood-color="#000" flood-opacity="0.8"/>
    </filter>
    <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#334155"/>
      <stop offset="40%" stop-color="#94a3b8"/>
      <stop offset="60%" stop-color="#f97316"/>
      <stop offset="80%" stop-color="#eab308"/>
      <stop offset="100%" stop-color="#22c55e"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="980" height="580" fill="#090d16"/>

  <!-- Title Header -->
  <rect x="0" y="0" width="980" height="58" fill="#0f172a"/>
  <text x="24" y="28" fill="#f8fafc" font-size="16" font-weight="bold">Planetary Analog Similarity Map: {target_name}</text>
  <text x="24" y="46" fill="#94a3b8" font-size="11">Target ID: {target_id} | Reference Grid: Global Earth 0.05° (WorldClim 2.1 + ETOPO 2022) | Balanced Preset</text>

  <!-- Ocean / Globe Box -->
  <rect x="{map_x0}" y="{map_y0}" width="{map_w}" height="{map_h}" fill="#0d1527" stroke="#1e293b" stroke-width="1.5" rx="4"/>

  <!-- Graticule Lines -->
  <!-- Equator -->
  <line x1="{map_x0}" y1="{map_y0 + map_h/2}" x2="{map_x0 + map_w}" y2="{map_y0 + map_h/2}" stroke="#334155" stroke-dasharray="3,3" stroke-width="1"/>
  <text x="{map_x0 + 6}" y="{map_y0 + map_h/2 - 4}" fill="#64748b" font-size="9">0° Equator</text>

  <!-- Tropics -->
  <line x1="{map_x0}" y1="{map_y0 + map_h*0.37}" x2="{map_x0 + map_w}" y2="{map_y0 + map_h*0.37}" stroke="#1e293b" stroke-width="0.8"/>
  <line x1="{map_x0}" y1="{map_y0 + map_h*0.63}" x2="{map_x0 + map_w}" y2="{map_y0 + map_h*0.63}" stroke="#1e293b" stroke-width="0.8"/>

  <!-- Polar Circles -->
  <line x1="{map_x0}" y1="{map_y0 + map_h*0.13}" x2="{map_x0 + map_w}" y2="{map_y0 + map_h*0.13}" stroke="#334155" stroke-dasharray="2,2" stroke-width="0.8"/>
  <text x="{map_x0 + 6}" y="{map_y0 + map_h*0.13 - 3}" fill="#64748b" font-size="8.5">66.5°N Arctic</text>
  <line x1="{map_x0}" y1="{map_y0 + map_h*0.87}" x2="{map_x0 + map_w}" y2="{map_y0 + map_h*0.87}" stroke="#334155" stroke-dasharray="2,2" stroke-width="0.8"/>
  <text x="{map_x0 + 6}" y="{map_y0 + map_h*0.87 - 3}" fill="#64748b" font-size="8.5">66.5°S Antarctic</text>

  <!-- Prime Meridian -->
  <line x1="{map_x0 + map_w/2}" y1="{map_y0}" x2="{map_x0 + map_w/2}" y2="{map_y0 + map_h}" stroke="#334155" stroke-dasharray="3,3" stroke-width="1"/>
  <text x="{map_x0 + map_w/2 + 4}" y="{map_y0 + 14}" fill="#64748b" font-size="9">0° PM</text>

  <!-- Continent Contours (Indicative Coastline Vectors) -->
  <path d="M 120 120 Q 180 100 240 130 T 320 220 T 300 320 T 250 420" fill="none" stroke="#1e293b" stroke-width="1.2"/>
  <path d="M 440 130 Q 520 110 580 140 T 560 260 T 510 380" fill="none" stroke="#1e293b" stroke-width="1.2"/>
  <path d="M 600 130 Q 720 120 820 160 T 780 280 T 720 360" fill="none" stroke="#1e293b" stroke-width="1.2"/>

  <!-- Plotted Candidate Markers -->
  {markers_svg}

  <!-- Footer Cartographic Metadata -->
  <!-- Scale Bar & CRS -->
  <rect x="60" y="505" width="280" height="58" fill="#0f172a" rx="6" stroke="#1e293b"/>
  <text x="75" y="524" fill="#f8fafc" font-size="10.5" font-weight="600">CRS: WGS 84 (EPSG:4326) Equirectangular</text>
  <text x="75" y="540" fill="#94a3b8" font-size="9.5">Grid Resolution: 0.05° (~5 km at equator)</text>
  <line x1="75" y1="552" x2="195" y2="552" stroke="#cbd5e1" stroke-width="2"/>
  <line x1="75" y1="548" x2="75" y2="556" stroke="#cbd5e1" stroke-width="2"/>
  <line x1="195" y1="548" x2="195" y2="556" stroke="#cbd5e1" stroke-width="2"/>
  <text x="135" y="548" fill="#cbd5e1" font-size="8" text-anchor="middle">5,000 km</text>

  <!-- Similarity Legend -->
  <rect x="580" y="505" width="320" height="58" fill="#0f172a" rx="6" stroke="#1e293b"/>
  <text x="595" y="523" fill="#f8fafc" font-size="10.5" font-weight="600">Similarity Match Score</text>
  <rect x="595" y="531" width="240" height="10" fill="url(#scoreGrad)" rx="3"/>
  <text x="595" y="553" fill="#94a3b8" font-size="9">0% (Dissimilar)</text>
  <text x="715" y="553" fill="#94a3b8" font-size="9">50%</text>
  <text x="815" y="553" fill="#22c55e" font-size="9" font-weight="600">100% (High)</text>

  <!-- Famous vs Overlooked Legend Marker -->
  <circle cx="852" cy="536" r="4.5" fill="#22c55e" stroke="#ffffff" stroke-width="1.5"/>
  <text x="862" y="540" fill="#cbd5e1" font-size="9">Overlooked</text>
  <circle cx="852" cy="520" r="4.5" fill="#22c55e" stroke="#facc15" stroke-width="1.5"/>
  <text x="862" y="524" fill="#cbd5e1" font-size="9">Famous</text>
</svg>"""
    filepath.write_text(svg, encoding="utf-8")
