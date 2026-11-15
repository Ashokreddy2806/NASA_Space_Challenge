# Backend API (Phase 4)

```bash
python -m uvicorn backend.api.main:app --port 8000     # interactive docs: http://localhost:8000/docs
```

Needs the precomputed outputs: `python -m backend.pipeline.build_earth_features`, `python -m backend.targets.build_target_profiles`, `python -m backend.engine.build_scores`. Targets: `moon_south_pole`, `mars_jezero`. Custom weights: `weights={"slope_20km_deg":3,"precip_annual_mm":1}` (JSON, keys from `/presets`).

| Endpoint | Purpose |
|---|---|
| `GET /health` | liveness |
| `GET /targets` | targets, scored features, features **not** scored, presets and availability |
| `GET /targets/{t}` | full target profile (value, spread, Earth percentile, limitations) + what Earth cannot replicate |
| `GET /presets` | feature list and preset weights per target |
| `GET /targets/{t}/top-sites?preset=&exclude_famous=&n=&format=json\|geojson` | precomputed top candidates, with or without famous analog regions |
| `GET /targets/{t}/site?lat=&lon=&preset=\|weights=` | per-feature breakdown: Earth value, target value, sub-score, verdict (match >= 80, partial >= 60, else mismatch), weight, limitation note; `does_not_match`, `not_scored`, `earth_cannot_replicate`. 404 over ocean |
| `GET /targets/{t}/score.png?preset=\|weights=&step=` | equirectangular RGBA score map (magma, 40-100, ocean transparent); bounds in `/score-map-info` |

Unavailable presets (thermal_cycling) return 422 with the reason. Responses are served from precomputed NetCDF/JSON; measured latency 2-270 ms (custom-weight PNG about 0.3 s first call, then cached).
