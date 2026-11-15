# Plan

> Living document. Update it whenever a task starts, finishes, gets blocked, or a decision is made.
> Problem definition: [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) · What happened: [PROGRESS_LOG.md](PROGRESS_LOG.md) · Rules for AI assistants: [AGENTS.md](AGENTS.md)

**Last updated:** 2026-11-15 13:33 by ashok (Phase 3b complete: declared no-precipitation constraint, per-site stability, ice/substrate caveats, analog provenance)

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
| W5 | Similarity engine: normalization, weights, scores, per-feature breakdown | ashok | done |
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
| 8–13 | Similarity engine produces a global score map for each target | [x] |
| 13–19 | API + visualization working end-to-end; top sites identified | [ ] |
| 19–22 | Site write-ups, polish visuals, "overlooked site" story | [ ] |
| 22–24 | Demo video, slides, submit | [ ] |

> The 2–8 h milestone is **complete**: Earth has 13 features + land mask on the 0.05° grid (2026-11-14 22:07), and the Moon (85°S disc) and Mars (Jezero 150 km disc) target profiles are built with the same registry (2026-11-15 01:20).

> The 8–13 h milestone is **complete** (2026-11-15 11:01 UTC): the engine writes `data/processed/scores_moon.nc` and `scores_mars.nc` (per-group grids plus one score per preset), `data/processed/top_sites.json` and `docs/phase3_report.md` in ~82 s. Top site, Moon balanced: −5.925, 146.525 (0.830). Top site, Mars balanced: −71.725, −72.825 (0.951, terrain-only). Phase 4 (API) is next.

