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

**Now working on:** project docs and resources setup

<!-- entries -->

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
