# Feature definitions

> **Status: locked for Phase 1 (2026-11-14).** This file is the contract for what
> "similar" means. The Earth implementation is finished and its exact definitions
> are recorded at the end of this file. Phase 2 must measure the Moon and Mars
> targets the same physical way; any change must be recorded in `PLAN.md`
> Decisions.

The core rule: a feature is only comparable if it is measured the **same physical
way** on every body. Pixel windows are therefore converted to kilometres, and
each body's values are converted to percentiles *within that body* before any
distance is computed.

## MVP features (6)

| # | Feature | Earth measurement | Moon target | Mars target | Units |
|---|---|---|---|---|---|
| 1 | **Relief** | ETOPO elevation: p95−p5 range in a 20 km window | LOLA `LDEM_80S_80MPP_ADJ` same window | MOLA 16 ppd DEM same window | m |
| 2 | **Slope** | ETOPO gradient magnitude per 2 km cell, mean in a 20 km window | LOLA DEM gradient / `SLP_800M`, `SLP_1600M` | MOLA DEM gradient | degrees |
| 3 | **Roughness (multi-scale)** | ETOPO high-pass residual standard deviation at 5, 10 and 20 km windows | LOLA `ROUGH_800M`, `ROUGH_1600M` and DEM residuals | MOLA DEM residuals, limited by 3.7 km pixels | m |
| 4 | **Scale-robust roughness** | Hurst exponent from log–log elevation structure function over 2–32 km | LOLA `H` and `SPSLP` products | MOLA-derived Hurst where resolution allows; otherwise flagged unavailable | unitless / σ per km |
| 5 | **Temperature statistics and swing** | WorldClim `bio_1` (mean), `bio_2` (diurnal range proxy), `bio_5` (warmest month max), `bio_6` (coldest month min), `bio_7` (annual range) | Literature CSV (`moon_thermal_literature.csv`) | Literature CSV (`mars_thermal_literature.csv`) | °C |
| 6 | **Dryness** | WorldClim `bio_12` (annual precipitation), `bio_14` (driest-month precipitation) | Airless: treated as one-sided "drier than any Earth desert" constraint, not a measured target value | Hyper-arid: same one-sided treatment | mm |

### Ice / cold-trap proxy (MVP auxiliary dimension)

| Body | Measurement | Why |
|---|---|---|
| Moon | Fraction of a cell covered by permanently shadowed regions (PSR polygon table `LPSR_80S_20MPP_ADJ_1km2.csv`) | Cold traps are the resource/ice story for a south-pole base |
| Earth | `bio_6` cold extremes (coldest-month minimum air temperature) | Best available global proxy for persistent cold; **not** a radiation or vacuum proxy |
| Mars | Not in MVP | No comparable mapped cold-trap product in the downloaded data |

The ice proxy is reported as a separate sub-score, not silently mixed into the six terrain/climate features.

## Definitions in detail

### 1. Relief
Robust elevation range within a moving window of **20 km**: `p95(z) − p5(z)`.
A percentile range is used instead of max−min so a single artefact or crater rim
does not dominate. On Earth the range is computed on a **2 km metric working
grid** built for each 10° tile, then area-averaged onto the 0.05° search grid.
Lunar and Martian DEMs are measured in their native projected grids, where the
pixel size is known in metres; Phase 2 must use the same percentile range.

### 2. Slope
Gradient magnitude of the DEM in the local projected coordinate system,
expressed in degrees, averaged over a **20 km** window. The per-cell gradient is
computed at the 2 km working resolution first, so a 20 km mean slope is the
typical grade a traverse would meet, not a slope derived from a smoothed DEM.
For the Moon the published `SLP_800M` / `SLP_1600M` products are used as a
cross-check; the DEM-derived value is used for like-for-like comparison.
Never compute lunar slope from `ldem_16.tif` (no georeferencing, distorted pole).

