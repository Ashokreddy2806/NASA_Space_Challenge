# Plan

> Living document. Update it whenever a task starts, finishes, gets blocked, or a decision is made.
> Problem definition: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) · What happened: [PROGRESS_LOG.md](PROGRESS_LOG.md) · Rules for AI assistants: [AGENTS.md](AGENTS.md)

**Last updated:** 2026-11-15 01:24 by ashok (Phase 2 complete: Moon/Mars target profiles, PSR and Hurst checks, config-driven)

---

## 1. Goal

Build a Python-backed tool that **ranks every place on Earth by similarity to a lunar or Martian target site**, explains each match feature by feature (what matches, how closely, what doesn't), connects top sites to exploration use cases, and presents it all in a **visually impressive interactive map**.

Targets (each teammate will focus on one part; parts are **not assigned yet**):
- **Moon:** lunar south pole (permanent Moon base candidate region; permanently shadowed regions / cold traps, ice).
- **Mars:** a landing / exploration site (e.g. Jezero Crater; final choice is an open decision).

## 2. Approach

1. **Common feature space.** Pick a small set of features that can be measured on Earth *and* on the target body (e.g. surface temperature stats, slope, roughness, elevation range, albedo, hydrogen/ice proxy, mineral proxy, dryness, vegetation = 0).
2. **Global Earth grid.** Resample each Earth dataset to one common coarse grid (~0.05°, ≈5 km). Store as one compressed, chunked NetCDF4 dataset (Zarr is unavailable on this machine; see Decisions).
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
- **Frontend:** **deck.gl + MapLibre GL JS + Plotly** (confirmed 2026-11-14) — a polished web map with a 3D globe, heatmap layer of similarity scores and clickable sites; Plotly radar/bar charts for feature comparisons.

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
| W2 | Earth data pipeline: download + regrid to common global grid | ashok | done |
| W3 | Moon target profile (lunar south pole features) | ashok | done |
| W4 | Mars target profile (choose site + features) | ashok | done |
| W5 | Similarity engine: normalization, weights, scores, per-feature breakdown | — | not started |
| W6 | Backend API (FastAPI) serving scores and site details | — | not started |
| W7 | Frontend visualization (map, site cards, comparison charts) | — | not started |
| W8 | Top-site analysis + write-up (matches, mismatches, exploration use, Earth's limits) | — | not started |
| W9 | Submission: demo video, slides, final README | — | not started |

Status values: `not started` · `in progress` · `blocked` · `done`

## 6. Timeline (~24 h)

| Hours | Milestone | Done? |
|---|---|---|
| 0–2 | Repo + env set up, datasets chosen, feature list agreed | [x] |
| 2-8 | Earth grid built for core features; Moon + Mars target vectors computed | [x] |
| 8–13 | Similarity engine produces a global score map for each target | [ ] |
| 13–19 | API + visualization working end-to-end; top sites identified | [ ] |
| 19–22 | Site write-ups, polish visuals, "overlooked site" story | [ ] |
| 22–24 | Demo video, slides, submit | [ ] |

> The 2–8 h milestone is **complete**: Earth has 13 features + land mask on the 0.05° grid (2026-11-14 22:07), and the Moon (85°S disc) and Mars (Jezero 150 km disc) target profiles are built with the same registry (2026-11-15 01:20). Phase 3 (the similarity engine) is next.

## 7. Decisions log

Append newest at the bottom. Format: `YYYY-MM-DD HH:MM — <name> — decision — why`

- 2026-11-14 — rahul — Python backend; visuals must be high quality — judges see the visualization first.
- 2026-11-14 — rahul — Coarse global grid (~5 km) for search, high-res only for top candidates — 8 GB RAM Macs.
- 2026-11-14 — rahul — Each teammate will focus on one part; parts not assigned yet.
- 2026-11-14 16:38 — ashok — Project code/docs stay in `NASA_Space_Challenge/`; raw data stays in `../Datasets/{Moon,Mars,Earth}` and is mapped by `backend/paths.py` — the team docs already live here and copying >1 GB of rasters into the repo would waste disk.
- 2026-11-14 16:38 — ashok — Use the detected 2.5 arc-minute WorldClim layers (not the 10-minute fallback), ETOPO 60 arc-second, LOLA polar GeoTIFFs, and the raw MOLA `megt90n000eb.img` — all verified open in Phase 0; no data re-downloaded.
- 2026-11-14 16:38 — ashok — Pin `rasterio<1.5` in `requirements.txt` — 1.5.2's `_base` DLL is blocked by this machine's Windows Application Control policy; 1.4.3 imports and reads every raster normally.
- 2026-11-14 16:38 — ashok — Compute terrain features in km-sized windows on an equal-area working grid, then sample them onto the 0.05° lon/lat search grid — meets the "matched physical window" rule; 0.05° cells shrink in longitude toward the poles, which the ranker must not hide.
- 2026-11-14 17:05 — ashok — Frontend confirmed: **deck.gl + MapLibre GL JS + Plotly** — approved by the team; best visual quality for the global heat layer and site comparison charts.
- 2026-11-14 17:05 — ashok — MVP feature list confirmed: **relief, slope, multi-scale roughness, scale-robust roughness (Hurst), temperature stats/day–night swing, dryness**, plus a **separate ice/cold-trap proxy** — recorded in `docs/FEATURES.md`; no extra features until the MVP works.
- 2026-11-14 17:05 — ashok — Use the raw MOLA `megt90n000eb.img` directly; do **not** create `mars_elev.npy` — the file is verified int16 16 ppd, north-up, 0–360°E.
- 2026-11-14 17:05 — ashok — Hand-made `moon_thermal_literature.csv` and `mars_thermal_literature.csv` will be supplied by the team before Phase 2 — no temperature values will be guessed.
- 2026-11-14 21:40 — ashok — Store the Earth grid as chunked, compressed **NetCDF4** (`data/processed/earth_features.nc`) instead of Zarr — `numcodecs`' Jenkins DLL is blocked by Windows Application Control, but NetCDF4/HDF5 gives the same chunking and compression; `zarr` was removed from `requirements.txt`.
- 2026-11-14 21:40 — ashok — Terrain features are computed per 10° tile on a **2 km local azimuthal-equidistant grid** (1° halo), then area-averaged onto the 0.05° grid — this keeps every window in kilometres and avoids stretching 0.05° cells near the poles.
- 2026-11-14 21:40 — ashok — Locked terrain estimators: relief = **p95−p5 in 20 km**, slope = **mean of per-2 km gradient magnitude in 20 km**, roughness = **std of a Gaussian high-pass residual** at 5/10/20 km (`σ = window/2`), Hurst = **half the log–log structure-function slope** for lags 2/4/8/16/32 km. Phase 2 must use exactly the same estimators; recorded in `docs/FEATURES.md`.
- 2026-11-14 21:40 — ashok — Before filtering, **ocean cells are filled with the nearest land elevation** using the WorldClim land mask — ETOPO includes bathymetry, and without this a 20 km coastal window would report a fake 3–5 km relief cliff along every coast.
- 2026-11-14 21:40 — ashok — Earth land mask and climate features come from **WorldClim ocean nodata** (majority-valid at 0.05°); all published features are NaN over ocean — ETOPO cannot supply a land mask because it includes the sea floor.
- 2026-11-15 01:20 — ashok — **No-hard-coding retrofit**: every grid, window, lag, percentile, target, site and file name lives in `config/*.yaml` and is read through `backend/config.py`; one feature registry serves Earth, Moon and Mars — required as a condition of Phase 1 approval, and proven by two config-only runs (`docs/hardcode_audit.md`).
- 2026-11-15 01:20 — ashok — Lunar target is the **disc poleward of 85°S**, radius 151.713 km computed from the LDEM's own south-polar-stereographic CRS (`r = 2R·tan(colat/2)`), not from a named site list — the team asked for the regional analog rather than single landing sites.
- 2026-11-15 01:20 — ashok — Mars target is **Jezero crater, 18.3628°N 77.5945°E, −2656 m, 150 km radius**; the nearest raw-MOLA cell is −2663 m (Δ −7 m), which confirms the 0–360°E grid orientation.
- 2026-11-15 01:20 — ashok — **Comparability rule**: a window is `resolved` at ≥2.5 native pixels, `marginal` at 2.5–4.0, `unavailable` below 2.5; Hurst needs ≥3 resolved lags. This is why Mars (MOLA 16 ppd, ~3.7 km) loses 5 km roughness and Hurst instead of interpolating them.
- 2026-11-15 01:20 — ashok — Moon terrain is **recomputed from the 80 m LDEM** with the same windows and lags as Earth; LOLA H/SPSLP/ROUGH are cross-checks only. LOLA `H` is nearly saturated (median 0.971) so it is documented as a weak cross-check; slope r=0.983 and 800 m roughness r=0.882 are the informative ones.
- 2026-11-15 01:20 — ashok — Mars has **no surface-temperature range** in the cited literature, so `temp_diurnal_range_c` and `temp_annual_range_c` are unavailable by config, excluded from its score, and the remaining group weights are renormalised.
- 2026-11-15 01:20 — ashok — Phase 3 must output **both** rank-based similarity and the **absolute gap in real units** per feature, with a plain-language note where rank similarity hides a large real-unit difference (e.g. lunar day–night swing vs any Earth desert).

## 8. Open questions

- [x] Frontend: **deck.gl + MapLibre GL JS with Plotly radar/bar charts** — confirmed 2026-11-14.
- [x] Final feature list: **six MVP features + separate ice proxy** — confirmed 2026-11-14; see `docs/FEATURES.md`.
- [x] Which Mars site is the target — **Jezero crater** (18.3628°N 77.5945°E, 150 km disc) — confirmed 2026-11-15.
- [x] Confirm the lunar target region — **poleward of 85°S**, a 151.713 km disc around the pole — confirmed 2026-11-15.
- [ ] How to weight features, and should users be able to change weights in the UI? (Phase 3 defaults, Phase 5 controls.)
- [ ] Who owns which workstream? (W1–W4 done by ashok; W5–W9 unassigned.)
- [x] Lunar PSR CSV has no CRS metadata — **read as metres in the LDEM south-polar-stereographic CRS**; all 1,531 polygons fall inside the DEM extent and the rasterised PSRs sit on topographic lows, which is the evidence. The ~76°S tile corner does not clip the 85°S cap (429.9 km > 151.7 km). Confirmed 2026-11-15.
- [ ] Provide `moon_thermal_literature.csv` and `mars_thermal_literature.csv` — still missing; Phase 2 reports Moon/Mars temperature as unavailable by exact path.

## 9. Results so far

_Nothing yet. Add top candidate sites here as they appear (name, lat/lon, target, score, one-line why)._
