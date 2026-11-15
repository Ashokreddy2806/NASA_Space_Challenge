# Progress Log

Who did what, and when. Each team member has **their own section**. Only write in your own section.

## How to add an entry

1. Go to **your** section below.
2. Update the **Now working on** line.
3. Add a new entry **at the top** of your entries (newest first), directly under the `<!-- entries -->` marker.
4. Use this format:

```markdown
#### YYYY-MM-DD HH:MM — short title
- **Did:** what changed / what was made (1–3 bullets, concrete)
- **Files:** paths touched (e.g. `backend/engine/score.py`)
- **Next:** what comes next
- **Blockers:** anything blocking you or needing a teammate (or "none")
```

Keep entries short. Big decisions also go in the **Decisions log** in [PLAN.md](PLAN.md); workstream status goes in the **Workstreams** table there.

---

## rahul

**Now working on:** Using unused NASA data: Diviner lunar temperatures done; next MODIS LST for Earth, Mars thermal inertia; Phase 2/3 reconcile with main still open

<!-- entries -->

#### 2026-11-15 13:14 — Diviner lunar temperatures
- **Did:** Read the already-downloaded Diviner PRP table (563k triangles poleward of 85S) and set the lunar target's `temp_mean_c` (-171 C) and `temp_max_warmest_c` (-42 C); both beyond Earth's range. Cold-trap area from Diviner (9.81%) matches the LOLA PSR table (9.81%). Added preset `thermal_surface`; `thermal_cycling` stays unavailable (table has no min/range). Reran scoring; `balanced` results unchanged. 55 tests pass.
- **Files:** `backend/pipeline/target_profiles.py`, `backend/engine/similarity.py`, `frontend/app.js`, `tests/test_phase2.py`, `docs/target_profiles.json`, `docs/top_sites.json`, `docs/validation.md`
- **Next:** MODIS MOD11C3 surface temperature for Earth (needs Earthdata login) so the comparison is surface vs surface; Mars thermal inertia.
- **Blockers:** Earth side is still WorldClim air temperature; Jezero temperatures still null.

#### 2026-11-15 14:00 — Phase 7 submission pack
- **Did:** Final README (reproduction, credits, limits), `docs/SUBMISSION.md` (1:45 storyboard, 8-slide outline, judging checklist), architecture figure, Makefile `all/serve/targets/score`, `GridStore` creates its output dir. Fresh-clone reproduction test run (result below in PLAN/summary).
- **Files:** `README.md`, `docs/SUBMISSION.md`, `docs/make_architecture.py`, `docs/figures/architecture.png`, `Makefile`, `backend/pipeline/feature_store.py`
- **Next:** decide with Ashok which Phase 2/3 implementation is canonical (main has his; this branch has mine); record the demo video.
- **Blockers:** merge conflicts with origin/main in `backend/engine/similarity.py`, `tests/test_phase2.py`, `tests/test_phase3.py`, `PLAN.md`, `docs/FEATURES.md`; temperatures still unscored.

#### 2026-11-15 13:20 — Phase 6 top-site analysis
- **Did:** Wrote `docs/SITE_ANALYSIS.md`: six candidates (3 Jezero, 3 lunar pole) with matches, mismatches, exploration use, what Earth cannot replicate, and next steps; added them to PLAN.md section 9. Flags: place names approximate, temperatures unscored, sub-scores are percentile ranks.
- **Files:** `docs/SITE_ANALYSIS.md`, `PLAN.md`
- **Next:** Phase 7 submission pack (awaiting approval).
- **Blockers:** site-specific temperatures (lunar pole, Jezero); minerals not in the feature set.

#### 2026-11-15 12:50 — Phase 5 frontend
- **Did:** Interactive map app: Moon/Mars target picker, preset chips, weight sliders, top-10 with hide-famous toggle, click-anywhere site panel (radar, feature table, "where the analogy breaks down", "Earth cannot replicate"). Verified end to end in a browser incl. custom weights; screenshots captured. 54 tests pass.
- **Files:** `frontend/{index.html,style.css,app.js,README.md}`, `backend/api/main.py` (serves `/`), `docs/figures/frontend_{moon,mars}.png`
- **Next:** Phase 6 top-site analysis (awaiting approval).
- **Blockers:** needs internet for CDN libs and basemap; temperatures still unscored.

