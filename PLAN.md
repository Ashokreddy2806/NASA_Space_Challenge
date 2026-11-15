# Plan

> Living document. Update it whenever a task starts, finishes, gets blocked, or a decision is made.
> Problem definition: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) · What happened: [PROGRESS_LOG.md](PROGRESS_LOG.md) · Rules for AI assistants: [AGENTS.md](AGENTS.md)

**Last updated:** 2026-11-15 10:55 by mrinalini

---

## 1. Goal

Build a Python-backed tool that **ranks every place on Earth by similarity to a lunar or Martian target site**, explains each match feature by feature (what matches, how closely, what doesn't), connects top sites to exploration use cases, and presents it all in a **visually impressive interactive map**.

Targets (each teammate will focus on one part; parts are **not assigned yet**):
- **Moon:** lunar south pole (permanent Moon base candidate region; permanently shadowed regions / cold traps, ice).
- **Mars:** a landing / exploration site (e.g. Jezero Crater; final choice is an open decision).

## 2. Approach

1. **Common feature space.** Pick a small set of features that can be measured on Earth *and* on the target body (e.g. surface temperature stats, slope, roughness, elevation range, albedo, hydrogen/ice proxy, mineral proxy, dryness, vegetation = 0).
2. **Global Earth grid.** Resample each Earth dataset to one common coarse grid (~0.05°, ≈5 km). Store as one `xarray` dataset / Zarr or NetCDF.
3. **Target profiles.** For each target site, compute the same features from Moon/Mars data → one feature vector (plus value ranges).
4. **Similarity engine.** Normalize features, compute weighted distance per Earth cell → overall score + per-feature sub-scores. User-adjustable weights (e.g. "geology only", "thermal only").
5. **Zoom in.** Take the top N candidates, filter out famous sites (Atacama, Antarctica Dry Valleys, Iceland, Hawaii, Devon Island, Death Valley) to surface **overlooked** sites, pull higher-res data for a few.
6. **Explain.** For each top site: matching features, mismatches, exploration use (instrument testing, crew training, resource prospecting, astrobiology, risk reduction), and what Earth **cannot** replicate (gravity, vacuum / thin atmosphere, radiation).
7. **Visualize.** Interactive map + site cards + side-by-side Earth vs. target comparison.

## 3. Architecture (proposed — confirm in Decisions)

```
data/raw/          downloaded source files (git-ignored)
data/processed/    gridded features, target profiles (git-ignored if large)
backend/           Python: data pipeline, similarity engine, API
  pipeline/        download + regrid scripts, one per dataset
  engine/          feature normalization, scoring, ranking
  api/             FastAPI app serving scores, tiles, site details
frontend/          visualization (map, site cards, comparisons)
notebooks/         exploration only; anything reused moves into backend/
docs/              write-up, figures, submission material
```

- **Backend:** Python (xarray, rioxarray/rasterio, numpy, pandas, scikit-learn) + **FastAPI**.
- **Frontend (proposed, not decided):** a polished web map — e.g. **deck.gl + MapLibre** (3D globe, heatmap layer of similarity scores, clickable sites) with **Plotly** radar/bar charts for feature comparisons. Alternative: Streamlit + pydeck (faster, less polished).

## 4. Candidate datasets (pick, then record choice in Decisions)

### Earth
| Feature | Candidate product | Notes |
|---|---|---|
| Surface temperature (mean, min, max, range) | MODIS LST, MOD11C3 (monthly, 0.05° CMG) | Already global coarse grid |
| Elevation, slope, roughness | SRTM / Copernicus DEM / GMTED2010 | Derive slope + roughness at coarse scale |
| Minerals / surface composition | ASTER GED (emissivity), EMIT minerals | EMIT covers arid regions only (~±52° lat) |
| Soil moisture / dryness | SMAP L3/L4 | ~9–36 km |
| Vegetation (should be ~0) | MODIS NDVI, MOD13C2 | Mask out vegetated cells |
| Snow / ice / permafrost | MODIS snow cover, ESA CCI Permafrost | Ice analog for lunar cold traps |
| Dust | MERRA-2 aerosol / dust | For Mars dust analogs |
| Precipitation | GPM IMERG or JAXA GSMaP | Dryness proxy |
| Radar texture (single site only) | Sentinel-1 / RADARSAT | Too heavy for global search |

### Moon (lunar south pole)
| Feature | Product |
|---|---|
| Elevation, slope, roughness | LRO LOLA polar DEMs |
| Surface temperature | LRO Diviner polar temperature products (max/avg) |
| Ice / hydrogen proxy | LRO LEND, Lunar Prospector neutron data |
| Radar texture | LRO Mini-RF CPR |
| Illumination | LOLA-derived illumination maps |

### Mars (site TBD, e.g. Jezero)
| Feature | Product |
|---|---|
| Elevation, slope, roughness | MOLA / HRSC-MOLA blended DEM |
| Thermal inertia, temperature | MGS TES, Mars Odyssey THEMIS, Mars Climate Database |
| Minerals | MRO CRISM, TES mineral maps |
| Ice / hydrogen | Mars Odyssey GRS/NS |
| Dust | TES dust cover index |

## 5. Workstreams (unassigned — claim one by writing your name in `Owner`)

| # | Workstream | Owner | Status |
|---|---|---|---|
| W1 | Repo setup: folders, `requirements.txt`/env, `.gitignore`, README | — | done |
| W2 | Earth data pipeline: download + regrid to common global grid | — | done |
| W3 | Moon target profile (lunar south pole features) | mrinalini | done |
| W4 | Mars target profile (choose site + features) | mrinalini | done |
| W5 | Similarity engine: normalization, weights, scores, per-feature breakdown | mrinalini | done |
| W6 | Backend API (FastAPI / Standard HTTP) serving scores and site details | mrinalini | done |
| W7 | Frontend visualization (map, site cards, comparison charts) | mrinalini | done |
| W8 | Top-site analysis + write-up (matches, mismatches, exploration use, Earth's limits) | mrinalini | done |
| W9 | Submission: demo video, slides, final README | — | in progress |

Status values: `not started` · `in progress` · `blocked` · `done`

## 6. Timeline (~24 h)

| Hours | Milestone | Done? |
|---|---|---|
| 0–2 | Repo + env set up, datasets chosen, feature list agreed | [ ] |
| 2–8 | Earth grid built for core features; Moon + Mars target vectors computed | [ ] |
| 8–13 | Similarity engine produces a global score map for each target | [ ] |
| 13–19 | API + visualization working end-to-end; top sites identified | [ ] |
| 19–22 | Site write-ups, polish visuals, "overlooked site" story | [ ] |
| 22–24 | Demo video, slides, submit | [ ] |

## 7. Decisions log

Append newest at the bottom. Format: `YYYY-MM-DD HH:MM — <name> — decision — why`

- 2026-11-14 — rahul — Python backend; visuals must be high quality — judges see the visualization first.
- 2026-11-14 — rahul — Coarse global grid (~5 km) for search, high-res only for top candidates — 8 GB RAM Macs.
- 2026-11-14 — rahul — Each teammate will focus on one part; parts not assigned yet.
- 2026-11-14 16:42 — mrinalini — Selected Oxia Planum (18.28°N, 335.37°E) as primary Mars target, with Jezero Crater as comparative benchmark — Oxia Planum's extensive Noachian clay sheet (~4.0 Ga) matches a 5 km grid without sub-pixel blurring and captures Mars' earliest habitable epoch.

- 2026-11-14 16:42 — mrinalini — Selected Oxia Planum (18.28°N, 335.37°E) as primary Mars target, with Jezero Crater as comparative benchmark — Oxia Planum's extensive Noachian clay sheet (~4.0 Ga) matches a 5 km grid without sub-pixel blurring and captures Mars' earliest habitable epoch.
- 2026-11-15 10:40 — mrinalini — Rebuilt clean Phase 2 & 3 scientific engine (Moon South Pole, Mars Jezero, Mars Oxia Planum target profiles and Mahalanobis/Percentile similarity engine) in `scientific_engine/` with 100% test coverage.
- 2026-11-15 10:55 — mrinalini — Built TERRATWIN interactive spatial exploration platform (Phase 5 frontend + Phase 6 top-site analysis) with standalone 3D globe / 2D map, dynamic weight tuning, and evidence-based "Where the Analogy Breaks Down" guardrails.

## 8. Open questions

- [x] Which Mars site is the target (Jezero? another)? -> Oxia Planum chosen as primary, Jezero Crater as benchmark.
- [x] Frontend: deck.gl + MapLibre vs Streamlit + pydeck vs something else? -> Built TERRATWIN interactive 3D WebGL/Canvas Globe & 2D Equirectangular map with standalone zero-dependency offline mode and standard Python REST API.
- [x] Final feature list per target (which features exist on both Earth and the target body?). -> 13 instrument-verified features spanning relief, slope, roughness (5/10/20 km), Hurst exponent, mean/diurnal/annual temperature, coldest minimum, and precipitation.
- [x] How to weight features, and should users be able to change weights in the UI? -> Implemented 4 presets (Rover Mobility, Cold-Trap & Ice, Thermal Cycling, Balanced Default) and 8 real-time interactive weight sliders with < 1 ms recalculation.
- [x] Who owns which workstream? -> mrinalini completed W3, W4, W5, W6, W7, W8.

## 9. Frontend and Top-Site Analysis (TERRATWIN Platform)

### 9.1 Frontend Architecture
- **Application Name:** **TERRATWIN — Planetary Analogue Explorer** ("Explore Earth. Understand Other Worlds.")
- **Design Aesthetic:** NASA Mission Control styling, deep navy space backdrop (`#070b14`), glowing cyan/purple/orange telemetry HUD, translucent glassmorphism panels (`backdrop-filter: blur(16px)`).
- **Execution Architecture:**
  - **Standalone File Mode (`frontend/index.html`):** Single, self-contained HTML5 file with embedded 68 KB JSON payload (`terratwin_data.json`) and client-side scoring logic. Operates 100% offline via `file://` in any standard browser without Node/npm or external build steps.
  - **REST API Mode (`frontend/server.py`):** Lightweight HTTP server (pure Python standard library) exposing endpoints: `GET /api/targets`, `GET /api/targets/{id}/profile`, `GET /api/similarity/{id}`, `GET /api/presets`, `POST /api/similarity/recalculate`.

### 9.2 Spatial Map Engine
- **3D Interactive Earth Globe:** Spherical coordinates projection with starfield background, atmospheric glow, coordinate meridians, and rotating candidate pins. Supports mouse drag to pitch/yaw, mousewheel zoom, and smooth fly-to camera tweening.
- **2D Flat Map Mode:** Equirectangular projection covering $-180^\circ$ to $+180^\circ$ longitude and $-90^\circ$ to $+90^\circ$ latitude with graticule lines.
- **Continuous Similarity Heat Layer:** Color gradient overlay ($0\%$ dark slate $\rightarrow$ $70\%$ cyan $\rightarrow$ $80\%$ emerald $\rightarrow$ $100\%$ gold) showing regional similarity around candidate sites with adjustable opacity slider ($0-100\%$).
- **Segregated Mini-Target HUD:** Displays local crater/plain topography and CRS for the active planetary target, physically separated from Earth coordinates to prevent geographical confusion.

### 9.3 Dynamic Target Selection & Mission Presets
- **Supported Targets:**
  1. **Lunar South Pole:** Artemis III Base Camp zone, Shackleton/de Gerlache rims, South Polar Stereographic CRS.
  2. **Mars Jezero Crater:** Perseverance landing site, ancient river delta, clay-carbonate margins.
  3. **Mars Oxia Planum:** ExoMars Rosalind Franklin landing site, flat Noachian clay plains.
- **Presets & Real-Time Tuning:**
  - **Rover Mobility:** Prioritizes slope (30%), roughness (35%), relief (15%), and Hurst exponent (10%).
  - **Cold-Trap & Ice:** Prioritizes cryogenic minimum temperature (35%), PSR fraction (25%), and mean temperature (20%).
  - **Thermal Cycling:** Prioritizes diurnal temperature swing (35%), annual thermal range (25%), and mean temperature (20%).
  - **Balanced Default:** Equalized multi-feature balance.
  - **Interactive Sliders:** 8 real-time sliders for live weight tuning with $<1\text{ ms}$ recalculation of candidate rankings.

### 9.4 "Where the Analogy Breaks Down" Guardrails
Visually distinct, mandatory scientific limitation panel highlighting what Earth cannot replicate:
1. **Surface Gravity:** $0.166\text{ g}$ (Moon) / $0.376\text{ g}$ (Mars) vs $1.00\text{ g}$ (Earth) altering rover sinkage and tractive mechanics.
2. **Atmospheric Pressure & Vacuum:** $<10^{-10}\text{ Pa}$ (Moon vacuum) / $0.6\text{ kPa}$ (Mars $\text{CO}_2$) causing pure radiative thermal dissipation and instant water boiling/sublimation.
3. **Radiation Environment:** 300 to $1,100\text{ mSv/year}$ unshielded GCR + SPE vs $2.4\text{ mSv/year}$ on Earth.
4. **Regolith Morphology:** Jagged, sub-micron impact glass shards with electrostatic clinging and perchlorates ($\text{ClO}_4^-$) on Mars vs wind-abraded rounded sands on Earth.

### 9.5 Phase 6 Top-Site Analysis Dossiers
Detailed scientific Markdown reports generated in `docs/site-analysis/`:
- **Moon:** [McMurdo Dry Valleys](docs/site-analysis/moon/mcmurdo_dry_valleys.md), [Puna Plateau](docs/site-analysis/moon/puna_plateau.md), [Beacon Valley](docs/site-analysis/moon/beacon_valley.md), [Devon Island](docs/site-analysis/moon/devon_island.md).
- **Mars:** [Puna Plateau](docs/site-analysis/mars/puna_plateau.md), [Qaidam Basin](docs/site-analysis/mars/qaidam_basin.md), [Death Valley](docs/site-analysis/mars/death_valley.md), [Western Desert](docs/site-analysis/mars/western_desert.md), [Axel Heiberg](docs/site-analysis/mars/axel_heiberg.md).
- **Executive Summary:** [SITE_ANALYSIS_SUMMARY.md](docs/SITE_ANALYSIS_SUMMARY.md) summarizing rankings, presets, and limitations.

### 9.6 Visual Figures & Screenshot Locations
Located in `docs/figures/`:
1. `01_main_globe.svg` — Interactive 3D Earth Globe view.
2. `02_similarity_heat_layer.svg` — 2D Equidistant spatial similarity heatmap.
3. `03_moon_south_pole_view.svg` — Lunar South Pole target selected & AOI.
4. `04_mars_jezero_view.svg` — Mars Jezero Crater target selected & delta profile.
5. `05_mars_oxia_view.svg` — Mars Oxia Planum target selected & clay plains.
6. `06_mission_presets.svg` — Mission preset controls & weight tuning sliders.
7. `07_comparison_radar.svg` — Multi-axis Radar comparison chart (Earth vs Target).
8. `08_top_site_detail.svg` — Top-site detailed exploration dossier.
9. `09_analogy_breakdown.svg` — Where the analogy breaks down (unreplicable physics).
10. `10_full_app_overview.svg` — Complete dashboard application overview.

## 10. Results so far

Candidate analog sites identified from initial engine testing against Oxia Planum:
- **Western Desert Smectite Basin (Egypt)** — 24.50°N, 27.20°E — Target: Oxia Planum — Score: 68.6% — Strong geomorphic and wind-deflated clay analog (99.9% slope match, 99.0% roughness match).
- **Qaidam Basin Yardangs (Tibet)** — 37.15°N, 93.68°E — Target: Oxia Planum — Score: 67.0% — Strong terrain/locomotion analog (99.8% roughness match, 99.5% slope match, hyper-arid playa).
- **Beacon Valley (Antarctica)** — 77.83°S, 160.67°E — Target: Oxia Planum — Score: 63.9% — Volatile preservation and hyper-aridity analog (100% NDVI match, 94.6% moisture match).