### 3. Roughness (multi-scale)
Elevation residual after removing the local low-frequency surface (Gaussian
high-pass with `σ = window/2`), summarised by the standard deviation (`std`) of
that residual in windows of **5, 10 and 20 km**. The three values are kept as
separate sub-features so a site that is smooth at 5 km but broken at 20 km is
not flattened into one number. Lunar `ROUGH_800M` and `ROUGH_1600M` provide
independent published checks. Phase 2 must apply the same high-pass + std
recipe, not a different roughness estimator.

### 4. Scale-robust roughness
How roughness changes with scale. On the Moon, use the published **Hurst
exponent** (`H`) and **spectral slope** (`SPSLP`) products. On Earth, estimate a
Hurst exponent from the slope of `log(structure function)` versus `log(lag)` for
lags of **2, 4, 8, 16, 32 km** inside a fixed 32 km analysis window.
Mars: attempt the same over lags ≥ 2 MOLA pixels (~7.4 km); if too few lags are
stable, mark the feature **unavailable** rather than inventing a value.

### 5. Temperature statistics and swing
Five sub-features: annual mean, diurnal range, warmest-month maximum,
coldest-month minimum, annual range.

- Earth: WorldClim `bio_1`, `bio_2`, `bio_5`, `bio_6`, `bio_7` — **air**
  temperature, 1970–2000 climatology, 2.5 arc-minute.
- Moon and Mars: values read only from the hand-made, cited literature CSVs
  (`feature,value,units,source`). Each target value carries its source and its
  measurement type (surface vs air, day vs night, equator vs pole).
- No satellite temperature raster is used or implied. Missing literature values
  are reported as missing; they are never filled with guesses.

### 6. Dryness
Earth: `bio_12` annual precipitation and `bio_14` driest-month precipitation.
The Moon has no atmosphere and Mars is hyper-arid, so dryness is a **one-sided
constraint**: an Earth site can be "not dry enough", but a wet target value is
not fabricated. This dimension mainly separates true desert candidates from
merely cold or rocky ones.

## Phase 1 implementation record (Earth)

Locked 2026-11-14; code in `backend/pipeline/earth_terrain.py` and
`backend/pipeline/earth_climate.py`. The published file is
`data/processed/earth_features.nc`, global **0.05°** (7200 × 3600 cell centres).

| Variable | Sub-feature | Exact computation |
|---|---|---|
| `relief_20km_m` | relief | `p95 − p5` of elevation in a 20 km square window (11 px on the 2 km working grid) |
| `slope_20km_deg` | slope | `atan(|∇z|)` per 2 km cell, then mean in a 20 km window |
| `roughness_5km_m` | roughness | std of `z − Gaussian(z, σ = 2.5 km)` in a 5 km window |
| `roughness_10km_m` | roughness | std of `z − Gaussian(z, σ = 5 km)` in a 10 km window |
| `roughness_20km_m` | roughness | std of `z − Gaussian(z, σ = 10 km)` in a 20 km window |
| `hurst_2_32km` | scale-robust roughness | OLS slope of `log` structure function against `log` lags 2/4/8/16/32 km in a 32 km window; `H = slope/2`, clipped to 0–1.5 |
| `temp_mean_c` | temperature | WorldClim `bio_1`, area-averaged from 2.5′ |
| `temp_diurnal_range_c` | temperature | WorldClim `bio_2` (day–night swing proxy) |
| `temp_max_warmest_c` | temperature | WorldClim `bio_5` |
| `temp_min_coldest_c` | temperature | WorldClim `bio_6`; also the Earth **ice/cold-trap proxy** (attribute `role`) |
| `temp_annual_range_c` | temperature | WorldClim `bio_7` |
| `precip_annual_mm` | dryness | WorldClim `bio_12` |
| `precip_driest_month_mm` | dryness | WorldClim `bio_14` |

Implementation rules:

- **Working grid.** Each 10° × 10° tile (1° halo) is reprojected from the 1.85 km
  ETOPO DEM to a local azimuthal-equidistant grid at 2 km. Features are computed
  there in kilometre windows and area-averaged onto the 0.05° search grid.
- **Land mask.** WorldClim ocean nodata (majority-valid rule at 0.05°). All
  features are NaN over ocean.