#### 2026-11-15 10:30 — Phase 4 backend API
- **Did:** FastAPI app with targets, presets, top sites (JSON/GeoJSON, with/without famous sites), per-site feature breakdown (match/partial/mismatch, not-scored, Earth-cannot-replicate), score PNG with preset or custom weights. Latency 2–270 ms. 53 tests pass.
- **Files:** `backend/api/main.py`, `backend/api/data.py`, `docs/API.md`, `tests/test_phase4.py`, `requirements.txt`
- **Next:** Phase 5 frontend (awaiting approval).
- **Blockers:** none for the API; temperature scoring still needs site-specific values.

#### 2026-11-15 10:05 — Phase 3 similarity engine
- **Did:** Percentile-distance engine with 4 presets, score maps for both targets, top-10 sites with and without famous sites, validation vs Atacama / Dry Valleys / Devon / Death Valley / Iceland (all 9 expected-feature checks pass). Top Moon sites: Andes–Atacama, Kunlun (36N 81E), East Antarctica; Mars: Andes, Egypt/Sudan desert. 46 tests pass.
- **Files:** `backend/engine/similarity.py`, `backend/engine/run_scoring.py`, `tests/test_phase3.py`, `docs/top_sites.json`, `docs/validation.md`, `docs/figures/score_*.png`; scores in `data/processed/similarity_*.nc` (git-ignored)
- **Next:** Phase 4 API (awaiting approval).
- **Blockers:** thermal_cycling preset and all temperature scoring need site-specific temperatures.

#### 2026-11-15 09:40 — Phase 1 merged, Phase 2 target profiles
- **Did:** Merged Ashok's Phase 1 from main, rebuilt the Earth grid locally (matches his report). Measured the lunar south pole (<85°S) and Jezero with the Earth estimators on a 2 km grid; placed each on Earth's area-weighted percentile scale (Moon relief 99th pct, slope 99th; Jezero relief 83rd). Moon PSR cover 9.8% of the disk. 39 tests pass.
- **Files:** `backend/pipeline/target_profiles.py`, `tests/test_phase2.py`, `docs/target_profiles.json`, `docs/figures/target_{moon,mars}_vs_earth.png`, `PLAN.md`
- **Next:** Phase 3 similarity engine (awaiting approval).
- **Blockers:** site-specific temperatures (south pole, Jezero) still missing; targets' temperature features are null.

#### 2026-11-14 21:53 — Thermal CSVs from NASA sources, normalization fix, Phase 0 alignment
- **Did:** Wrote `Datasets/Moon/moon_thermal_literature.csv` and `Datasets/Mars/mars_thermal_literature.csv` from NASA NSSDC fact sheets and Sefton-Nash 2019 (only values actually read; equator / Viking 1 / global, not south pole or Jezero). Changed `docs/FEATURES.md` normalization to the Earth reference distribution (Decision logged). Phase 0 alignment: pyproj in requirements, cross-platform Makefile, macOS README, `Datasets/` in .gitignore.
- **Files:** `docs/FEATURES.md`, `PLAN.md`, `requirements.txt`, `Makefile`, `README.md`, `.gitignore`, `Datasets/{Moon,Mars}/*_thermal_literature.csv` (git-ignored)
- **Next:** South-pole temperatures and Jezero values still missing (Williams 2019 and MEDA papers are paywalled or blocked).
- **Blockers:** need open-access copies of Williams et al. 2019 (JGR, doi:10.1029/2019JE006028) and a Jezero MEDA paper, or values supplied by a teammate.

#### 2026-11-14 21:46 — Data downloaded, adopted Ashok's Datasets layout, HF upload
- **Did:** Downloaded all of `docs/DATASETS.md` plus PDS Diviner/LOLA/MOLA (~2.2 GB). Replicated Ashok's Phase 0 on macOS (Python 3.11 venv, 13 tests pass). Moved everything to `../Datasets/{Moon,Mars,Earth}` with his file names (PDS extras in `Moon/pds/`). Uploading to private HF dataset `rahuloruganti/nasa-analog-data` in the same layout.
- **Files:** `backend/pipeline/download.py`, `download_datasets.py`, `publish_hf.py` (run with `python -m backend.pipeline.<name>`), `docs/DATA_CATALOG.md`
- **Next:** Teammates can fetch the HF repo into `Datasets/`. Makefile/README need macOS lines.
- **Blockers:** only 7 of 19 WorldClim layers downloaded; both thermal-literature CSVs still missing.

#### 2026-11-14 15:36 — Data catalog + PDS downloader
- **Did:** Wrote `docs/DATA_CATALOG.md` (data kinds, formats, per-product files/sizes checked against live PDS listings, download tiers). Wrote `backend/pipeline/download.py` (open PDS products, `--list` verified all URLs). No data downloaded yet.
- **Files:** `docs/DATA_CATALOG.md`, `backend/pipeline/download.py`
- **Next:** Approve and run `python backend/pipeline/download.py T1`; Earth products need an Earthdata login in `~/.netrc`.
- **Blockers:** Earthdata account/credentials needed from a teammate for Earth data.