> **Phase 3b complete** (2026-11-15 13:33): the no-precipitation constraint is scored on both targets with the same engine, every candidate carries a stability value from the nine sensitivity runs, the site lists carry both with/without-famous forms plus ice/substrate caveat flags, and analog provenance is explicit. Engine runtime 287 s (stability now ranks variants exactly like the report list). Post-3b coverage: Moon 10/13 features, 6/7 groups; Mars 6/13, 4/7. Top site, Moon balanced: −10.275, −77.575 (0.795, stability 0.78). Top site, Mars balanced: 25.675, 34.575 (0.917).

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
- 2026-11-15 10:50 — ashok — Both thermal literature CSVs arrived and are now ingested, not guessed: flat `feature,value,units,source` schema, 10 Moon reference quantities and 4 Mars quantities (**thermal inertia only — no Mars temperatures**). Kelvin→°C is an exact −273.15 offset, and bracketing `*_min`/`*_max` rows become **derived ranges** that name both inputs. They are reference numbers, not per-cell maps, so they are **not** matched numerically to WorldClim air temperature; all temperature features stay `unavailable` until the qualitative-anchor mapping is approved.
- 2026-11-15 10:50 — ashok — The PSR "lower slopes than background" test is recorded as an **expected result, not a failure**: a PSR polygon includes the shadowed crater wall and rim that cast the shadow, so a strict slope test cannot pass by construction. Numbers stay in `docs/psr_verification.md`; the topographic-low test (1,213 m below background median, 77% of PSR pixels) is the alignment evidence.
- 2026-11-15 10:50 — ashok — `docs/phase2_report.md` now takes its timestamp from the JSON `created_utc` instead of wall-clock time, so report header and artifact can no longer drift apart.
- 2026-11-15 12:16 — ashok — **Thermal mapping: option A (banded anchors)**. Only exact cited *polar* rows are scored: `temp_min_coldest_c` from the PSR/cold-trap rows (Cabeus 37 K, coldest midday 29 K, large-crater daily max 40–90 K, cold-trap threshold 110 K) and `temp_max_warmest_c` from the 89°S peak-illumination value (180 K, labelled horizontal surface). Earth cells are placed in configured bands and scored by band distance; every such output is labelled `qualitative` and the group weight is low (0.25 in `config/features.yaml`). A build fails if the cited anchors straddle two bands.
- 2026-11-15 12:16 — ashok — **No derived day–night swing or annual range for the Moon**: no cited polar value exists for either, so `temp_diurnal_range_c`, `temp_mean_c` and `temp_annual_range_c` stay `unavailable` with the reason recorded. The equatorial 400 K subsolar maximum and 100 K night value are **context only** and never enter a score.
- 2026-11-15 12:16 — ashok — **Similarity = both rank and real units.** Rank similarity is `1 − |p_earth − q|` (area-weighted percentiles); absolute similarity is `exp(−0.5·(gap/scale)²)` with `scale = max(p16–p84 half-spread, 10%·|median|, measurement floor)`. A `hidden_gap` flag marks rank ≥ 0.75 with absolute ≤ 0.35 (both config) and never changes the score.
- 2026-11-15 12:16 — ashok — **Area, not cells.** Every percentile, mean, group score and site score is weighted by `cos(latitude)`. Coverage of Earth land is reported per target, and a target that uses fewer features gets renormalised weights instead of imputed values.
- 2026-11-15 12:16 — ashok — **Top sites are greedy NMS** at the preset's `min_separation_km`, then ranked by an area-weighted site score inside a configurable fraction of that radius. Lists are emitted **with and without** sites inside the configured 100 km famous-site radius, because famous analogs are a sanity check rather than the answer.
- 2026-11-15 12:16 — ashok — **Four presets in `config/presets.yaml`**: `balanced`, `rover_mobility` (terrain only, temperature weight 0), `cold_trap_ice` (terrain + temperature), `thermal_cycling` (heavier roughness + temperature). For Mars, `cold_trap_ice` collapses to the same ranking as `balanced` because only terrain features are usable; the engine emits `equivalent_to` and the report labels it "not independent evidence".
- 2026-11-15 12:16 — ashok — **Thermal sensitivity verdict kept as found**: varying band edges by ±5 °C and the temperature weight over {0, 0.25, 0.5} gives a **minimum top-N overlap of 0.20** against the balanced baseline (Spearman rho ≥ 0.975). Rankings change materially, so the thermal contribution is reported as **weak evidence, not a ranking driver**. Nothing was tuned to change this.
- 2026-11-15 12:16 — ashok — **Composition gap recorded, not papered over**: this build has no Earth substrate, mineralogy or thermal-inertia map, so a smooth ice sheet and a smooth rock plain are indistinguishable to the terrain features. That is why the Mars ranking puts Antarctic plateau cells on top; the report calls Mars a terrain result, not a composition result.
- 2026-11-15 13:33 — ashok — **Dryness is a physical constraint on both targets.** The Moon and Mars have no rainfall and no vegetation, so the target is **0 mm** with a declared tolerance band (0–50 mm annual, 0–4 mm driest month) in `config/config.yaml`, scored by the same rank + absolute engine and labelled `constraint` / `declared_tolerance`. Weight **0.25** in `balanced` and `cold_trap_ice` (the same low weight as the qualitative thermal anchors) and **0** in `rover_mobility` and `thermal_cycling`; it is never tuned to flatter an analog.
- 2026-11-15 13:33 — ashok — **Per-site stability from the sensitivity runs.** A site's stability is the fraction of the nine thermal settings in which it stays in the top-N, matched within 25 km (half the 50 km separation, configured). It is stored on every balanced Moon site, ranked in the report, and never folded into the score. The sensitivity variants now rank sites exactly as the report list does (NMS → area-weighted site score), fixing a spurious zero-stability artefact from comparing aggregated sites with raw peaks.
- 2026-11-15 13:33 — ashok — **Ice/substrate caveat is a heuristic flag, not a mask.** Two config-declared boxes (Greenland, Antarctic) mark regions where this feature set cannot distinguish ice cover from bare ground; a site inside one carries "our data cannot distinguish ice cover from bare ground". The boxes include ice-free coast, nunataks, the Dry Valleys and Ross Island, and say so in config.
- 2026-11-15 13:33 — ashok — **Analog provenance is explicit and never over-claimed.** Coordinates were reviewed on 2026-11-15; Licancabur (Cabrol et al. 2009 JGR 114 G00D06, DOI fetched) and Mistastin (Mader et al. 2010 GeoCanada abstract, PDF found) are marked citation-verified; Rio Tinto keeps its from-memory source with a spot-check warning; Mauna Kea has no citation and `display_source: false`, so its source string is never shown. Going forward an unchecked reference is labelled "proposed, unverified", never presented as a citation.
- 2026-11-15 13:33 — ashok — **Both site lists are guaranteed for every preset**: `top_sites.json` and the report carry `sites` and `sites_excluding_famous`, and the famous list now covers McMurdo Station, Ross Island, Mount Erebus and McMurdo Dry Valleys (proposed, reviewed: false, awaiting team confirmation).

## 8. Open questions

