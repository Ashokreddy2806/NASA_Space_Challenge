# Earth Analogs of Moon and Mars Base Sites

Rank every place on Earth by how closely it resembles a candidate **lunar south-pole base region** or a **Mars landing site**, explain the match feature by feature, and show where the analogy breaks down.

> **Status: Phase 3 complete.** The Earth 0.05° feature grid is built, the Moon
> (poleward of 85°S) and Mars (Jezero, 150 km disc) target profiles are computed
> with the same feature registry over the same physical windows, and the
> similarity engine writes global score maps, per-feature evidence and
> non-maximum-suppressed candidate sites for four config-driven presets. Both
> cited thermal tables are ingested as **reference values** and the Moon's polar
> temperature anchors are scored qualitatively; Mars has thermal inertia but no
> temperatures, so its temperature features stay unavailable. All parameters —
> grid, windows, lags, percentiles, targets, weights, presets, bands, top-N,
> separation, famous sites and file names — live in `config/*.yaml`.

## What this is

A data-driven analog finder, not a "this desert looks like Mars" slideshow. Every Earth cell gets a vector of physically comparable measurements (terrain, temperature, dryness, ice/cold-trap proxy). The same features are measured on the Moon and Mars target regions. A weighted percentile-distance score ranks Earth, and every ranking is accompanied by its per-feature breakdown and its limitations.

## Quick start

```bash
# from the repository root
python -m venv .venv
.venv\Scripts\activate            # Windows
python -m pip install -r NASA_Space_Challenge/requirements.txt
cd NASA_Space_Challenge
python -m backend.pipeline.inspect_datasets   # writes docs/data_inventory.md
python -m backend.pipeline.earth_climate      # WorldClim -> 0.05° climate + land mask (~1 min)
python -m backend.pipeline.earth_terrain      # ETOPO -> 0.05° terrain features (~8 min)
python -m backend.pipeline.build_earth_features  # merge, mask, figures, report (~2 min)
python -m backend.targets.build_target_profiles  # Moon + Mars profiles, PSR and Hurst checks (~4 min)
python -m backend.engine.build_scores            # score maps, top sites, sensitivity, report (~1.5 min)
python -m pytest -q                           # Phase 0 + 1 + 2 + 3 tests
```

Proof that configuration drives everything (no code edits):

```bash
python -m backend.pipeline.earth_climate     --config config/proofs/window_30km.yaml
python -m backend.pipeline.earth_terrain     --config config/proofs/window_30km.yaml
python -m backend.pipeline.build_earth_features --config config/proofs/window_30km.yaml
python -m backend.pipeline.earth_climate     --config config/proofs/sahara.yaml
python -m backend.pipeline.earth_terrain     --config config/proofs/sahara.yaml
python -m backend.pipeline.build_earth_features --config config/proofs/sahara.yaml
```

The raw datasets are expected in `../Datasets/` (`Moon/`, `Mars/`, `Earth/`) and are **not** committed. Set `NASA_DATA_ROOT` to override the location.

### Phase 1 outputs

| Path | Contents |
|---|---|
| `data/processed/earth_features.nc` | 7200 × 3600 0.05° grid: relief, slope, three roughness scales, Hurst, five temperature statistics, two precipitation variables (all NaN over ocean), plus `land_mask` and `land_fraction` |
| `data/processed/earth_features_meta.json` | machine-readable ranges, coverage and spot checks |
| `docs/earth_grid_report.md` | coverage, polar notes, spot checks and limits |
| `docs/figures/earth_*.png` | one quick-look map per feature plus a combined overview |

Intermediate files (`earth_terrain.nc`, `earth_climate.nc`) are deleted after a successful merge; run with `--keep-intermediates` to retain them.

### Phase 2 outputs

| Path | Contents |
|---|---|
| `data/processed/target_profiles.json` | Moon and Mars feature distributions (median, p16–p84, min/max, n_cells), resolution verdicts and reasons, PSR ice proxy, cross-check results, group availability and renormalised weights |
| `docs/phase2_report.md` | targets, comparability, per-feature distributions, scoring groups, carried-forward scoring contract |
| `docs/psr_verification.md` | data-driven PSR checks: CRS interpretation, DEM extent, topographic position, slope finding |
| `docs/hurst_sensitivity.md` | Earth Hurst with and without the 2 km lag |

### Phase 3 outputs

| Path | Contents |
|---|---|
| `data/processed/scores_moon.nc`, `scores_mars.nc` | per-group similarity grids and one score grid per preset, area-weighted on the 0.05° grid, plus the preset coverage grid |
| `data/processed/top_sites.json` | for each target and preset: renormalised weights, coverage, score statistics, NMS sites with and without famous analogs, per-feature absolute gap / rank similarity / hidden-gap flag, validation sites, thermal sensitivity |
| `docs/phase3_report.md` | similarity definition, coverage per target, per-feature evidence, top sites, analog results, sensitivity verdict, what does not match |

Scores are **Earth-relative**. A Moon score and a Mars score are never
comparable: they use different feature sets, different coverage and different
target distributions.

## Repository layout

```
NASA_Space_Challenge/
  backend/
    config.py       typed loader for config/*.yaml (grid, features, targets, paths)
    features/       the single feature registry used by Earth, Moon and Mars
    targets/        Moon/Mars profiles, PSR verification, thermal reader, Hurst check
    pipeline/       one ingestion/regrid script per source dataset
    engine/         similarity maths, NMS top sites, score builds and reports
    api/            FastAPI application
    paths.py        single source of truth for data locations
  config/           every tunable value: grid, windows, lags, targets, sites, files
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
- Moon and Mars temperature values come from cited literature CSVs, never from invented numbers. They are reference numbers, not per-cell maps, so Moon temperature is scored **qualitatively** (banded polar anchors) and Mars temperature is unavailable.
- No Earth substrate, mineralogy or thermal-inertia map is in this build, so a smooth ice sheet and a smooth rock plain are indistinguishable to the terrain features. The Mars ranking is a terrain result, not a composition result.

## Documentation

- [PLAN.md](PLAN.md) — approach, architecture, workstreams, decisions
- [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) — challenge definition
- [PROGRESS_LOG.md](PROGRESS_LOG.md) — who did what
- [docs/DATASETS.md](docs/DATASETS.md) — dataset manifest
- [docs/data_inventory.md](docs/data_inventory.md) — Phase 0 verification
- [docs/FEATURES.md](docs/FEATURES.md) — locked feature definitions, Phase 1–3 implementation records
- [docs/hardcode_audit.md](docs/hardcode_audit.md) — no-hard-coding audit and the configuration proofs
- [docs/phase2_report.md](docs/phase2_report.md) — Moon and Mars target profiles
- [docs/phase3_report.md](docs/phase3_report.md) — similarity engine, score maps and candidate sites
- [docs/psr_verification.md](docs/psr_verification.md) — data-driven PSR checks
- [docs/hurst_sensitivity.md](docs/hurst_sensitivity.md) — Earth Hurst robustness
- [docs/earth_grid_report.md](docs/earth_grid_report.md) — Phase 1 grid coverage and limits