- **Coastal handling.** ETOPO includes bathymetry, so ocean cells are replaced
  with the nearest land elevation (WorldClim mask) *before* filtering. Without
  this, a 20 km window at the coast would include the continental shelf and
  report a spurious multi-kilometre relief cliff.
- **NaN policy.** Isolated ETOPO voids are filled with the nearest finite value
  *inside a tile* for filtering only; no feature value is invented.
- **0.05° cells are not equal-area.** Near the poles a cell is much narrower in
  longitude than at the equator. Terrain features come from the 2 km working
  grid, so adjacent polar cells can repeat one sample. This is documented in
  `docs/earth_grid_report.md`; the ranker must area-weight rather than count cells.
- **Temperature type.** WorldClim is air temperature, not surface skin
  temperature. It is a climate analog, not a radiation or vacuum analog.
- **Dryness is one-sided.** No lunar/Martian precipitation value is fabricated;
  the scorer treats "drier than Earth's driest desert" as a constraint.

## Phase 2 implementation record (Moon and Mars)

Phase 2 does **not** define a second estimator. `backend/features/registry.py` is
the only implementation; `config/targets.yaml` says which body, which region and
which native pixel size. The same physical windows and lags are used everywhere,
and a feature is only computed where the native source resolves its window.

**Comparability rule** (`config.yaml → comparability`). A window is `resolved`
when it spans at least 2.5 native pixels, `marginal` between 2.5 and 4.0, and
`unavailable` below 2.5. Hurst additionally needs at least 3 usable lags, each
spanning 2.5 pixels. An unavailable feature gets a reason and no number; it is
excluded from the target score and the remaining group weights are renormalised.

| Body | Source | Native pixel | Region | Cells | Result |
|---|---|---|---|---|---|
| Moon | `LDEM_80S_80MPP_ADJ.tiff` | 80 m | poleward of 85°S, 151.713 km disc | 11,298,124 (706,141 sampled, stride 4) | all six terrain features resolved |
| Mars | `megt90n000eb.img` (raw MOLA, 16 ppd) | ≈3.70 km | Jezero 18.3628°N 77.5945°E, 150 km disc | 5,169 | 5 km roughness and Hurst unavailable; 10 km roughness marginal |

The Moon is processed block-wise (1024 px cores, 36 km halo) so every window near
a block edge sees real neighbouring terrain. Mars is reprojected from the raw
0–360°E MOLA grid to a local azimuthal-equidistant grid on a Mars sphere. The
configured Jezero elevation (−2656 m) is checked against the nearest MOLA cell
(−2663 m, Δ −7 m), which confirms the grid orientation.

**Moon medians** (p16–p84): relief 1789 m (925–3003), slope 9.29° (6.26–12.29),
roughness 5/10/20 km = 77/170/374 m, Hurst 0.683 (0.566–0.812). PSR area fraction
inside the disc is 0.0983 (7,110 km² of 72,308 km², 366 of 1,531 polygons).

**Mars medians**: relief 472 m (242–897), slope 1.47° (0.83–2.65), roughness
10 km 40 m (marginal), roughness 20 km 85 m. Mars has **no** surface-temperature
range in the supplied literature, so the two range features are unavailable by
configuration and excluded; the remaining weights are renormalised.

**Cross-check against the published LOLA products.** The profile values come
from the 80 m DEM. The pre-computed layers are used only to test that
recomputation on a like-for-like 1 km grid:

| Our computation | LOLA layer | Pearson r | Our median | LOLA median |
|---|---|---|---|---|
| slope at 1.6 km | `SLP_1600M` | 0.983 | 8.20° | 7.24° |
| roughness at 0.8 km | `ROUGH_800M` | 0.882 | 6.32 m | 3.96 m |
| Hurst 2–32 km | `H` | −0.15 | 0.683 | 0.971 |

Slope and roughness agree well. The LOLA `H` layer is nearly saturated (median
0.971, p05 0.72, p95 1.02), so it cannot confirm a structure-function exponent
that spans a real range; it is reported as a weak cross-check, not as agreement.