- [x] Frontend: **deck.gl + MapLibre GL JS with Plotly radar/bar charts** — confirmed 2026-11-14.
- [x] Final feature list: **six MVP features + separate ice proxy** — confirmed 2026-11-14; see `docs/FEATURES.md`.
- [x] Which Mars site is the target — **Jezero crater** (18.3628°N 77.5945°E, 150 km disc) — confirmed 2026-11-15.
- [x] Confirm the lunar target region — **poleward of 85°S**, a 151.713 km disc around the pole — confirmed 2026-11-15.
- [x] How to weight features, and should users be able to change weights in the UI? — **Phase 3 defaults are four config presets** (`balanced`, `rover_mobility`, `cold_trap_ice`, `thermal_cycling`); user-facing weight controls remain a Phase 5 frontend item.
- [ ] Who owns which workstream? (W1–W5 done by ashok; W6–W9 unassigned.)
- [x] Lunar PSR CSV has no CRS metadata — **read as metres in the LDEM south-polar-stereographic CRS**; all 1,531 polygons fall inside the DEM extent and the rasterised PSRs sit on topographic lows, which is the evidence. The ~76°S tile corner does not clip the 85°S cap (429.9 km > 151.7 km). Confirmed 2026-11-15.
- [x] Provide `moon_thermal_literature.csv` and `mars_thermal_literature.csv` — **supplied 2026-11-15** (Moon: 10 reference quantities; Mars: 4 thermal-inertia quantities, no temperatures). Read and reported in `docs/phase2_report.md` under "Thermal literature".
- [x] **Thermal scoring mapping** — **option A, banded polar anchors** chosen 2026-11-15; equatorial values stay context-only, Mars temperature stays unavailable.
- [x] **Validation sites for Phase 3** — four analogs were reviewed on 2026-11-15; `reviewed: true` is set in `config/validation_sites.yaml` as instructed, and the conflicting line asking to leave them `false` is flagged at the phase gate. Reviewing them changed no score. Two citations are verified, Rio Tinto is marked from-memory and Mauna Kea has no citation and is never displayed.
- [x] **Presets** — `balanced`, `rover_mobility`, `cold_trap_ice` and `thermal_cycling` defined in `config/presets.yaml` 2026-11-15, with weights, top-N and separation all in config.

## 9. Results so far

Top NMS site per target and preset, after area weighting and the configured separation. **Moon and Mars scores are not comparable** — different feature sets and different coverage (Moon 10/13 features, 6/7 groups; Mars 6/13, 4/7).

| Target | Preset | Top site (lat, lon) | Score | Stability | One-line why |
|---|---|---|---|---|---|
| Moon | balanced | −10.275, −77.575 | 0.795 | 0.78 | High Andean terrain: matched relief/slope/roughness plus an almost dry driest month (annual ≈279 mm); the constraint demoted the wet tropical peak that led before |
| Moon | rover_mobility | −5.925, 146.525 | 0.858 | — | Terrain-only optimum (New Guinea highlands): the most traversable relief/slope/roughness match |
| Moon | cold_trap_ice | −84.325, 175.525 | 0.783 | — | High Antarctic plateau: smooth cold terrain with the coldest configured band; flagged `ice-substrate` |
| Moon | thermal_cycling | −64.375, −60.025 | 0.805 | — | Antarctic Peninsula: high roughness with a cold band match; flagged `ice-substrate` |
| Mars | balanced | 25.675, 34.575 | 0.917 | — | Eastern Desert (Egypt): smooth low-relief terrain closest to Jezero, now also very dry — **terrain + dryness only** |
| Mars | rover_mobility | −71.725, −72.825 | 0.953 | — | Antarctic plateau on terrain alone |
| Mars | cold_trap_ice | 25.675, 34.575 | 0.921 | — | Same top cell as balanced but a different ranking (dryness participates); not emitted as equivalent |
| Mars | thermal_cycling | −76.175, −148.375 | 0.940 | — | Antarctic plateau with rougher micro-relief, still terrain-driven; flagged `ice-substrate` |

Known analogs, scored as found and **not** tuned for (`docs/phase3_report.md` §5): Moon balanced — Mauna Kea 0.807, Licancabur 0.786, Dry Valleys 0.605, Death Valley 0.492, Iceland 0.477, Atacama 0.440, Sahara 0.219, Devon Island 0.217, Mistastin Lake 0.196, Amazon 0.144. Mars balanced — Atacama 0.847, Rio Tinto 0.824, Devon Island 0.773, Iceland 0.732, Sahara 0.610, Death Valley 0.578, Amazon 0.438, Dry Valleys 0.079, Licancabur 0.040, Mauna Kea 0.000. The Mars column rewards smooth low-relief, dry terrain rather than the classic astrobiological analogs, which is the honest result of a terrain + dryness feature set. Adding the constraint changed every analog score (mostly downward: Moon Mauna Kea 0.855 → 0.807, Mars Rio Tinto 0.881 → 0.824; a few already-dry sites moved slightly up, e.g. Atacama 0.417 → 0.440 on the Moon), because an Earth site receiving more than 0 mm is physically unlike the target.

Thermal sensitivity (Moon): top-N overlap with the balanced baseline falls as low as **0.64** (after the ranking consistency fix; previously 0.20) while Spearman rho stays ≥ 0.978 — still labelled weak evidence, not a ranking driver. Per-site stability across the nine settings ranges from 0.56 to 1.00; the top balanced site survives 7/9, while the terrain-only optimum survives 9/9.
