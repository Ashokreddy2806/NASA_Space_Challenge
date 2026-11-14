# Plan

> Living document. Update it whenever a task starts, finishes, gets blocked, or a decision is made.
> Problem definition: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) · What happened: [PROGRESS_LOG.md](PROGRESS_LOG.md) · Rules for AI assistants: [AGENTS.md](AGENTS.md)

**Last updated:** 2026-11-14 16:38 by ashok (Phase 0: repo scaffold + data inventory)

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
data/raw/          downloaded source files (git-ignored; actual files live in
                   ../Datasets/{Moon,Mars,Earth}, mapped by backend/paths.py)
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
| W1 | Repo setup: folders, `requirements.txt`/env, `.gitignore`, README | ashok | done |
| W2 | Earth data pipeline: download + regrid to common global grid | — | not started |
| W3 | Moon target profile (lunar south pole features) | — | not started |
| W4 | Mars target profile (choose site + features) | — | not started |
| W5 | Similarity engine: normalization, weights, scores, per-feature breakdown | — | not started |
| W6 | Backend API (FastAPI) serving scores and site details | — | not started |
| W7 | Frontend visualization (map, site cards, comparison charts) | — | not started |
| W8 | Top-site analysis + write-up (matches, mismatches, exploration use, Earth's limits) | — | not started |
| W9 | Submission: demo video, slides, final README | — | not started |

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
- 2026-11-14 16:38 — ashok — Project code/docs stay in `NASA_Space_Challenge/`; raw data stays in `../Datasets/{Moon,Mars,Earth}` and is mapped by `backend/paths.py` — the team docs already live here and copying >1 GB of rasters into the repo would waste disk.
- 2026-11-14 16:38 — ashok — Use the detected 2.5 arc-minute WorldClim layers (not the 10-minute fallback), ETOPO 60 arc-second, LOLA polar GeoTIFFs, and the raw MOLA `megt90n000eb.img` — all verified open in Phase 0; no data re-downloaded.
- 2026-11-14 16:38 — ashok — Pin `rasterio<1.5` in `requirements.txt` — 1.5.2's `_base` DLL is blocked by this machine's Windows Application Control policy; 1.4.3 imports and reads every raster normally.
- 2026-11-14 16:38 — ashok — Compute terrain features in km-sized windows on an equal-area working grid, then sample them onto the 0.05° lon/lat search grid — meets the "matched physical window" rule; 0.05° cells shrink in longitude toward the poles, which the ranker must not hide.

## 8. Open questions

- [ ] Which Mars site is the target (Jezero? another)? Ask again in Phase 2.
- [ ] Confirm the lunar target region: poleward of 85°S vs specific candidate base sites. Ask in Phase 2.
- [ ] Frontend: **proposal** deck.gl + MapLibre GL JS with Plotly radar/bar charts (alternative: Streamlit + pydeck). Awaiting confirmation; not recorded as a decision yet.
- [ ] Final feature list: **proposal** is the six MVP features + separate ice proxy in `docs/FEATURES.md`. Awaiting confirmation; not recorded as a decision yet.
- [ ] How to weight features, and should users be able to change weights in the UI? (Phase 3 defaults, Phase 5 controls.)
- [ ] Who owns which workstream? (W1 done by ashok; others unassigned.)
- [ ] Lunar PSR CSV has no CRS metadata and its square tile reaches ~76°S at the corners (not a strict 80°S cut). Confirm the intended projection for the Phase 2 polygon overlay.

## 9. Results so far

_Nothing yet. Add top candidate sites here as they appear (name, lat/lon, target, score, one-line why)._