**PSR verification** (`docs/psr_verification.md`). The CSV has no CRS field, so
the polygons are read as metres in the LDEM south-polar-stereographic CRS taken
from the DEM. All 1,531 polygons fall inside the DEM extent, 366 lie in the
85°S disc, and the rasterised PSRs sit 1,213 m below the background median
elevation (77% of PSR pixels below it). Their median slope is **10.30° vs 9.18°**
for the background, i.e. PSRs are slightly *steeper* than their surroundings.
That is the **expected** result, not a failure: a PSR polygon is the shadowed
floor *plus* the crater wall and rim that cast the shadow, so a strict
"lower slopes than background" test cannot pass by construction. The numbers
stay in the report; the topographic-low test is the alignment evidence. The
~76°S tile-corner radius (429.9 km) is far outside the 151.7 km target cap, so
the corner clip cannot truncate the region of interest.

**Earth Hurst robustness.** Recomputing on 504 random ETOPO patches, dropping the
2 km lag (ETOPO native ≈1.85 km) shifts the median H by +0.040 and leaves the two
estimates correlated at r=0.990 (`docs/hurst_sensitivity.md`). The nested fit is
robust enough to compare across bodies, with that small positive bias recorded.

**Thermal values.** Both hand-made tables arrived on 2026-11-15 and are read from
disk, never guessed. They use a flat `feature,value,units,source` schema: **10
cited Moon quantities** (subsolar maximum, night typical, PSR and cold-crater
bounds, cold-trap threshold) and **4 Mars quantities, all thermal inertia** —
Mars has *no* surface temperatures at all. Kelvin values are converted to °C by
exact −273.15 offset, and two bracketing `*_min`/`*_max` pairs per body are
combined into **derived ranges** that name both inputs and the rule. These are
reference numbers, not per-cell maps, so they are deliberately **not** turned
into target distributions and **not** compared numerically with WorldClim 2 m
air temperature. All temperature features therefore remain `unavailable` for
Moon and Mars, and the qualitative-anchor mapping is a Phase 3 decision awaiting
approval.

## Normalization and scoring (Phase 3 contract)

1. Convert each feature to a percentile rank **within its own body's valid
   cells** (Earth land; Moon polar tile; Mars target region). Rank similarity is
   `1 − |p_earth,f − p_target,f|`.
2. **Also** report the absolute gap in real units, `Earth value − target median`,
   and how many target p16–p84 spreads that gap is worth. This is mandatory: a
   rank can look close while the real difference is enormous (the Moon's
   day–night swing is hundreds of kelvin; an Earth desert that ranks near it is
   still nowhere near it in absolute terms). Every site card must show the
   absolute gap, with a plain-language note where rank similarity hides a large
   real-unit difference.
3. Overall score: weighted mean of available sub-scores; weights adjustable in
   the UI, with presets for rover mobility, cold-trap/ice and thermal cycling.
   Unavailable features carry no score and the remaining weights are
   renormalised (the Phase 2 reports give the renormalised weights per body).
4. Report the weight vector, the per-feature sub-scores, the absolute gaps, and
   any feature that is unavailable for a body. A high score with an unavailable
   ice proxy must not look like a high-confidence ice analog.

## Window and resolution policy

| Source | Native resolution | Role |
|---|---|---|
| LOLA polar DEM | 80 m | Moon terrain truth |
| LOLA derived products | 1 km | Moon roughness/slope/Hurst cross-checks |
| MOLA MEGDR | 16 ppd (~3.7 km) | Mars terrain; smallest honest window ≥ ~7.4 km |
| ETOPO 2022 | 60 arc-sec (~1.85 km) | Earth terrain |
| WorldClim 2.1 | 2.5 arc-min (~4.6 km) | Earth climate |

Analysis windows are defined in kilometres (5, 10, 20, 2–32 km). Where a target
body cannot resolve a window, the feature is marked as limited or unavailable
rather than silently comparing a 5 km Earth texture with a 3.7 km Mars pixel.
