# Hard-code audit and config retrofit

Phase 1 was approved with one required retrofit: **no hard-coding**. This
document records what was audited, what moved into `config/`, what deliberately
stayed in code, and the two proofs that the configuration layer really drives
the pipeline.

Status: complete for `backend/`. Every scientific parameter, file name, target
coordinate and validation site now comes from `config/*.yaml`.

---

## 1. Method

The audit was a targeted grep over `backend/` (plus `tests/`), repeated after the
refactor to confirm the surface shrank. The patterns looked for:

- grid and resolution numbers: `0.05`, `7200`, `3600`, `2000`, `10.0`, `1.0`
- window and lag sizes: `20.0`, `32.0`, `5.0`, `10.0`, `2.0`, `16.0`
- percentile definitions: `percentile`, `95`, `5`
- source file names: `ETOPO`, `wc2.1`, `LDEM`, `LDRM`, `megt`, `LPSR`, `.tif`,
  `.img`, `.csv`, `.nc`
- target coordinates and names: `85`, `18.3628`, `77.5945`, `2656`, `Jezero`
- validation sites: `Atacama`, `Dry Valleys`, `Devon`, `Death Valley`,
  `Iceland`, `Sahara`, `Amazon`

Each hit was classified as **moved to config**, **definitional** (a fact about
the coordinate system or a CRS, not a project setting), or **presentation**
(a layout constant with no scientific effect).

## 2. What moved into `config/`

| Literal / behaviour | Old location | New home |
|---|---|---|
| 0.05° grid, global bounds | `earth_grid.py` module constants | `config.yaml` → `grid` |
| 10° tiles, 1° halo | `earth_grid.py` | `config.yaml` → `grid.tile_deg`, `grid.halo_deg` |
| 2 km local working grid | `earth_grid.py` (`LOCAL_PIXEL_M`) | `config.yaml` → `grid.working_pixel_m` |
| NetCDF chunk shape 360×720 | `feature_store.py` (`CHUNK_ROWS/COLS`) | `config.yaml` → `grid.chunk_rows/chunk_cols` |
| NetCDF compression level | `feature_store.py` | `config.yaml` → `storage.compression_level` |
| Land-mask source layer and 0.5 threshold | `earth_climate.py` (as `"wc2.1_2.5m_bio_1.tif"`) | `config.yaml` → `earth.land_mask_source`, `earth.land_mask_threshold` |
| ETOPO native 1.85 km | prose in reports | `config.yaml` → `earth.native_pixel_m` |
| Relief 20 km, p5–p95 | `earth_terrain.py` (`FEATURE_ATTRS`, `compute_terrain_features`) | `features.yaml` → `relief_20km_m.params` |
| Slope 20 km | `earth_terrain.py` | `features.yaml` → `slope_20km_deg.params` |
| Roughness 5/10/20 km, σ = window/2 | `earth_terrain.py` literal tuple `(5.0, 10.0, 20.0)` | `features.yaml` → three `roughness` entries |
| Hurst lags 2/4/8/16/32 km, 32 km window | `earth_terrain.py` default args | `features.yaml` → `hurst_2_32km.params` |
| Percentile stretch, stride, dpi, overview grid | `build_earth_features.py` | `config.yaml` → `figures` |
| Zone thresholds (66.5°), axis ticks | `build_earth_features.py` | `config.yaml` → `report` |
| Feature order, units, long names, colour maps | four separate copies across modules | `features.yaml` (single registry) |
| Group weights for scoring | not present | `features.yaml` → `groups` |
| Earth terrain + 19 WorldClim file names | `earth_climate.py`, `inspect_datasets.py` | `paths.yaml` → `sources`, `inventory.yaml` |
| Output file names, figure prefixes, docs routing | `build_earth_features.py`, module constants | `paths.yaml` → `outputs` |
| Validation sites and their expected bounds | `build_earth_features.py` + `tests/test_phase1.py` | `validation_sites.yaml` |
| Moon target (poleward of 85°S) | prose only | `targets.yaml` → `moon.region.lat_min/lat_max` |
| Mars target (Jezero 18.3628 N, 77.5945 E, −2656 m, 150 km) | prose only | `targets.yaml` → `mars.site` |
| MOLA 16 ppd and orientation check points | `inspect_datasets.py` | `inventory.yaml` → `mars.pixels_per_degree`, `orientation_checks` |
| Comparability thresholds (window/lag pixels) | not present | `config.yaml` → `comparability` |
| Moon target region, block size, halo margin, PSR area floor, cross-check products | not present | `targets.yaml` → `moon` |
| Mars site, radius, sphere radius, MOLA grid facts, unavailable features | not present | `targets.yaml` → `mars`; `inventory.yaml` |
| Thermal table file names and scoring groups | not present | `paths.yaml` → `sources.*.thermal`, `targets.yaml` → `thermal_groups` |
| Hurst sensitivity sample count, seed, patch size, drop lag, verdict thresholds | not present | `config.yaml` → `hurst_sensitivity` |
| Distribution sample stride | not present | `config.yaml` → `distribution.sample_stride_px` |
| Similarity kernel, spread floor, hidden-gap thresholds, CDF quantiles | not present | `config.yaml` → `scoring` |
| Four presets: weights, labels, top-N, minimum separation | not present | `presets.yaml` |
| Famous-site list and matching radius | not present | `validation_sites.yaml` → `famous`, `famous_radius_km` |
| Thermal sensitivity grid, sample count, seed, top-N | not present | `config.yaml` → `thermal_sensitivity` |
| Per-site stability match fraction | not present | `config.yaml` → `thermal_sensitivity.stability_match_fraction` |
| No-precipitation constraint: target value, tolerance band, label, weight note | not present | `config.yaml` → `physical_constraints.dryness` |
| Dryness weight per preset and group weight | not present | `presets.yaml`, `features.yaml` → groups |
| Per-body dryness reason and enable/disable | not present | `targets.yaml` → `*.dryness_constraint` |
| Ice/substrate caveat boxes, label, text, heuristic flag | not present | `config.yaml` → `caveats` |
| Analog provenance: reviewed, display_source, citation_verified | prose only | `validation_sites.yaml` → `analogs` |

