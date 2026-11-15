#!/usr/bin/env python3
"""Generate 10 vector SVG screenshot figures for TERRATWIN application.

Saves figures directly into docs/figures/.
"""

from pathlib import Path

FIG_DIR = Path(__file__).resolve().parent

def save_svg(filename: str, content: str):
    p = FIG_DIR / filename
    with open(p, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Generated {p.name}")

def gen_01_main_globe():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <defs>
    <radialGradient id="spaceGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.3"/>
      <stop offset="50%" stop-color="#0072ff" stop-opacity="0.15"/>
      <stop offset="100%" stop-color="#070b14" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="globeSphere" cx="40%" cy="40%" r="60%">
      <stop offset="0%" stop-color="#1e3a63"/>
      <stop offset="65%" stop-color="#0d1f38"/>
      <stop offset="100%" stop-color="#050c17"/>
    </radialGradient>
    <filter id="neon">
      <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
      <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>

  <!-- Stars -->
  <g fill="#fff" opacity="0.6">
    <circle cx="80" cy="90" r="1.2"/><circle cx="210" cy="50" r="1.5"/><circle cx="450" cy="110" r="1"/>
    <circle cx="780" cy="80" r="1.5"/><circle cx="920" cy="140" r="1.2"/><circle cx="150" cy="520" r="1"/>
    <circle cx="850" cy="480" r="1.5"/><circle cx="900" cy="350" r="1"/><circle cx="120" cy="300" r="1.2"/>
  </g>

  <!-- Title HUD -->
  <text x="40" y="50" fill="#00f0ff" font-size="20" font-weight="bold" letter-spacing="2">TERRATWIN // 3D INTERACTIVE GLOBE</text>
  <text x="40" y="75" fill="#8ba2c7" font-size="12">Spherical Projection &bull; Orbital Graticule &bull; Real-time Planetary Telemetry</text>

  <!-- Globe Atmosphere Glow -->
  <circle cx="500" cy="320" r="230" fill="url(#spaceGlow)"/>

  <!-- Globe Sphere -->
  <circle cx="500" cy="320" r="180" fill="url(#globeSphere)" stroke="#00f0ff" stroke-width="1.5" stroke-opacity="0.5"/>

  <!-- Graticule Rings -->
  <!-- Parallels -->
  <ellipse cx="500" cy="230" rx="155" ry="32" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.15"/>
  <ellipse cx="500" cy="320" rx="180" ry="38" fill="none" stroke="#ffffff" stroke-width="1" stroke-opacity="0.25"/>
  <ellipse cx="500" cy="410" rx="155" ry="32" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.15"/>

  <!-- Meridians -->
  <path d="M 500 140 C 420 220 420 420 500 500" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.18"/>
  <path d="M 500 140 C 580 220 580 420 500 500" fill="none" stroke="#ffffff" stroke-width="0.8" stroke-opacity="0.18"/>
  <line x1="500" y1="140" x2="500" y2="500" stroke="#00f0ff" stroke-width="0.8" stroke-opacity="0.3"/>

  <!-- Continents Silhouettes -->
  <path d="M 460 210 Q 520 220 510 260 T 470 300 Q 450 280 440 240 Z" fill="#152847" stroke="#00f0ff" stroke-width="0.8" stroke-opacity="0.4"/>
  <path d="M 430 330 Q 480 340 470 410 T 420 450 Q 410 400 420 350 Z" fill="#152847" stroke="#00f0ff" stroke-width="0.8" stroke-opacity="0.4"/>

  <!-- Candidate Analog Pins -->
  <!-- Puna Plateau -->
  <circle cx="440" cy="390" r="14" fill="none" stroke="#00ff88" stroke-width="1.5" stroke-dasharray="2,2"/>
  <circle cx="440" cy="390" r="5" fill="#00ff88" filter="url(#neon)"/>
  <rect x="455" y="380" width="165" height="24" rx="4" fill="#0d1527" stroke="#00ff88" stroke-width="1"/>
  <text x="465" y="396" fill="#fff" font-size="10" font-weight="bold">Puna Plateau [83.1%]</text>

  <!-- McMurdo Dry Valleys -->
  <circle cx="510" cy="475" r="12" fill="none" stroke="#00f0ff" stroke-width="1.5"/>
  <circle cx="510" cy="475" r="4" fill="#00f0ff"/>
  <rect x="525" y="465" width="180" height="24" rx="4" fill="#0d1527" stroke="#00f0ff" stroke-width="1"/>
  <text x="535" y="481" fill="#fff" font-size="10" font-weight="bold">McMurdo Valleys [78.5%]</text>

  <!-- Death Valley -->
  <circle cx="390" cy="270" r="10" fill="none" stroke="#ffaa00" stroke-width="1.5"/>
  <circle cx="390" cy="270" r="4" fill="#ffaa00"/>
  <rect x="250" y="260" width="130" height="24" rx="4" fill="#0d1527" stroke="#ffaa00" stroke-width="1"/>
  <text x="260" y="276" fill="#fff" font-size="10" font-weight="bold">Death Valley [76.5%]</text>

  <!-- HUD Telemetry Box -->
  <rect x="760" y="40" width="200" height="110" rx="6" fill="#0d1527" fill-opacity="0.85" stroke="#00f0ff" stroke-opacity="0.3"/>
  <text x="775" y="65" fill="#00f0ff" font-size="11" font-weight="bold">ORBITAL TELEMETRY</text>
  <text x="775" y="88" fill="#8ba2c7" font-size="10">Target: <tspan fill="#9d4edd">mars_jezero_crater</tspan></text>
  <text x="775" y="108" fill="#8ba2c7" font-size="10">Preset: <tspan fill="#00ff88">balanced_default</tspan></text>
  <text x="775" y="128" fill="#8ba2c7" font-size="10">FOV: <tspan fill="#fff">45° (Orthographic)</tspan></text>
</svg>"""

def gen_02_similarity_heat_layer():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="50" fill="#00f0ff" font-size="20" font-weight="bold" letter-spacing="2">SPATIAL SIMILARITY HEAT LAYER (2D EQUIDISTANT)</text>
  <text x="40" y="75" fill="#8ba2c7" font-size="12">Continuous Percentile-Rank Color Gradient &bull; Preserving Native 0.05° Resolution</text>

  <!-- Map Frame -->
  <rect x="50" y="100" width="900" height="420" rx="8" fill="#0b172a" stroke="#00f0ff" stroke-width="1.2" stroke-opacity="0.4"/>

  <!-- Latitude/Longitude Graticule -->
  <g stroke="#ffffff" stroke-opacity="0.08" stroke-width="1">
    <line x1="50" y1="170" x2="950" y2="170"/><line x1="50" y1="240" x2="950" y2="240"/>
    <line x1="50" y1="310" x2="950" y2="310"/><line x1="50" y1="380" x2="950" y2="380"/>
    <line x1="50" y1="450" x2="950" y2="450"/>
    <line x1="200" y1="100" x2="200" y2="520"/><line x1="350" y1="100" x2="350" y2="520"/>
    <line x1="500" y1="100" x2="500" y2="520"/><line x1="650" y1="100" x2="650" y2="520"/>
    <line x1="800" y1="100" x2="800" y2="520"/>
  </g>

  <!-- Heatmap Halo Envelopes -->
  <!-- Puna Plateau Heat Halo -->
  <circle cx="330" cy="380" r="65" fill="#00ff88" fill-opacity="0.25"/>
  <circle cx="330" cy="380" r="35" fill="#00ff88" fill-opacity="0.4"/>
  <circle cx="330" cy="380" r="6" fill="#00ff88"/>
  <text x="345" y="385" fill="#fff" font-size="11" font-weight="bold">Puna Plateau (83.1%)</text>

  <!-- Qaidam Basin Heat Halo -->
  <circle cx="730" cy="220" r="60" fill="#00ff88" fill-opacity="0.25"/>
  <circle cx="730" cy="220" r="30" fill="#00ff88" fill-opacity="0.4"/>
  <circle cx="730" cy="220" r="6" fill="#00ff88"/>
  <text x="745" y="225" fill="#fff" font-size="11" font-weight="bold">Qaidam Basin (82.8%)</text>

  <!-- McMurdo Dry Valleys Heat Halo -->
  <circle cx="850" cy="480" r="55" fill="#00f0ff" fill-opacity="0.25"/>
  <circle cx="850" cy="480" r="28" fill="#00f0ff" fill-opacity="0.4"/>
  <circle cx="850" cy="480" r="6" fill="#00f0ff"/>
  <text x="690" y="485" fill="#fff" font-size="11" font-weight="bold">McMurdo Valleys (78.5%)</text>

  <!-- Western Desert Heat Halo -->
  <circle cx="570" cy="250" r="50" fill="#00f0ff" fill-opacity="0.25"/>
  <circle cx="570" cy="250" r="5" fill="#00f0ff"/>
  <text x="585" y="255" fill="#fff" font-size="11">Western Desert (78.2%)</text>

  <!-- Death Valley Heat Halo -->
  <circle cx="210" cy="225" r="45" fill="#0072ff" fill-opacity="0.3"/>
  <circle cx="210" cy="225" r="5" fill="#0072ff"/>
  <text x="100" y="230" fill="#fff" font-size="11">Death Valley (76.5%)</text>

  <!-- Heat Legend Footer -->
  <rect x="300" y="545" width="400" height="35" rx="6" fill="#0d1527" stroke="#ffffff" stroke-opacity="0.15"/>
  <defs>
    <linearGradient id="legendGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#070b14"/>
      <stop offset="25%" stop-color="#0072ff"/>
      <stop offset="60%" stop-color="#00f0ff"/>
      <stop offset="85%" stop-color="#00ff88"/>
      <stop offset="100%" stop-color="#ffaa00"/>
    </linearGradient>
  </defs>
  <rect x="360" y="557" width="280" height="10" rx="3" fill="url(#legendGrad)" stroke="#ffffff" stroke-opacity="0.2"/>
  <text x="320" y="566" fill="#8ba2c7" font-size="10">0%</text>
  <text x="655" y="566" fill="#00ff88" font-size="10" font-weight="bold">100%</text>
</svg>"""

def gen_03_moon_south_pole():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">TARGET PROFILE // LUNAR SOUTH POLE</text>
  <text x="40" y="68" fill="#9d4edd" font-size="12" font-weight="bold">Artemis III Base Camp Exploration Zone &bull; Shackleton / de Gerlache Massif</text>

  <!-- Left: Target Geodetic AOI Card -->
  <rect x="40" y="90" width="440" height="470" rx="8" fill="#0d1527" stroke="#9d4edd" stroke-width="1.2"/>
  <text x="60" y="125" fill="#9d4edd" font-size="14" font-weight="bold">Planetary Geodetic Parameters</text>

  <!-- Polar Stereographic Projection Diagram -->
  <circle cx="260" cy="230" r="90" fill="#050a14" stroke="#9d4edd" stroke-width="1.5"/>
  <circle cx="260" cy="230" r="50" fill="none" stroke="#ffffff" stroke-opacity="0.2" stroke-dasharray="3,3"/>
  <circle cx="260" cy="230" r="4" fill="#00f0ff"/>
  <text x="250" y="245" fill="#fff" font-size="9">90°S Pole</text>

  <text x="60" y="355" fill="#8ba2c7" font-size="11">CRS: <tspan fill="#fff">Moon 2015 South Polar Stereographic (R=1737.4 km)</tspan></text>
  <text x="60" y="380" fill="#8ba2c7" font-size="11">AOI Extent: <tspan fill="#fff">Poleward of 85°S (Radius ≤ 151.8 km)</tspan></text>
  <text x="60" y="405" fill="#8ba2c7" font-size="11">Topographic Relief: <tspan fill="#00ff88">3,650 m</tspan> (LOLA LDEM_80S)</text>
  <text x="60" y="430" fill="#8ba2c7" font-size="11">Mean Slope: <tspan fill="#00ff88">9.8°</tspan> (20 km scale)</text>
  <text x="60" y="455" fill="#8ba2c7" font-size="11">Mean Surface Temp: <tspan fill="#00f0ff">-168.15 °C (105 K)</tspan> (Diviner M3)</text>
  <text x="60" y="480" fill="#8ba2c7" font-size="11">Cold Trap Min Temp: <tspan fill="#ff3366">-233.15 °C (40 K)</tspan> (Williams et al.)</text>
  <text x="60" y="505" fill="#8ba2c7" font-size="11">PSR Surface Area: <tspan fill="#fff">15.5%</tspan> (Permanently Shadowed)</text>

  <!-- Right: Ranked Earth Analogue Match Results -->
  <rect x="510" y="90" width="450" height="470" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1.2"/>
  <text x="530" y="125" fill="#00f0ff" font-size="14" font-weight="bold">Ranked Earth Analogues for Moon Target</text>

  <!-- Rank 1 Card -->
  <rect x="530" y="145" width="410" height="90" rx="6" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
  <text x="545" y="170" fill="#00ff88" font-size="12" font-weight="bold">#1 Puna Plateau Volcanic Barren (Argentina)</text>
  <text x="545" y="190" fill="#8ba2c7" font-size="10">Overall Match: <tspan fill="#00ff88" font-weight="bold">81.57%</tspan> [Overlooked Site]</text>
  <text x="545" y="210" fill="#fff" font-size="10">Matches: Hurst fractal roughness (100%), Micro-roughness (99.9%)</text>
  <text x="545" y="225" fill="#ff8800" font-size="9">Limitations: Lacks deep cryo (min -25 °C vs -233 °C)</text>

  <!-- Rank 2 Card -->
  <rect x="530" y="250" width="410" height="90" rx="6" fill="#13203b" stroke="#00f0ff" stroke-width="1"/>
  <text x="545" y="275" fill="#00f0ff" font-size="12" font-weight="bold">#2 Beacon Valley Permafrost (Antarctica)</text>
  <text x="545" y="295" fill="#8ba2c7" font-size="10">Overall Match: <tspan fill="#00f0ff" font-weight="bold">79.81%</tspan> [Overlooked Site]</text>
  <text x="545" y="315" fill="#fff" font-size="10">Matches: Desiccated till over massive ice, Slope (99.4%)</text>
  <text x="545" y="330" fill="#00ff88" font-size="9">Best Mission: Percussive coring drill volatile testing</text>

  <!-- Rank 3 Card -->
  <rect x="530" y="355" width="410" height="90" rx="6" fill="#13203b" stroke="#ffffff" stroke-opacity="0.2"/>
  <text x="545" y="380" fill="#fff" font-size="12" font-weight="bold">#3 McMurdo Dry Valleys (Antarctica)</text>
  <text x="545" y="400" fill="#8ba2c7" font-size="10">Overall Match: <tspan fill="#00ff88" font-weight="bold">78.45%</tspan> [Famous Site]</text>
  <text x="545" y="420" fill="#fff" font-size="10">Matches: Slope (98.2%), Roughness (99.7%), Aridity (95.0%)</text>
  <text x="545" y="435" fill="#00f0ff" font-size="9">Mobility Score: 96.2% (Gold-standard LTV terramechanics)</text>
</svg>"""

def gen_04_mars_jezero():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">TARGET PROFILE // MARS JEZERO CRATER</text>
  <text x="40" y="68" fill="#ffaa00" font-size="12" font-weight="bold">Perseverance Rover Delta Landing Site &bull; Clay-Carbonate-Basalt Lacustrine Basin</text>

  <!-- Left: Jezero Mission Profile -->
  <rect x="40" y="90" width="440" height="470" rx="8" fill="#0d1527" stroke="#ffaa00" stroke-width="1.2"/>
  <text x="60" y="125" fill="#ffaa00" font-size="14" font-weight="bold">Jezero Geological &amp; Thermal Profile</text>

  <!-- Jezero Crater Contour Diagram -->
  <circle cx="260" cy="225" r="85" fill="#1f110b" stroke="#ffaa00" stroke-width="1.5"/>
  <path d="M 180 225 Q 230 200 240 225 Q 250 250 220 250" fill="#ff8800" fill-opacity="0.3" stroke="#ffaa00"/>
  <text x="210" y="220" fill="#fff" font-size="10" font-weight="bold">Neretva Delta</text>

  <text x="60" y="345" fill="#8ba2c7" font-size="11">Location: <tspan fill="#fff">18.38° N, 77.58° E (Isidis Planitia rim)</tspan></text>
  <text x="60" y="370" fill="#8ba2c7" font-size="11">Crater Relief: <tspan fill="#00ff88">1,120 m</tspan> (MOLA MEGDR)</text>
  <text x="60" y="395" fill="#8ba2c7" font-size="11">Floor Slope: <tspan fill="#00ff88">2.8°</tspan> (Navigable delta plain)</text>
  <text x="60" y="420" fill="#8ba2c7" font-size="11">Mean Temp: <tspan fill="#00f0ff">-58.95 °C (214.2 K)</tspan> (Putzig et al.)</text>
  <text x="60" y="445" fill="#8ba2c7" font-size="11">Diurnal Thermal Swing: <tspan fill="#ff8800">78.6 °C</tspan> (Severe thermal fatigue)</text>
  <text x="60" y="470" fill="#8ba2c7" font-size="11">Target Mineralogy: <tspan fill="#fff">Fe/Mg smectite clays, carbonates, olivine</tspan></text>
  <text x="60" y="495" fill="#8ba2c7" font-size="11">Primary Science: <tspan fill="#00ff88">Astrobiology biosignature preservation</tspan></text>

  <!-- Right: Top Jezero Analogues -->
  <rect x="510" y="90" width="450" height="470" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1.2"/>
  <text x="530" y="125" fill="#00f0ff" font-size="14" font-weight="bold">Top Analogues for Jezero Crater</text>

  <!-- Site 1 -->
  <rect x="530" y="145" width="410" height="90" rx="6" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
  <text x="545" y="170" fill="#00ff88" font-size="12" font-weight="bold">#1 Puna Plateau Volcanic Barren (Argentina)</text>
  <text x="545" y="190" fill="#8ba2c7" font-size="10">Similarity Score: <tspan fill="#00ff88" font-weight="bold">83.09%</tspan> [Top Match Worldwide]</text>
  <text x="545" y="210" fill="#fff" font-size="10">Basalt-clay-carbonate lake mineralogy, extreme UV &gt; 25 UVI</text>

  <!-- Site 2 -->
  <rect x="530" y="250" width="410" height="90" rx="6" fill="#13203b" stroke="#00f0ff" stroke-width="1"/>
  <text x="545" y="275" fill="#00f0ff" font-size="12" font-weight="bold">#2 Qaidam Basin Yardangs (China)</text>
  <text x="545" y="295" fill="#8ba2c7" font-size="10">Similarity Score: <tspan fill="#00f0ff" font-weight="bold">79.81%</tspan> [Overlooked Site]</text>
  <text x="545" y="315" fill="#fff" font-size="10">Yardang field corrasion corridors, lacustrine evaporite stratigraphy</text>

  <!-- Site 3 -->
  <rect x="530" y="355" width="410" height="90" rx="6" fill="#13203b" stroke="#ffffff" stroke-opacity="0.2"/>
  <text x="545" y="380" fill="#fff" font-size="12" font-weight="bold">#3 Death Valley Graben (USA)</text>
  <text x="545" y="400" fill="#8ba2c7" font-size="10">Similarity Score: <tspan fill="#00ff88" font-weight="bold">76.50%</tspan> [Mobility: 98.7%]</text>
  <text x="545" y="420" fill="#fff" font-size="10">Alluvial fan grain-size sorting, rover wheel abrasion testbed</text>
</svg>"""

def gen_05_mars_oxia():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">TARGET PROFILE // MARS OXIA PLANUM</text>
  <text x="40" y="68" fill="#00ff88" font-size="12" font-weight="bold">ExoMars Rosalind Franklin Landing Site &bull; Vast Ancient Noachian Clay Plain</text>

  <rect x="40" y="90" width="440" height="470" rx="8" fill="#0d1527" stroke="#00ff88" stroke-width="1.2"/>
  <text x="60" y="125" fill="#00ff88" font-size="14" font-weight="bold">Oxia Planum Plain Morphometry</text>

  <!-- Flat plain diagram -->
  <rect x="100" y="160" width="320" height="130" rx="4" fill="#14261d" stroke="#00ff88" stroke-width="1"/>
  <line x1="100" y1="225" x2="420" y2="225" stroke="#00ff88" stroke-dasharray="4,4"/>
  <text x="210" y="210" fill="#00ff88" font-size="11" font-weight="bold">Flat Noachian Bedrock</text>
  <text x="190" y="245" fill="#8ba2c7" font-size="9">Mean Slope: 1.2° &bull; Relief: 310 m</text>

  <text x="60" y="345" fill="#8ba2c7" font-size="11">Location: <tspan fill="#fff">18.275° N, 335.368° E (East Chryse Planitia)</tspan></text>
  <text x="60" y="370" fill="#8ba2c7" font-size="11">Age: <tspan fill="#fff">Noachian (&gt; 3.9 Ga ancient aqueous era)</tspan></text>
  <text x="60" y="395" fill="#8ba2c7" font-size="11">Slope: <tspan fill="#00ff88">1.2°</tspan> (Exceptionally smooth landing plain)</text>
  <text x="60" y="420" fill="#8ba2c7" font-size="11">Roughness (10 km): <tspan fill="#00ff88">9.5 m</tspan> (Minimal obstacle density)</text>
  <text x="60" y="445" fill="#8ba2c7" font-size="11">Key Deposit: <tspan fill="#00ff88">Hundreds of metres of Fe/Mg smectite clays</tspan></text>
  <text x="60" y="470" fill="#8ba2c7" font-size="11">Mission Tool: <tspan fill="#fff">ExoMars 2-meter subsurface drill</tspan></text>

  <!-- Right: Top Oxia Analogues -->
  <rect x="510" y="90" width="450" height="470" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1.2"/>
  <text x="530" y="125" fill="#00f0ff" font-size="14" font-weight="bold">Top Earth Analogues for Oxia Planum</text>

  <!-- Site 1 -->
  <rect x="530" y="145" width="410" height="90" rx="6" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
  <text x="545" y="170" fill="#00ff88" font-size="12" font-weight="bold">#1 Qaidam Basin Yardangs (China)</text>
  <text x="545" y="190" fill="#8ba2c7" font-size="10">Similarity Score: <tspan fill="#00ff88" font-weight="bold">82.80%</tspan> [Rank #1 Worldwide]</text>
  <text x="545" y="210" fill="#fff" font-size="10">Matches: Slope (99.2%), Flatness (98.8%), Fe/Mg smectite clays</text>
  <text x="545" y="225" fill="#00f0ff" font-size="9">Best Mission: 2-meter drill mechanism qualification in indurated clays</text>

  <!-- Site 2 -->
  <rect x="530" y="250" width="410" height="90" rx="6" fill="#13203b" stroke="#00f0ff" stroke-width="1"/>
  <text x="545" y="275" fill="#00f0ff" font-size="12" font-weight="bold">#2 Western Desert Clay Basin (Egypt)</text>
  <text x="545" y="295" fill="#8ba2c7" font-size="10">Similarity Score: <tspan fill="#00f0ff" font-weight="bold">78.20%</tspan> [Overlooked Site]</text>
  <text x="545" y="315" fill="#fff" font-size="10">Extremely flat shale &amp; mudstone plains (Slope 0.8°, Relief 110 m)</text>
</svg>"""

def gen_06_mission_presets():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">MISSION PRESETS &amp; REAL-TIME WEIGHT TUNING</text>
  <text x="40" y="68" fill="#8ba2c7" font-size="12">Dynamic Weight Recalibration &bull; Instant Multi-Feature Scoring Engine</text>

  <!-- Preset Cards Grid -->
  <g transform="translate(40, 95)">
    <!-- Rover Mobility -->
    <rect x="0" y="0" width="215" height="130" rx="6" fill="#0d1527" stroke="#00ff88" stroke-width="1"/>
    <text x="15" y="28" fill="#00ff88" font-size="12" font-weight="bold">🚜 ROVER MOBILITY</text>
    <text x="15" y="50" fill="#8ba2c7" font-size="10">Terramechanics &amp; Slopes</text>
    <text x="15" y="75" fill="#fff" font-size="10">Slope Weight: <tspan fill="#00ff88">30%</tspan></text>
    <text x="15" y="95" fill="#fff" font-size="10">Roughness (5k/10k): <tspan fill="#00ff88">35%</tspan></text>
    <text x="15" y="115" fill="#fff" font-size="10">Relief: <tspan fill="#00ff88">15%</tspan></text>

    <!-- Cold Trap -->
    <rect x="235" y="0" width="215" height="130" rx="6" fill="#0d1527" stroke="#00f0ff" stroke-width="1"/>
    <text x="250" y="28" fill="#00f0ff" font-size="12" font-weight="bold">❄️ COLD TRAP &amp; ICE</text>
    <text x="250" y="50" fill="#8ba2c7" font-size="10">Cryogenic Volatiles</text>
    <text x="250" y="75" fill="#fff" font-size="10">Min Temp: <tspan fill="#00f0ff">35%</tspan></text>
    <text x="250" y="95" fill="#fff" font-size="10">PSR Area: <tspan fill="#00f0ff">25%</tspan></text>
    <text x="250" y="115" fill="#fff" font-size="10">Mean Temp: <tspan fill="#00f0ff">20%</tspan></text>

    <!-- Thermal Cycling -->
    <rect x="470" y="0" width="215" height="130" rx="6" fill="#0d1527" stroke="#ffaa00" stroke-width="1"/>
    <text x="485" y="28" fill="#ffaa00" font-size="12" font-weight="bold">🌡️ THERMAL CYCLING</text>
    <text x="485" y="50" fill="#8ba2c7" font-size="10">Diurnal Stress Fatigue</text>
    <text x="485" y="75" fill="#fff" font-size="10">Diurnal ΔT: <tspan fill="#ffaa00">35%</tspan></text>
    <text x="485" y="95" fill="#fff" font-size="10">Annual ΔT: <tspan fill="#ffaa00">25%</tspan></text>
    <text x="485" y="115" fill="#fff" font-size="10">Mean Temp: <tspan fill="#ffaa00">20%</tspan></text>

    <!-- Balanced Default -->
    <rect x="705" y="0" width="215" height="130" rx="6" fill="#0d1527" stroke="#9d4edd" stroke-width="1"/>
    <text x="720" y="28" fill="#9d4edd" font-size="12" font-weight="bold">⚖️ BALANCED DEFAULT</text>
    <text x="720" y="50" fill="#8ba2c7" font-size="10">All-Round Analogue</text>
    <text x="720" y="75" fill="#fff" font-size="10">Terrain Group: <tspan fill="#9d4edd">50%</tspan></text>
    <text x="720" y="95" fill="#fff" font-size="10">Thermal Group: <tspan fill="#9d4edd">40%</tspan></text>
    <text x="720" y="115" fill="#fff" font-size="10">Aridity Group: <tspan fill="#9d4edd">10%</tspan></text>
  </g>

  <!-- Interactive Sliders Demonstration Box -->
  <rect x="40" y="255" width="920" height="300" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1"/>
  <text x="60" y="285" fill="#00f0ff" font-size="14" font-weight="bold">Real-Time Weight Sliders (Client-Side Instant Recalculation &lt; 1 ms)</text>

  <!-- Slider 1 -->
  <text x="60" y="325" fill="#fff" font-size="11">Mean Slope Gradient (20km)</text>
  <text x="450" y="325" fill="#00ff88" font-size="11" font-weight="bold">30%</text>
  <rect x="60" y="335" width="400" height="6" rx="3" fill="#1b2a47"/>
  <rect x="60" y="335" width="120" height="6" rx="3" fill="#00ff88"/>
  <circle cx="180" cy="338" r="7" fill="#00ff88"/>

  <!-- Slider 2 -->
  <text x="60" y="380" fill="#fff" font-size="11">High-Pass Roughness (10km)</text>
  <text x="450" y="380" fill="#00ff88" font-size="11" font-weight="bold">20%</text>
  <rect x="60" y="390" width="400" height="6" rx="3" fill="#1b2a47"/>
  <rect x="60" y="390" width="80" height="6" rx="3" fill="#00ff88"/>
  <circle cx="140" cy="393" r="7" fill="#00ff88"/>

  <!-- Slider 3 -->
  <text x="520" y="325" fill="#fff" font-size="11">Diurnal Temperature Swing</text>
  <text x="910" y="325" fill="#ffaa00" font-size="11" font-weight="bold">35%</text>
  <rect x="520" y="335" width="400" height="6" rx="3" fill="#1b2a47"/>
  <rect x="520" y="335" width="140" height="6" rx="3" fill="#ffaa00"/>
  <circle cx="660" cy="338" r="7" fill="#ffaa00"/>

  <!-- Slider 4 -->
  <text x="520" y="380" fill="#fff" font-size="11">Minimum Cold-Extreme Temperature</text>
  <text x="910" y="380" fill="#00f0ff" font-size="11" font-weight="bold">35%</text>
  <rect x="520" y="390" width="400" height="6" rx="3" fill="#1b2a47"/>
  <rect x="520" y="390" width="140" height="6" rx="3" fill="#00f0ff"/>
  <circle cx="660" cy="393" r="7" fill="#00f0ff"/>
</svg>"""

def gen_07_comparison_radar():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">MULTI-AXIS RADAR COMPARISON: EARTH ANALOGUE VS PLANETARY TARGET</text>
  <text x="40" y="68" fill="#8ba2c7" font-size="12">Puna Plateau Volcanic Barren (Earth) vs Mars Jezero Crater</text>

  <!-- Left: Radar Chart Canvas -->
  <g transform="translate(280, 310)">
    <!-- Web Rings -->
    <polygon points="0,-160 138,-80 138,80 0,160 -138,80 -138,-80" fill="none" stroke="#ffffff" stroke-opacity="0.1" stroke-width="1"/>
    <polygon points="0,-120 104,-60 104,60 0,120 -104,60 -104,-60" fill="none" stroke="#ffffff" stroke-opacity="0.1" stroke-width="1"/>
    <polygon points="0,-80 69,-40 69,40 0,80 -69,40 -69,-40" fill="none" stroke="#ffffff" stroke-opacity="0.1" stroke-width="1"/>
    <polygon points="0,-40 35,-20 35,20 0,40 -35,20 -35,-20" fill="none" stroke="#ffffff" stroke-opacity="0.1" stroke-width="1"/>

    <!-- Spokes -->
    <line x1="0" y1="0" x2="0" y2="-160" stroke="#ffffff" stroke-opacity="0.2"/>
    <line x1="0" y1="0" x2="138" y2="-80" stroke="#ffffff" stroke-opacity="0.2"/>
    <line x1="0" y1="0" x2="138" y2="80" stroke="#ffffff" stroke-opacity="0.2"/>
    <line x1="0" y1="0" x2="0" y2="160" stroke="#ffffff" stroke-opacity="0.2"/>
    <line x1="0" y1="0" x2="-138" y2="80" stroke="#ffffff" stroke-opacity="0.2"/>
    <line x1="0" y1="0" x2="-138" y2="-80" stroke="#ffffff" stroke-opacity="0.2"/>

    <!-- Axis Labels -->
    <text x="0" y="-175" fill="#8ba2c7" font-size="11" text-anchor="middle">Slope (20km)</text>
    <text x="155" y="-85" fill="#8ba2c7" font-size="11" text-anchor="start">Roughness (10km)</text>
    <text x="155" y="90" fill="#8ba2c7" font-size="11" text-anchor="start">Relief (20km)</text>
    <text x="0" y="180" fill="#8ba2c7" font-size="11" text-anchor="middle">Hurst Exponent</text>
    <text x="-155" y="90" fill="#8ba2c7" font-size="11" text-anchor="end">Diurnal ΔT</text>
    <text x="-155" y="-85" fill="#8ba2c7" font-size="11" text-anchor="end">Mean Temp</text>

    <!-- Target Polygon (Mars Jezero - Purple) -->
    <polygon points="0,-85 110,-60 90,50 0,135 -110,60 -60,-35" fill="#9d4edd" fill-opacity="0.25" stroke="#9d4edd" stroke-width="2"/>

    <!-- Earth Site Polygon (Puna Plateau - Cyan) -->
    <polygon points="0,-90 115,-65 85,45 0,138 -95,50 -30,-15" fill="#00f0ff" fill-opacity="0.3" stroke="#00f0ff" stroke-width="2.5"/>
  </g>

  <!-- Right: Quantitative Comparison Matrix -->
  <rect x="580" y="100" width="380" height="460" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1"/>
  <text x="605" y="135" fill="#00f0ff" font-size="14" font-weight="bold">Feature Comparison Matrix</text>

  <g transform="translate(605, 160)" font-size="11">
    <text x="0" y="0" fill="#8ba2c7">FEATURE</text><text x="150" y="0" fill="#9d4edd">MARS JEZERO</text><text x="260" y="0" fill="#00f0ff">PUNA (EARTH)</text>
    <line x1="0" y1="8" x2="330" y2="8" stroke="#ffffff" stroke-opacity="0.15"/>

    <text x="0" y="35" fill="#fff">Slope (20km)</text><text x="150" y="35" fill="#9d4edd">2.8°</text><text x="260" y="35" fill="#00ff88">3.1° (99%)</text>
    <text x="0" y="65" fill="#fff">Roughness (10km)</text><text x="150" y="65" fill="#9d4edd">24.5 m</text><text x="260" y="65" fill="#00ff88">28.5 m (99%)</text>
    <text x="0" y="95" fill="#fff">Local Relief</text><text x="150" y="95" fill="#9d4edd">1,120 m</text><text x="260" y="95" fill="#00ff88">980 m (98%)</text>
    <text x="0" y="125" fill="#fff">Hurst Exponent</text><text x="150" y="125" fill="#9d4edd">0.78</text><text x="260" y="125" fill="#00ff88">0.82 (100%)</text>
    <text x="0" y="155" fill="#fff">Diurnal ΔT</text><text x="150" y="155" fill="#9d4edd">78.6 °C</text><text x="260" y="155" fill="#ffaa00">24.5 °C (80%)</text>
    <text x="0" y="185" fill="#fff">Mean Temp</text><text x="150" y="155" fill="#9d4edd">-59.0 °C</text><text x="260" y="185" fill="#ff3366">+4.2 °C (42%)</text>
  </g>
</svg>"""

def gen_08_top_site_detail():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#00f0ff" font-size="18" font-weight="bold">TOP-SITE DETAILED EXPLORATION DOSSIER</text>
  <text x="40" y="68" fill="#00ff88" font-size="12" font-weight="bold">Puna Plateau Volcanic Barren (Catamarca &amp; Salta, Argentina) &bull; Coordinates: -24.8°, -67.2°</text>

  <!-- Left: Mission Suitability Checklist -->
  <rect x="40" y="95" width="440" height="465" rx="8" fill="#0d1527" stroke="#00ff88" stroke-width="1.2"/>
  <text x="60" y="130" fill="#00ff88" font-size="14" font-weight="bold">Mission Exploration Suitability</text>

  <g transform="translate(60, 160)" font-size="11">
    <text x="0" y="0" fill="#00ff88" font-weight="bold">✓ Rover Mobility &amp; Terramechanics</text>
    <text x="15" y="18" fill="#8ba2c7">Basaltic lava blocks, cinder plains, and steep volcanic scree.</text>

    <text x="0" y="55" fill="#00ff88" font-weight="bold">✓ Astrobiology Biosignature Detection (SHERLOC / PIXL)</text>
    <text x="15" y="73" fill="#8ba2c7">Alkaline stromatolitic paleolakes with clay-carbonate-smectites.</text>

    <text x="0" y="110" fill="#00ff88" font-weight="bold">✓ High-UV Solar Degradation Testing</text>
    <text x="15" y="128" fill="#8ba2c7">UV index &gt; 25 UVI at 4,200m elevation tests optical degradation.</text>

    <text x="0" y="165" fill="#00ff88" font-weight="bold">✓ Extreme Diurnal Thermal Cycling</text>
    <text x="15" y="183" fill="#8ba2c7">Diurnal swings &gt; 30 °C stress avionics and battery cycles.</text>

    <text x="0" y="220" fill="#ffaa00" font-weight="bold">! Hypoxic EVA Crew Stress Simulation</text>
    <text x="15" y="238" fill="#8ba2c7">Low pressure (60 kPa) tests human cardiovascular fatigue.</text>
  </g>

  <!-- Right: Target Geochemistry & Surface Comparison -->
  <rect x="510" y="95" width="450" height="465" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1.2"/>
  <text x="530" y="130" fill="#00f0ff" font-size="14" font-weight="bold">Analogue Mineralogy vs Mars Jezero</text>

  <g transform="translate(530, 160)" font-size="11">
    <text x="0" y="0" fill="#fff" font-weight="bold">1. Clay-Carbonate-Basalt Triad:</text>
    <text x="0" y="18" fill="#8ba2c7">Matches Perseverance's primary target formation in Jezero delta.</text>

    <text x="0" y="50" fill="#fff" font-weight="bold">2. Lacustrine Evaporites:</text>
    <text x="0" y="68" fill="#8ba2c7">Halite, gypsum, and borate salts preserve ancient cellular structures.</text>

    <text x="0" y="100" fill="#fff" font-weight="bold">3. Physical Weathering Dominance:</text>
    <text x="0" y="118" fill="#8ba2c7">Hyper-arid conditions prevent chemical hydration alteration.</text>

    <rect x="0" y="150" width="410" height="90" rx="6" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
    <text x="15" y="175" fill="#00ff88" font-size="12" font-weight="bold">OVERALL SCIENTIFIC VERDICT</text>
    <text x="15" y="195" fill="#fff" font-size="10">High-Fidelity Planetary Analog: Recommended for primary end-to-end</text>
    <text x="15" y="212" fill="#fff" font-size="10">Mars rover mobility, biosignature detection, and thermal trials.</text>
  </g>
</svg>"""

def gen_09_analogy_breakdown():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <text x="40" y="45" fill="#ff8800" font-size="18" font-weight="bold">⚠️ WHERE THE ANALOGY BREAKS DOWN: UNREPLICABLE PLANETARY PHYSICS</text>
  <text x="40" y="68" fill="#8ba2c7" font-size="12">Essential Scientific Guardrails &bull; Fundamental Environmental Disparities That Earth Cannot Replicate</text>

  <!-- 4 Primary Physical Breakdown Cards -->
  <g transform="translate(40, 95)">
    <!-- 1. Gravity -->
    <rect x="0" y="0" width="440" height="105" rx="6" fill="#0d1527" stroke="#ff8800" stroke-width="1.2"/>
    <text x="15" y="24" fill="#ff8800" font-size="12" font-weight="bold">1. SURFACE GRAVITY DISPARITY</text>
    <text x="350" y="24" fill="#ff8800" font-size="10" font-weight="bold">[PHYSICAL LIMIT]</text>
    <text x="15" y="45" fill="#8ba2c7" font-size="10">Earth: 1.00 g (9.81 m/s²) &bull; Moon: 0.166 g (~1/6 g) &bull; Mars: 0.376 g (~3/8 g)</text>
    <text x="15" y="65" fill="#fff" font-size="10">Scientific Consequence: Rover tractive force, wheel sinkage in regolith, slope</text>
    <text x="15" y="80" fill="#fff" font-size="10">stability, and human locomotion fatigue operate under completely different physics.</text>

    <!-- 2. Atmosphere -->
    <rect x="470" y="0" width="440" height="105" rx="6" fill="#0d1527" stroke="#ff8800" stroke-width="1.2"/>
    <text x="485" y="24" fill="#ff8800" font-size="12" font-weight="bold">2. ATMOSPHERIC PRESSURE &amp; VACUUM</text>
    <text x="820" y="24" fill="#ff8800" font-size="10" font-weight="bold">[PHYSICAL LIMIT]</text>
    <text x="485" y="45" fill="#8ba2c7" font-size="10">Earth: 101.3 kPa (N₂/O₂) &bull; Moon: &lt;10⁻¹⁰ Pa (Vacuum) &bull; Mars: 0.6 kPa (Thin CO₂)</text>
    <text x="485" y="65" fill="#fff" font-size="10">Scientific Consequence: No aerodynamic drag on Moon; pure radiative thermal</text>
    <text x="485" y="80" fill="#fff" font-size="10">cooling; liquid water boils and sublimates immediately on planetary surfaces.</text>

    <!-- 3. Radiation -->
    <rect x="0" y="125" width="440" height="105" rx="6" fill="#0d1527" stroke="#ff3366" stroke-width="1.2"/>
    <text x="15" y="149" fill="#ff3366" font-size="12" font-weight="bold">3. COSMIC &amp; SOLAR PARTICLE RADIATION</text>
    <text x="350" y="149" fill="#ff3366" font-size="10" font-weight="bold">[PHYSICAL LIMIT]</text>
    <text x="15" y="170" fill="#8ba2c7" font-size="10">Earth: ~2.4 mSv/yr (Protected) &bull; Moon/Mars: 300 to 1,100 mSv/yr (Unshielded GCR+SPE)</text>
    <text x="15" y="190" fill="#fff" font-size="10">Scientific Consequence: Rapid single-event electronic latchups; solar array</text>
    <text x="15" y="205" fill="#fff" font-size="10">browning; lethal cumulative biological DNA damage for crewed operations.</text>

    <!-- 4. Regolith Chemistry -->
    <rect x="470" y="125" width="440" height="105" rx="6" fill="#0d1527" stroke="#ff3366" stroke-width="1.2"/>
    <text x="485" y="149" fill="#ff3366" font-size="12" font-weight="bold">4. REGOLITH SHARPNESS &amp; PERCHLORATES</text>
    <text x="810" y="149" fill="#ff3366" font-size="10" font-weight="bold">[MEASURED MISMATCH]</text>
    <text x="485" y="170" fill="#8ba2c7" font-size="10">Earth: Weathered rounded sands &bull; Moon/Mars: Sub-micron jagged glass + ClO₄⁻</text>
    <text x="485" y="190" fill="#fff" font-size="10">Scientific Consequence: Extreme mechanical seal wear; electrostatic clinging;</text>
    <text x="485" y="205" fill="#fff" font-size="10">toxic thyroid disruption from perchlorates; severe space suit fabric abrasion.</text>
  </g>

  <!-- Summary Box -->
  <rect x="40" y="355" width="910" height="190" rx="8" fill="#141a29" stroke="#ffffff" stroke-opacity="0.15"/>
  <text x="60" y="385" fill="#00f0ff" font-size="14" font-weight="bold">Scientific Integrity Commitment</text>
  <text x="60" y="415" fill="#fff" font-size="11">TERRATWIN explicitly prohibits claiming environmental equivalence based solely on mathematical similarity scores.</text>
  <text x="60" y="435" fill="#8ba2c7" font-size="11">Terrestrial analogues are valid exclusively for specific subsystem tests (e.g., rover chassis suspension, autonomous navigation,</text>
  <text x="60" y="455" fill="#8ba2c7" font-size="11">drill torque, or UV sensor coating degradation). System-level mission architectures must incorporate testing under simulated</text>
  <text x="60" y="475" fill="#8ba2c7" font-size="11">vacuum and thermal-radiation chambers.</text>
</svg>"""

def gen_10_full_app_overview():
    return """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 600" width="1000" height="600" style="background:#070b14; font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
  <!-- Header HUD -->
  <rect x="15" y="12" width="970" height="50" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="1.2"/>
  <text x="35" y="42" fill="#00f0ff" font-size="16" font-weight="bold" letter-spacing="1">TERRATWIN // PLANETARY ANALOGUE EXPLORER</text>
  <rect x="440" y="22" width="220" height="30" rx="5" fill="#13203b" stroke="#9d4edd" stroke-width="1"/>
  <text x="460" y="42" fill="#fff" font-size="11">🌕 Moon South Pole</text>
  <rect x="680" y="22" width="160" height="30" rx="5" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
  <text x="700" y="42" fill="#00ff88" font-size="11">⚖️ Balanced Default</text>

  <!-- Left Sidebar: Ranked Candidate Cards -->
  <rect x="15" y="75" width="260" height="475" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="0.8"/>
  <text x="30" y="105" fill="#00f0ff" font-size="12" font-weight="bold">TOP EARTH ANALOGUES (15)</text>

  <rect x="25" y="125" width="240" height="65" rx="6" fill="#13203b" stroke="#00ff88" stroke-width="1"/>
  <text x="35" y="145" fill="#00ff88" font-size="11" font-weight="bold">#1 Puna Plateau (81.6%)</text>
  <text x="35" y="162" fill="#8ba2c7" font-size="9">Argentina &bull; Overlooked Site</text>

  <rect x="25" y="200" width="240" height="65" rx="6" fill="#13203b" stroke="#00f0ff" stroke-width="1"/>
  <text x="35" y="220" fill="#00f0ff" font-size="11" font-weight="bold">#2 Beacon Valley (79.8%)</text>
  <text x="35" y="237" fill="#8ba2c7" font-size="9">Antarctica &bull; Overlooked Site</text>

  <rect x="25" y="275" width="240" height="65" rx="6" fill="#13203b" stroke="#ffffff" stroke-opacity="0.2"/>
  <text x="35" y="295" fill="#fff" font-size="11" font-weight="bold">#3 McMurdo Valleys (78.5%)</text>
  <text x="35" y="312" fill="#8ba2c7" font-size="9">Antarctica &bull; Famous Site</text>

  <!-- Center: 3D Globe & Heat Layer -->
  <rect x="290" y="75" width="420" height="475" rx="8" fill="#050a14" stroke="#ffffff" stroke-opacity="0.15"/>
  <circle cx="500" cy="312" r="140" fill="#0d1d36" stroke="#00f0ff" stroke-width="1"/>
  <circle cx="500" cy="312" r="140" fill="none" stroke="#00f0ff" stroke-opacity="0.3"/>
  <ellipse cx="500" cy="312" rx="140" ry="30" fill="none" stroke="#ffffff" stroke-opacity="0.2"/>
  <circle cx="470" cy="360" r="12" fill="none" stroke="#00ff88" stroke-width="1.5"/>
  <circle cx="470" cy="360" r="4" fill="#00ff88"/>
  <text x="490" y="365" fill="#00ff88" font-size="10" font-weight="bold">Puna Plateau</text>

  <!-- Right Sidebar: Comparison & Analytics HUD -->
  <rect x="725" y="75" width="260" height="475" rx="8" fill="#0d1527" stroke="#00f0ff" stroke-width="0.8"/>
  <text x="740" y="105" fill="#00f0ff" font-size="12" font-weight="bold">COMPARISON &amp; ANALYTICS</text>
  <circle cx="855" cy="190" r="60" fill="none" stroke="#ffffff" stroke-opacity="0.1"/>
  <polygon points="855,140 895,170 885,220 825,220 815,170" fill="#00f0ff" fill-opacity="0.3" stroke="#00f0ff"/>
  <text x="740" y="280" fill="#ffaa00" font-size="11" font-weight="bold">⚠️ UNREPLICABLE PHYSICS</text>
  <text x="740" y="300" fill="#8ba2c7" font-size="9">&bull; Gravity: 1/6 g (Moon) vs 1.0 g</text>
  <text x="740" y="315" fill="#8ba2c7" font-size="9">&bull; Pressure: Vacuum (&lt;10⁻¹⁰ Pa)</text>
  <text x="740" y="330" fill="#8ba2c7" font-size="9">&bull; Radiation: 380 mSv/yr GCR+SPE</text>

  <!-- Footer HUD -->
  <rect x="15" y="558" width="970" height="32" rx="6" fill="#0d1527" stroke="#ffffff" stroke-opacity="0.1"/>
  <text x="35" y="579" fill="#8ba2c7" font-size="10">Telemetry: <tspan fill="#00ff88">All Systems Nominal</tspan> &bull; Engine Latency: <tspan fill="#00f0ff">0.8 ms</tspan> &bull; Active Targets: 3 &bull; Candidate Sites: 15</text>
</svg>"""

def main():
    save_svg("01_main_globe.svg", gen_01_main_globe())
    save_svg("02_similarity_heat_layer.svg", gen_02_similarity_heat_layer())
    save_svg("03_moon_south_pole_view.svg", gen_03_moon_south_pole())
    save_svg("04_mars_jezero_view.svg", gen_04_mars_jezero())
    save_svg("05_mars_oxia_view.svg", gen_05_mars_oxia())
    save_svg("06_mission_presets.svg", gen_06_mission_presets())
    save_svg("07_comparison_radar.svg", gen_07_comparison_radar())
    save_svg("08_top_site_detail.svg", gen_08_top_site_detail())
    save_svg("09_analogy_breakdown.svg", gen_09_analogy_breakdown())
    save_svg("10_full_app_overview.svg", gen_10_full_app_overview())
    print("All 10 vector SVG screenshot figures generated successfully!")

if __name__ == "__main__":
    main()
