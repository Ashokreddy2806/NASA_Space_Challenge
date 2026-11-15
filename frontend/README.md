# TerraTwin — Planetary Analogue Explorer
**Interactive Spatial Geospatial Platform | NASA Space Apps Challenge 2026**

---

## Overview

**TerraTwin** is a mission-control grade interactive spatial exploration platform comparing Moon and Mars landing sites with Earth terrestrial analogues.

The Earth map is the central element of the application (occupying ~70% of the screen). Built with Leaflet, CartoDB Dark Matter / Esri Satellite tile cartography, dynamic glowing markers, real-time spatial heat halos, and instant client-side Mahalanobis similarity scoring.

---

## Key Features

1. **Map-First Visual Hierarchy (70% Screen Area):**
   - Full interactive cartography: Zoom, pan, rotate, and reset to global view.
   - Dual tile layers: **CartoDB Dark Matter** and **Esri World Imagery (Satellite)** with full attribution.
   - 24 verified Earth analogue locations plotted at their exact coordinates.
   - Custom glowing, pulsating SVG marker pins color-coded by real similarity scores.
2. **Dynamic Continuous Similarity Heatmap:**
   - Spatial heat halos projected over Earth coordinates tinted by real calculated scores.
   - Green/Cyan for High ($\ge 75\%$), Yellow for Medium ($60\% - 74.9\%$), Orange for Low ($< 60\%$), and Slate Grey for Missing/Uncalculated ($< 40\%$ quality).
   - **Zero fake 50% scores:** Missing values are recorded as honest `N/A` states.
3. **Planetary Target Selector (Top Floating HUD):**
   - **Moon South Pole** (Artemis III Base Camp, Shackleton/de Gerlache rims, 13 features).
   - **Mars Jezero Crater** (Perseverance rover delta, clay-carbonate-basalt basin, 13 features).
   - **Mars Oxia Planum** (ExoMars Rosalind Franklin landing site, flat Noachian clay plain, 13 features).
4. **Mission Presets & Weight Tuning:**
   - 4 Presets: **Balanced Default**, **Rover Mobility**, **Cold Trap & Ice**, and **Thermal Cycling**.
   - 8 interactive weight calibration sliders with live recalculation in $<1\text{ ms}$.
5. **Multi-Axis Radar Comparison HUD:**
   - Interactive Canvas Radar Chart comparing Earth candidate vs Target across 6 key metrics.
   - Scientific matrix table showing target value, Earth value, diff, and match subscore.
6. **"Where the Analogy Breaks Down" Panel:**
   - Evidence-based scientific limitation dashboard detailing unreplicable physics:
     * Surface Gravity ($0.166\text{ g}$ Moon / $0.376\text{ g}$ Mars vs $1.00\text{ g}$ Earth).
     * Atmospheric Vacuum / Thin $\text{CO}_2$ ($<10^{-10}\text{ Pa}$ / $0.6\text{ kPa}$ vs $101.3\text{ kPa}$).
     * Radiation ($300-1100\text{ mSv/yr}$ vs $2.4\text{ mSv/yr}$).
     * Regolith Sharpness & Toxic Perchlorates ($\text{ClO}_4^-$).
     * Cryogenic Cold Traps ($40\text{ K}$).
7. **Search, Filter & Scientific Discovery Mode:**
   - Search by name, country, region.
   - Filter by continent, environment type, and validation status (`Validated Analogue` vs `Candidate Region`).
   - Discovery Mode toggle: Surfacing high-fidelity overlooked candidates (e.g., Puna Plateau, Qaidam Basin, Beacon Valley).

---

## How to Run

### Option A: Direct Browser Launch (Zero Setup)
Open [index.html](index.html) directly in any modern browser:
```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html
```

### Option B: Python REST API Server
To enable live backend API endpoints (`/api/targets`, `/api/similarity/recalculate`):
```bash
python3 frontend/server.py 8080
```
Navigate to: `http://localhost:8080/`

---

## Test Verification

Run the automated test suite verifying all 24 candidates and endpoints:
```bash
python3 -m unittest frontend/tests/test_api.py
```
Expected result:
```
Ran 7 tests in 0.002s
OK
```
