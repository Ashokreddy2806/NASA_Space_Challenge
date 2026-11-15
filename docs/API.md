# Backend API

A read-only FastAPI application over the precomputed outputs. Nothing heavy runs at request time.

```bash
make serve        # or: python -m uvicorn backend.api.main:app --port 8000
```

- App: <http://localhost:8000/>
- Interactive API docs: <http://localhost:8000/docs>

It needs the outputs of `make all` in `data/processed/` (`earth_features.nc`, `target_profiles.json`, `scores_moon.nc`, `scores_mars.nc`, `top_sites.json`).

## Conventions

- **Targets** are `moon` (lunar cap poleward of 85°S) and `mars` (150 km disc around Jezero crater).
- **Scores** are 0 to 1 and Earth-relative. A Moon score and a Mars score are never comparable.
- **Presets** are `balanced`, `rover_mobility`, `cold_trap_ice` and `thermal_cycling`, defined in `config/presets.yaml`.
- **Groups** are `relief`, `slope`, `roughness`, `scale_robust_roughness`, `temperature` and `dryness`. A group a target cannot support is dropped and the remaining weights are renormalised (Mars has no `scale_robust_roughness` or `temperature`).
- **Custom weights** are a JSON object over the groups, for example `weights={"relief":1,"slope":2}`. Values must be non-negative.

## Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Liveness and the list of targets |
| `GET /targets` | Each target with its extent, scored groups, groups not scored (with reasons), presets and coverage |
| `GET /targets/{target}` | Full target profile: per-feature distributions, resolution status, ice proxy, thermal references, and what Earth cannot replicate |
| `GET /presets` | Group list and the presets per target, with the weights actually used after renormalisation |
| `GET /targets/{target}/top-sites` | Ranked candidate sites with per-feature evidence |
| `GET /targets/{target}/site` | Evidence for any single Earth cell |
| `GET /targets/{target}/validation` | Known analog sites and spot checks as scored by the engine |
| `GET /targets/{target}/score.png` | Global score map as a transparent PNG |
| `GET /score-map-info` | Bounds, projection and colour scaling of the score PNG |

### `GET /targets/{target}/top-sites`

| Parameter | Default | Meaning |
|---|---|---|
| `preset` | `balanced` | Priority preset |
| `exclude_famous` | `false` | Drop sites within 100 km of a famous analog |
| `n` | `10` | Number of sites, 1 to 25 |
| `format` | `json` | `json` or `geojson` |

Each site has `lat`, `lon`, `site_score` (area-averaged over 25 km), `peak_score`, `group_scores`, `famous` / `famous_name`, `caveats` (for example the ice-sheet flag), `stability` (fraction of the nine thermal sensitivity runs in which the site stays in the top list; balanced preset only) and `features`.

### `GET /targets/{target}/site`

| Parameter | Meaning |
|---|---|
| `lat`, `lon` | Location; required |
| `preset` or `weights` | Preset name, or custom weights as JSON |

Returns `score`, `weights_used`, `group_scores`, `features`, `hidden_gaps`, `not_scored`, `famous_near` and `earth_cannot_replicate`. Returns 404 over ocean.

Each entry in `features` carries the evidence for one feature:

| Field | Meaning |
|---|---|
| `value`, `target_median`, `units` | Earth value and target value in real units |
| `absolute_gap` | Earth minus target, in real units |
| `absolute_similarity` | 0 to 1 closeness in real units, scaled by the target's spread |
| `earth_percentile`, `target_percentile`, `rank_similarity` | Where each value sits on Earth's land distribution, and how close those ranks are |
| `hidden_real_unit_gap` | True when the ranks agree but the real-unit gap is large; such features are also listed in `hidden_gaps` |
| `qualitative` | True for banded evidence (lunar temperature anchors) |
| `physical_constraint` | True for the declared no-precipitation constraint |

### `GET /targets/{target}/score.png`

| Parameter | Default | Meaning |
|---|---|---|
| `preset` or `weights` | `balanced` | What to draw |
| `step` | `5` | Decimation of the 0.05° grid, 1 to 20 (5 gives 0.25°) |

An equirectangular (EPSG:4326) RGBA image covering -180 to 180 and -90 to 90, magma colour map, scaled from the land median to the best site, ocean transparent. Responses are cached.

## Errors

| Status | When |
|---|---|
| 404 | Unknown target, or no land data at the requested location |
| 422 | Unknown or unavailable preset, or malformed weights |

## Example

```bash
curl "http://localhost:8000/targets/mars/top-sites?n=3&exclude_famous=true"
```

```bash
curl "http://localhost:8000/targets/moon/site?lat=-10.275&lon=-77.575&preset=balanced"
```
