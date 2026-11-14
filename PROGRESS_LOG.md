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

**Now working on:** Phase 0 complete — waiting for approval to start Phase 1 (Earth grid)

<!-- entries -->

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