Two structural changes came with this:

1. **One feature registry** — `backend/features/registry.py`. Every feature is a
   function `(dem, pixel_m, params, options) -> array`; `config/features.yaml`
   names the function and supplies the parameters. Earth, Moon and Mars all call
   `registry.compute_all(...)`. There is no second implementation anywhere.
2. **One grid description** — `backend/config.py::GridSpec` drives tiling,
   local reprojection, chunking and sampling, and supports arbitrary bounds, so
   a regional run is a config change rather than a code change.

## 3. What deliberately stayed in code

These are not project settings, so they are not in `config/`:

| Code value | Why it stays |
|---|---|
| `GLOBE_LON_MIN…GLOBE_LAT_MAX` in `earth_grid.py` | Limits of the lon/lat coordinate system itself (a padded tile may never exceed ±180/±90). The *search* bounds are configured. |
| `EPSG:4326`, `+proj=aeqd`, WGS84 | CRS identity, not a tunable. Changing it would change what "latitude" means. |
| `sigma_px = max(0.75, …)` in `registry.roughness` | Numerical guard: a Gaussian σ below ~1 pixel is not resolvable on any grid. The window and σ fraction are configured. |
| `np.clip(hurst, 0.0, 1.5)` | Physical output domain of an H estimate; documented in the feature definition. |
| `273.15` in `thermal.py` | Kelvin→Celsius zero offset: a definitional constant, applied exactly and recorded in each converted entry. |
| `1.2` padding in `mars_target._lonlat_window` | Numerical safety margin so the reprojected Mars disc is fully covered; it adds data, never truncates. |
| `distance_transform_edt`, `np.gradient`, `uniform_filter` | Algorithm choice, not a parameter. |
| `complevel`, `zlib`, `shuffle` flags | Storage mechanics; the level itself is configured. |
| `figsize`, `fontsize`, label offsets in `build_earth_features.py` | Presentation only: they change the PNG layout, never a number in the data or report. |
| Source facts in prose (ETOPO 60 arc-sec, WorldClim 2.5 arc-min, MOLA 16 ppd, DOIs) | Dataset citation, required in the report; the numbers that *drive computation* are configured. |

Re-running the audit grep after the refactor returns only rows from this table
(plus the report prose above), i.e. no remaining scientific parameter, file name,
target coordinate or site name in `backend/`.

## 4. Proof 1 — change one config value, outputs change

