# Documentation index

Project overview and setup are in the [root README](../README.md). This folder holds the reference pages, the dataset records, and the reports the pipeline writes.

## Start here

| Page | What it answers |
|---|---|
| [FEATURES.md](FEATURES.md) | What each feature is, how it is computed, and the scoring contract |
| [SITE_ANALYSIS.md](SITE_ANALYSIS.md) | Which Earth sites come out on top, what matches and what does not |
| [API.md](API.md) | The HTTP endpoints served by `backend/api` |
| [../frontend/README.md](../frontend/README.md) | How the globe app works |
| [SUBMISSION.md](SUBMISSION.md) | Pitch, demo storyboard, slide outline, judging checklist |

## Data

| Page | What it answers |
|---|---|
| [DATASETS.md](DATASETS.md) | The datasets the pipeline uses: file names, links, sizes, citations |
| [data_inventory.md](data_inventory.md) | Generated check that every raw file opens, with its grid, CRS and value range (`make inventory`) |
| [DATA_CATALOG.md](DATA_CATALOG.md) | Background survey of what the challenge's data portals offer, including products we did not use |

## Generated reports

These are written by the pipeline and overwritten on every run. Do not edit them by hand.

| Page | Written by | Contents |
|---|---|---|
| [earth_grid_report.md](earth_grid_report.md) | `make features` | Earth grid coverage, feature ranges, spot checks; maps in [figures/](figures/) |
| [phase2_report.md](phase2_report.md) | `make targets` | Moon and Mars target profiles, which features are comparable and why |
| [psr_verification.md](psr_verification.md) | `make targets` | Checks on the lunar permanently-shadowed-region table |
| [hurst_sensitivity.md](hurst_sensitivity.md) | `make targets` | Robustness of the Earth Hurst exponent |
| [phase3_report.md](phase3_report.md) | `make scores` | Similarity definition, coverage, top sites, known-analog scores, sensitivity |

## Engineering notes

| Page | Contents |
|---|---|
| [hardcode_audit.md](hardcode_audit.md) | Audit showing every tunable value lives in `config/`, plus two proofs that a different region or window size runs with no code change |

The two proofs write `docs/proof_*_report.md` and `docs/figures/proof_*.png`. Those outputs are git-ignored; regenerate them with the commands in the audit.

## Figures

`figures/earth_*.png` are quick-look maps of each Earth feature (from `make features`). `figures/app_globe.png` is a screenshot of the app.