#### 2026-11-14 15:21 — Added resources folder
- **Did:** Added a "Resources" subsection with the challenge's NASA/CSA/ESA/JAXA links to PROBLEM_STATEMENT.md (also kept a local-only `resources/` folder, excluded via .git/info/exclude).
- **Files:** `PROBLEM_STATEMENT.md`
- **Next:** Team picks specific data products and records them in PLAN.md.
- **Blockers:** none

#### 2026-11-14 15:17 — No AI attribution in commits
- **Did:** Added a git rule to AGENTS.md: no Claude/AI co-author trailers or "Generated with" lines in commits or PRs.
- **Files:** `AGENTS.md`
- **Next:** Team picks workstreams in PLAN.md.
- **Blockers:** none

#### 2026-11-14 — Project docs set up
- **Did:** Created problem statement, plan, progress log, and AI assistant rules.
- **Files:** `PROBLEM_STATEMENT.md`, `PLAN.md`, `PROGRESS_LOG.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`
- **Next:** Team picks workstreams in PLAN.md.
- **Blockers:** none

---

## ashok

**Now working on:** Phase 1 complete — Earth 0.05° feature grid built and tested; awaiting Phase 2 approval

<!-- entries -->

#### 2026-11-14 22:07 — Phase 1: global 0.05° Earth feature grid
- **Did:** Built the Earth side of the analog search: a 7200×3600 (0.05°) grid from ETOPO 2022 + WorldClim 2.1 with 13 features + land mask. Terrain is computed per 10° tile on a 2 km local azimuthal-equidistant grid in km windows (relief p95−p5 at 20 km, mean slope at 20 km, high-pass roughness at 5/10/20 km, Hurst from 2–32 km lags), then area-averaged; ocean cells are filled with the nearest land elevation before filtering so bathymetry cannot fake coastal relief. Climate is five temperature statistics + two precipitation variables; WorldClim ocean nodata supplies the land mask (8,712,831 land cells, 29.3% area-weighted). Wrote `earth_features.nc` (~300 MB), `docs/earth_grid_report.md`, 13 feature maps + overview, and 21 Phase 1 tests (34 total passing).
- **Files:** `backend/pipeline/earth_grid.py`, `earth_climate.py`, `earth_terrain.py`, `build_earth_features.py`, `feature_store.py`, `tests/test_phase1.py`, `docs/FEATURES.md`, `docs/earth_grid_report.md`, `docs/figures/earth_*.png`, `README.md`, `Makefile`, `PLAN.md`, `requirements.txt`
- **Next:** Phase 2 — Moon (LOLA polar DEM + PSR table) and Mars (MOLA) target profiles using the same estimators, plus the cited thermal CSVs.
- **Blockers:** await Phase 2 approval; confirm lunar target region (poleward of 85°S vs named sites), confirm Mars site (Jezero?), and receive `moon_thermal_literature.csv` + `mars_thermal_literature.csv`.

#### 2026-11-14 16:38 — Phase 0: inventory, environment, scaffold
- **Did:** Verified every downloaded raster/CSV (CRS, resolution, nodata, sampled range, units) in `docs/data_inventory.md`; found `mars_elev.npy` absent but the raw MOLA `.img` present, both literature CSVs missing, and the WorldClim layers at 2.5 arc-min. Added pinned `requirements.txt`, repo scaffold, README, proposed `docs/FEATURES.md`, Makefile and 13 passing smoke tests.
- **Files:** `backend/paths.py`, `backend/pipeline/inspect_datasets.py`, `docs/data_inventory.md`, `docs/FEATURES.md`, `README.md`, `requirements.txt`, `Makefile`, `tests/test_phase0.py`, `.gitignore`
- **Next:** Phase 1 — regrid ETOPO/WorldClim to the 0.05° grid and derive terrain/climate features.
- **Blockers:** await approval of frontend stack and MVP feature list; confirm lunar/Mars target regions in Phase 2.

#### 2026-11-14 15:56 — Added dataset catalog
- **Did:** Added the Moon, Mars, and Earth dataset inventory with source links, feature mappings, and limitations.
- **Files:** `docs/DATASETS.md`
- **Next:** Team integrates the documented datasets into the processing pipeline.
- **Blockers:** none

---

## mrinalini

**Now working on:** —

<!-- entries -->

_No entries yet._