`config/proofs/window_30km.yaml` changes **one** parameter, the relief window
(20 km → 30 km), through the loader's `features.yaml → overrides` mechanism. No
Python file is edited. Outputs go to `proof_window_*` names so the real Phase 1
products are untouched.

```
.venv/Scripts/python -m backend.pipeline.earth_climate --config config/proofs/window_30km.yaml
.venv/Scripts/python -m backend.pipeline.earth_terrain --config config/proofs/window_30km.yaml
.venv/Scripts/python -m backend.pipeline.build_earth_features --config config/proofs/window_30km.yaml
```

| Quantity | Default (20 km window) | Proof (30 km window) |
|---|---|---|
| `relief_20km_m` land median | 78.70 m | 104.36 m |
| `relief_20km_m` land max | 4,169.99 m | 4,709.58 m |
| `relief_20km_m` valid cells | 8,712,831 | 8,712,831 |
| Every other feature | — | identical (medians, maxima and valid-cell counts match to machine precision) |

The run itself was unchanged apart from the window: climate 51.8 s, terrain
471.4 s (648 tiles), merge 50.0 s. The relief median rises by 33% and the maximum
by 540 m, which is the expected effect of a larger percentile window. Twelve
other features, including the other two roughness scales and the Hurst exponent,
are unchanged.

## 5. Proof 2 — different bounding box, config only

`config/proofs/sahara.yaml` changes `config.yaml → grid` to a Saharan box
(`lon -20…40`, `lat 10…40`) and the output names. Nothing else.

```
.venv/Scripts/python -m backend.pipeline.earth_climate --config config/proofs/sahara.yaml
.venv/Scripts/python -m backend.pipeline.earth_terrain --config config/proofs/sahara.yaml
.venv/Scripts/python -m backend.pipeline.build_earth_features --config config/proofs/sahara.yaml
```

Result: a 1200 × 600 cell grid, 18 tiles (terrain 20.2 s), `docs/proof_sahara_report.md`
and a complete 14-figure set, all from configuration. The pipeline produced real
halo data beyond the box (tile bounds are padded up to the coordinate limits), so
edge features are not degraded. Validation sites outside the box — which is all
seven configured sites, since the box is lon −20…40, lat 10…40 — are reported as
`outside` in the spot-check table instead of being silently clamped, and the
polar-zone rows correctly say `n/a (outside grid)`.

## 6. Tests

`tests/` reads its grid, feature ids, file names, sites, target coordinates and
expected bounds from the same YAML files; `tests/test_config.py` asserts that
config values are what the code uses, that the proof overrides change only their
intended keys, that targets and distribution percentiles come from YAML, and that
the registry refuses unknown feature functions. `tests/test_phase2.py` adds PSR
parsing/rasterising/verification, the thermal readers (long statistic table, flat
reference table, exact Kelvin conversion, derived ranges, missing table),
the Mars profile's unavailable-window reasons, and group-weight renormalisation.
`tests/test_phase3.py` adds the absolute/rank similarity maths, the floored spread,
band-distance scoring, area-weighted percentiles and group means, preset
renormalisation and NaN propagation, NMS separation, high-latitude site
aggregation, famous-site filtering, the hidden-gap flag, the qualitative
feature rows, and the structure of `top_sites.json` / `scores_*.nc` including the
configured weights, top-N and separation. Phase 3b adds the declared
no-precipitation constraint (entries, group status, floored scale, coverage),
caveat regions, per-site stability and stability ranking, both site lists for
every preset, and analog source provenance. Every value is read from
`config/*.yaml`; the tests contain no target coordinate, window or weight.
`pytest` → **114 passed**.

## 7. Reproducing the audit

```
# 1. the greps (from NASA_Space_Challenge/)
rg -n "0\.05|7200|3600|2_000|20\.0|32\.0" backend
rg -n "ETOPO|wc2\.1|LDEM|LDRM|megt|LPSR" backend
rg -n "Atacama|Dry Valleys|Devon|Death Valley|Iceland|Sahara|Jezero|2656" backend

# 2. the proofs
python -m backend.pipeline.earth_climate --config config/proofs/window_30km.yaml
python -m backend.pipeline.earth_terrain  --config config/proofs/window_30km.yaml
python -m backend.pipeline.build_earth_features --config config/proofs/window_30km.yaml

# 3. the suite
python -m pytest tests -q
```

`rg` is not installed on this machine; the same searches were run with the
editor's content search and reproduced here for teammates who have it.
