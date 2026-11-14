# Earth Analogs of Moon and Mars Base Sites

Rank every place on Earth by how closely it resembles a candidate **lunar south-pole base region** or a **Mars landing site**, explain the match feature by feature, and show where the analogy breaks down.

> **Status: Phase 0 complete.** Data inventory verified, Python environment pinned, repository scaffolded. The Earth feature grid, target profiles, similarity engine, API and map follow in Phases 1–7.

## What this is

A data-driven analog finder, not a "this desert looks like Mars" slideshow. Every Earth cell gets a vector of physically comparable measurements (terrain, temperature, dryness, ice/cold-trap proxy). The same features are measured on the Moon and Mars target regions. A weighted percentile-distance score ranks Earth, and every ranking is accompanied by its per-feature breakdown and its limitations.

## Quick start

```bash
# macOS / Linux, from NASA_Space_Challenge/ (use Python 3.11 or 3.12)
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
make phase0                                   # tests + writes docs/data_inventory.md
```

```bash
# Windows, from the repository root
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r NASA_Space_Challenge/requirements.txt
cd NASA_Space_Challenge
python -m backend.pipeline.inspect_datasets   # writes docs/data_inventory.md
python -m pytest -q                           # Phase 0 smoke tests
```

The raw datasets are expected in `../Datasets/` (`Moon/`, `Mars/`, `Earth/`) and are **not** committed. Set `NASA_DATA_ROOT` to override the location.
Teammates can fetch the shared copy (private Hugging Face dataset, ask Rahul for access) with
`hf download rahuloruganti/nasa-analog-data --repo-type dataset --local-dir ../Datasets`.

## Repository layout

```
NASA_Space_Challenge/
  backend/
    pipeline/       one ingestion/regrid script per source dataset
    engine/         percentile normalization, weighted scoring, ranking
    api/            FastAPI application
    paths.py        single source of truth for data locations
  data/             raw/ and processed/ (git-ignored, created by scripts)
  docs/             inventory, feature definitions, figures, submission text
  frontend/         interactive map (Phase 5)
  notebooks/        exploration only
  tests/            one smoke test per phase
```

## Data sources and credits

No data were re-downloaded for this project; the team uses local copies.

| Body | Product | Credit / citation |
|---|---|---|
| Moon | LOLA south-polar DEM and derived roughness/slope/Hurst/spectral-slope products (80°S–pole, 80 m and 1 km) | Barker et al. (2023), *Planetary Science Journal* 4, 183, <https://doi.org/10.3847/PSJ/acf3e1>; NASA GSFC PGDA, data DOI <https://doi.org/10.60903/gsfcpgda-lola-spole> |
| Moon | Permanently shadowed regions > 1 km² polygon table | NASA GSFC PGDA LOLA south-polar products (same DOI) |
| Moon | Global context DEM (`ldem_16.tif`) | NASA SVS lunar DEM, 16 pixels/degree |
| Mars | MOLA MEGDR topography, 16 pixels/degree | MGS MOLA, PDS Geosciences Node, <https://doi.org/10.17189/1519460> |
| Earth | WorldClim 2.1 bioclimatic variables, 2.5 arc-minute | Fick & Hijmans (2017), *International Journal of Climatology* 37(12), 4302–4315, <https://doi.org/10.1002/joc.5086> |
| Earth | ETOPO 2022 global relief, 60 arc-second | NOAA NCEI (2022), <https://doi.org/10.25921/fd45-gt74> |

Full file-level details, local names, sizes and verification results: [`docs/data_inventory.md`](docs/data_inventory.md). Dataset manifest: [`docs/DATASETS.md`](docs/DATASETS.md).

## Honest limits (carried through every output)

- WorldClim provides **air temperature** (1970–2000 climatology), not surface skin temperature. It cannot reproduce lunar or Martian surface temperatures.
- Moon rasters cover only the south-polar stereographic tile (80°S at the edge midpoints; corners reach ~76°S). They are never interpreted as a lon/lat grid.
- Mars MOLA is 16 pixels/degree (~3.7 km); ETOPO is ~1.85 km; lunar terrain products are 80 m–1 km. Features are therefore compared in **kilometre-sized windows**, and coarse sources are explicitly noted.
- Earth cannot reproduce reduced gravity, vacuum or the thin Martian atmosphere, or the radiation environment.
- Moon and Mars temperature values come from cited literature CSVs, never from invented numbers.

## Documentation

- [PLAN.md](PLAN.md) — approach, architecture, workstreams, decisions
- [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) — challenge definition
- [PROGRESS_LOG.md](PROGRESS_LOG.md) — who did what
- [docs/DATASETS.md](docs/DATASETS.md) — dataset manifest
- [docs/data_inventory.md](docs/data_inventory.md) — Phase 0 verification
- [docs/FEATURES.md](docs/FEATURES.md) — feature definitions (proposed, locked in Phase 1)
