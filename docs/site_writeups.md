# Site write-ups: Earth analogs for the lunar south pole and Jezero Crater

Generated from `docs/top_sites.json`, `docs/target_profiles.json`, `docs/validation.md` and `data/processed/earth_features.nc` by `backend/engine/write_sites.py`.

## How to read this

- Candidates are Earth 0.05 degree land cells (about 5.6 km north-south). Each list keeps sites at least 300 km apart.
- Score (0-100) = 100 x (1 - D). D is a weighted average of scaled physical distances: each feature is log1p-transformed (dryness uses log1p(x / reference)) and divided by its Earth P95-P5 span.
- Sub-score = 100 x (1 - distance) per feature. Verdict: match >= 80, partial >= 60, mismatch < 60, as in the API.
- Rank is the position in the list under each site. It is not a probability, and neighbouring scores are close.
- Place names are the nearest GeoNames place with population over 1,000, found offline with the `reverse_geocoder` package (GeoNames data, CC BY 4.0). They name the nearest settlement, not the site.
- Famous-site check: a site is flagged when it lies inside the exclusion radius of a region in `backend/engine/similarity.py` (FAMOUS).

## What Earth cannot replicate

- Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Moon gravity is 1/6 g and Mars gravity is 0.38 g.
- Moon temperatures are Diviner surface (skin) values compared with WorldClim air temperature. This is not like-for-like.
- Mars has no temperature, mineral or dust data in this ranking.
- Scores within each top list are near-ties (spreads are given under each target), so the order inside a list is provisional.

## Lunar south pole (poleward of 85S)

Target: disk of radius 151.7 km around the pole in the Moon 2015 polar stereographic grid. Method: LOLA LDEM_80S_80MPP_ADJ area-averaged to a 2 km grid; Earth estimators applied; median and p10-p90 over the disk. Resolution: 80 m source, 2 km working grid, windows 5-32 km.

- Not used (no target value): temp_diurnal_range_c (missing_no_source), temp_min_coldest_c (missing_no_source), temp_annual_range_c (missing_no_source).
- precip_annual_mm, precip_driest_month_mm: Airless body: no precipitation by definition. Treated as 'drier than any Earth desert', not a measured value.

Balanced scores without famous sites span 1.4 points (92.1 to 93.5).

### balanced preset, without famous sites (top 5)

#### 1. Nearest named place: Achanizo, Arequipa, PE (13 km away)
Lat -15.93, lon -73.97. Score 93.5 (rank 1 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Atacama: 1,012 km, radius 400 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.70 | 0.71 | 98.6 | match |
| ice_proxy | 0.000 fraction | 0.098 fraction | 68.7 | partial |
| precip_annual_mm | 8.6 mm | 0.0 mm | 93.1 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 1,788 m | 1,773 m | 99.8 | match |
| roughness_10km_m | 161 m | 152 m | 98.7 | match |
| roughness_20km_m | 278 m | 359 m | 94.4 | match |
| roughness_5km_m | 93 m | 64 m | 91.0 | match |
| slope_20km_deg | 6.0 degrees | 6.9 degrees | 92.7 | match |

- **Matches:** precip_driest_month_mm (100.0); relief_20km_m (99.8); roughness_10km_m (98.7)
- **Does not match:** no feature below 60; weakest of the features used: ice_proxy Earth 0.000 fraction vs target 0.098 fraction (sub-score 68.7); roughness_5km_m Earth 93 m vs target 64 m (sub-score 91.0); slope_20km_deg Earth 6.0 degrees vs target 6.9 degrees (sub-score 92.7)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_5km_m, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 2. Nearest named place: Nur, Xinjiang Uygur Zizhiqu, CN (53 km away)
Lat 36.52, lon 80.53. Score 93.3 (rank 2 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Sahara (Libya/Egypt): 5,881 km, radius 600 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.71 | 0.71 | 99.4 | match |
| ice_proxy | 0.000 fraction | 0.098 fraction | 68.7 | partial |
| precip_annual_mm | 31.6 mm | 0.0 mm | 80.4 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 1,740 m | 1,773 m | 99.6 | match |
| roughness_10km_m | 205 m | 152 m | 93.4 | match |
| roughness_20km_m | 330 m | 359 m | 98.1 | match |
| roughness_5km_m | 84 m | 64 m | 93.3 | match |
| slope_20km_deg | 6.6 degrees | 6.9 degrees | 97.8 | match |

- **Matches:** precip_driest_month_mm (100.0); relief_20km_m (99.6); hurst_2_32km (99.4)
- **Does not match:** no feature below 60; weakest of the features used: ice_proxy Earth 0.000 fraction vs target 0.098 fraction (sub-score 68.7); precip_annual_mm Earth 31.6 mm vs target 0.0 mm (sub-score 80.4); roughness_5km_m Earth 84 m vs target 64 m (sub-score 93.3)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_5km_m, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 3. Nearest named place: Nuevo Imperial, Lima, PE (16 km away)
Lat -13.03, lon -76.17. Score 93.0 (rank 3 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Atacama: 1,408 km, radius 400 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.70 | 0.71 | 97.6 | match |
| ice_proxy | 0.000 fraction | 0.098 fraction | 68.7 | partial |
| precip_annual_mm | 14.6 mm | 0.0 mm | 89.2 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 1,366 m | 1,773 m | 94.2 | match |
| roughness_10km_m | 197 m | 152 m | 94.3 | match |
| roughness_20km_m | 308 m | 359 m | 96.6 | match |
| roughness_5km_m | 89 m | 64 m | 91.9 | match |
| slope_20km_deg | 6.8 degrees | 6.9 degrees | 98.7 | match |

- **Matches:** precip_driest_month_mm (100.0); slope_20km_deg (98.7); hurst_2_32km (97.6)
- **Does not match:** no feature below 60; weakest of the features used: ice_proxy Earth 0.000 fraction vs target 0.098 fraction (sub-score 68.7); precip_annual_mm Earth 14.6 mm vs target 0.0 mm (sub-score 89.2); roughness_5km_m Earth 89 m vs target 64 m (sub-score 91.9)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_5km_m, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 4. Nearest named place: Putre, Arica y Parinacota, CL (34 km away)
Lat -18.38, lon -69.82. Score 93.0 (rank 4 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Atacama: 626 km, radius 400 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.69 | 0.71 | 97.1 | match |
| ice_proxy | 0.000 fraction | 0.098 fraction | 68.7 | partial |
| precip_annual_mm | 34.8 mm | 0.0 mm | 79.0 | partial |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 1,670 m | 1,773 m | 98.7 | match |
| roughness_10km_m | 176 m | 152 m | 96.6 | match |
| roughness_20km_m | 314 m | 359 m | 97.1 | match |
| roughness_5km_m | 78 m | 64 m | 95.3 | match |
| slope_20km_deg | 7.3 degrees | 6.9 degrees | 97.4 | match |

- **Matches:** precip_driest_month_mm (100.0); relief_20km_m (98.7); slope_20km_deg (97.4)
- **Does not match:** no feature below 60; weakest of the features used: ice_proxy Earth 0.000 fraction vs target 0.098 fraction (sub-score 68.7); precip_annual_mm Earth 34.8 mm vs target 0.0 mm (sub-score 79.0); roughness_5km_m Earth 78 m vs target 64 m (sub-score 95.3)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_5km_m, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 5. Nearest named place: Tieganlike, Heilongjiang Sheng, CN (33 km away)
Lat 38.82, lon 88.47. Score 92.1 (rank 5 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Sahara (Libya/Egypt): 6,552 km, radius 600 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.68 | 0.71 | 94.9 | match |
| ice_proxy | 0.000 fraction | 0.098 fraction | 68.7 | partial |
| precip_annual_mm | 57.0 mm | 0.0 mm | 71.0 | partial |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 2,187 m | 1,773 m | 95.3 | match |
| roughness_10km_m | 160 m | 152 m | 98.9 | match |
| roughness_20km_m | 325 m | 359 m | 97.9 | match |
| roughness_5km_m | 69 m | 64 m | 98.0 | match |
| slope_20km_deg | 7.0 degrees | 6.9 degrees | 99.5 | match |

- **Matches:** precip_driest_month_mm (100.0); slope_20km_deg (99.5); roughness_10km_m (98.9)
- **Does not match:** no feature below 60; weakest of the features used: ice_proxy Earth 0.000 fraction vs target 0.098 fraction (sub-score 68.7); precip_annual_mm Earth 57.0 mm vs target 0.0 mm (sub-score 71.0); hurst_2_32km Earth 0.68 vs target 0.71 (sub-score 94.9)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_5km_m, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

### cold_trap_ice preset, all sites (top 3; flagged if inside a famous exclusion radius)

#### 1. Nearest named place: Clyde River, Nunavut, CA (1,358 km away)
Lat 82.57, lon -76.37. Score 92.8 (rank 1 of 3 in this list). Famous-site check: outside all exclusion radii (nearest Devon Island / Haughton: 840 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| ice_proxy | 0.100 fraction | 0.098 fraction | 99.7 | match |
| precip_annual_mm | 132.2 mm | 0.0 mm | 54.0 | mismatch |
| precip_driest_month_mm | 3.0 mm | 0.0 mm | 79.3 | partial |
| relief_20km_m | 1,652 m | 1,773 m | 98.4 | match |
| slope_20km_deg | 7.1 degrees | 6.9 degrees | 98.4 | match |

- **Matches:** ice_proxy (99.7); relief_20km_m (98.4); slope_20km_deg (98.4)
- **Does not match:** precip_annual_mm Earth 132.2 mm vs target 0.0 mm (sub-score 54.0); precip_driest_month_mm Earth 3.0 mm vs target 0.0 mm (sub-score 79.3); relief_20km_m Earth 1,652 m vs target 1,773 m (sub-score 98.4)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg
- **Use for exploration** (guidance, not a finding): Ice prospecting and cold-trap operations; the Earth frozen-ground fraction stands in for the lunar cold-trap area.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 2. Nearest named place: Upernavik, Qaasuitsup, GL (1,005 km away)
Lat 81.77, lon -51.72. Score 92.2 (rank 2 of 3 in this list). Famous-site check: outside all exclusion radii (nearest Devon Island / Haughton: 1,057 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| ice_proxy | 0.091 fraction | 0.098 fraction | 98.8 | match |
| precip_annual_mm | 104.1 mm | 0.0 mm | 59.2 | mismatch |
| precip_driest_month_mm | 3.1 mm | 0.0 mm | 78.6 | partial |
| relief_20km_m | 1,260 m | 1,773 m | 92.4 | match |
| slope_20km_deg | 6.7 degrees | 6.9 degrees | 98.5 | match |

- **Matches:** ice_proxy (98.8); slope_20km_deg (98.5); relief_20km_m (92.4)
- **Does not match:** precip_annual_mm Earth 104.1 mm vs target 0.0 mm (sub-score 59.2); precip_driest_month_mm Earth 3.1 mm vs target 0.0 mm (sub-score 78.6); relief_20km_m Earth 1,260 m vs target 1,773 m (sub-score 92.4)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg
- **Use for exploration** (guidance, not a finding): Ice prospecting and cold-trap operations; the Earth frozen-ground fraction stands in for the lunar cold-trap area.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

#### 3. Nearest named place: Ushuaia, Tierra del Fuego, AR (1,688 km away)
Lat -69.98, lon -69.27. Score 91.4 (rank 3 of 3 in this list). Famous-site check: outside all exclusion radii (nearest McMurdo Dry Valleys: 3,273 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| ice_proxy | 0.095 fraction | 0.098 fraction | 99.5 | match |
| precip_annual_mm | 291.2 mm | 0.0 mm | 35.4 | mismatch |
| precip_driest_month_mm | 1.3 mm | 0.0 mm | 89.2 | match |
| relief_20km_m | 1,732 m | 1,773 m | 99.5 | match |
| slope_20km_deg | 6.0 degrees | 6.9 degrees | 92.4 | match |

- **Matches:** ice_proxy (99.5); relief_20km_m (99.5); slope_20km_deg (92.4)
- **Does not match:** precip_annual_mm Earth 291.2 mm vs target 0.0 mm (sub-score 35.4); precip_driest_month_mm Earth 1.3 mm vs target 0.0 mm (sub-score 89.2); slope_20km_deg Earth 6.0 degrees vs target 6.9 degrees (sub-score 92.4)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg
- **Use for exploration** (guidance, not a finding): Ice prospecting and cold-trap operations; the Earth frozen-ground fraction stands in for the lunar cold-trap area.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. Permanently shadowed regions (9.8% of the disk, annual maximum below 110 K) have no Earth analogue; the lunar warmest-month maximum median is -42.0 degC, and the coldest Earth warmest-month maximum is -30.0 degC.

## Jezero Crater, Mars

Target: disk of radius 50 km around 18.38N 77.58E. Method: MOLA MEGDR 16 ppd reprojected (bilinear) to a 2 km azimuthal equidistant grid on R=3396.19 km; Earth estimators applied; median and p10-p90 over the disk. Resolution: 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

- Not used (no target value): temp_mean_c (missing_site_specific_literature_value), temp_diurnal_range_c (missing_site_specific_literature_value), temp_max_warmest_c (missing_site_specific_literature_value), temp_min_coldest_c (missing_site_specific_literature_value), temp_annual_range_c (missing_site_specific_literature_value), ice_proxy (not_in_mvp).
- relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m: 3.7 km MOLA pixels bilinearly resampled to 2 km smooth fine-scale terrain, biasing slope and roughness low.
- hurst_2_32km: Lags 2 and 4 km are below MOLA resolution; fitted over 8/16/32 km only, so the exponent is indicative.
- precip_annual_mm, precip_driest_month_mm: Hyper-arid: no liquid precipitation. Treated as a one-sided constraint, not a measured value.

Balanced scores without famous sites span 1.3 points (98.0 to 99.3).

### balanced preset, without famous sites (top 5)

#### 1. Nearest named place: Nazca, Ica, PE (11 km away)
Lat -14.93, lon -74.97. Score 99.3 (rank 1 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Atacama: 1,161 km, radius 400 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.66 | 0.66 | 99.2 | match |
| precip_annual_mm | 2.9 mm | 0.0 mm | 97.4 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 428 m | 427 m | 99.9 | match |
| roughness_10km_m | 34 m | 35 m | 99.2 | match |
| roughness_20km_m | 68 m | 71 m | 99.2 | match |
| slope_20km_deg | 1.6 degrees | 1.5 degrees | 99.3 | match |

- **Matches:** precip_driest_month_mm (100.0); relief_20km_m (99.9); slope_20km_deg (99.3)
- **Does not match:** no feature below 60; weakest of the features used: precip_annual_mm Earth 2.9 mm vs target 0.0 mm (sub-score 97.4); hurst_2_32km Earth 0.66 vs target 0.66 (sub-score 99.2); roughness_10km_m Earth 34 m vs target 35 m (sub-score 99.2)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 2. Nearest named place: Tor, South Sinai, EG (71 km away)
Lat 27.82, lon 33.08. Score 98.6 (rank 2 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Sahara (Libya/Egypt): 1,374 km, radius 600 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.66 | 0.66 | 99.8 | match |
| precip_annual_mm | 6.3 mm | 0.0 mm | 94.8 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 405 m | 427 m | 98.8 | match |
| roughness_10km_m | 36 m | 35 m | 99.7 | match |
| roughness_20km_m | 64 m | 71 m | 97.9 | match |
| slope_20km_deg | 1.6 degrees | 1.5 degrees | 99.3 | match |

- **Matches:** precip_driest_month_mm (100.0); hurst_2_32km (99.8); roughness_10km_m (99.7)
- **Does not match:** no feature below 60; weakest of the features used: precip_annual_mm Earth 6.3 mm vs target 0.0 mm (sub-score 94.8); roughness_20km_m Earth 64 m vs target 71 m (sub-score 97.9); relief_20km_m Earth 405 m vs target 427 m (sub-score 98.8)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 3. Nearest named place: Ushuaia, Tierra del Fuego, AR (3,253 km away)
Lat -83.88, lon -55.47. Score 98.4 (rank 3 of 5 in this list). Famous-site check: outside all exclusion radii (nearest McMurdo Dry Valleys: 1,974 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.74 | 0.66 | 87.4 | match |
| precip_annual_mm | 5.1 mm | 0.0 mm | 95.7 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 418 m | 427 m | 99.6 | match |
| roughness_10km_m | 36 m | 35 m | 99.5 | match |
| roughness_20km_m | 73 m | 71 m | 99.4 | match |
| slope_20km_deg | 1.5 degrees | 1.5 degrees | 100.0 | match |

- **Matches:** precip_driest_month_mm (100.0); slope_20km_deg (100.0); relief_20km_m (99.6)
- **Does not match:** no feature below 60; weakest of the features used: hurst_2_32km Earth 0.74 vs target 0.66 (sub-score 87.4); precip_annual_mm Earth 5.1 mm vs target 0.0 mm (sub-score 95.7); roughness_20km_m Earth 73 m vs target 71 m (sub-score 99.4)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 4. Nearest named place: Arica, Arica y Parinacota, CL (59 km away)
Lat -18.98, lon -70.12. Score 98.0 (rank 4 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Atacama: 562 km, radius 400 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.69 | 0.66 | 96.3 | match |
| precip_annual_mm | 1.5 mm | 0.0 mm | 98.7 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 385 m | 427 m | 97.7 | match |
| roughness_10km_m | 30 m | 35 m | 96.6 | match |
| roughness_20km_m | 89 m | 71 m | 95.0 | match |
| slope_20km_deg | 1.6 degrees | 1.5 degrees | 99.0 | match |

- **Matches:** precip_driest_month_mm (100.0); slope_20km_deg (99.0); precip_annual_mm (98.7)
- **Does not match:** no feature below 60; weakest of the features used: roughness_20km_m Earth 89 m vs target 71 m (sub-score 95.0); hurst_2_32km Earth 0.69 vs target 0.66 (sub-score 96.3); roughness_10km_m Earth 30 m vs target 35 m (sub-score 96.6)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 5. Nearest named place: Marsa Alam, Red Sea, EG (127 km away)
Lat 24.07, lon 35.53. Score 98.0 (rank 5 of 5 in this list). Famous-site check: outside all exclusion radii (nearest Sahara (Libya/Egypt): 1,576 km, radius 600 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.66 | 0.66 | 99.8 | match |
| precip_annual_mm | 13.1 mm | 0.0 mm | 90.1 | match |
| precip_driest_month_mm | 0.0 mm | 0.0 mm | 100.0 | match |
| relief_20km_m | 393 m | 427 m | 98.2 | match |
| roughness_10km_m | 37 m | 35 m | 98.7 | match |
| roughness_20km_m | 74 m | 71 m | 99.1 | match |
| slope_20km_deg | 1.5 degrees | 1.5 degrees | 99.8 | match |

- **Matches:** precip_driest_month_mm (100.0); hurst_2_32km (99.8); slope_20km_deg (99.8)
- **Does not match:** no feature below 60; weakest of the features used: precip_annual_mm Earth 13.1 mm vs target 0.0 mm (sub-score 90.1); relief_20km_m Earth 393 m vs target 427 m (sub-score 98.2); roughness_10km_m Earth 37 m vs target 35 m (sub-score 98.7)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): General terrain and dryness analog for instrument tests and crew training.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

### rover_mobility preset, all sites (top 3; flagged if inside a famous exclusion radius)

#### 1. Nearest named place: McMurdo Station, AQ (515 km away)
Lat -73.43, lon 161.03. Score 99.7 (rank 1 of 3 in this list). Famous-site check: outside all exclusion radii (nearest McMurdo Dry Valleys: 454 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.66 | 0.66 | 99.0 | match |
| relief_20km_m | 425 m | 427 m | 99.9 | match |
| roughness_10km_m | 36 m | 35 m | 99.7 | match |
| roughness_20km_m | 73 m | 71 m | 99.3 | match |
| slope_20km_deg | 1.5 degrees | 1.5 degrees | 99.8 | match |

- **Matches:** relief_20km_m (99.9); slope_20km_deg (99.8); roughness_10km_m (99.7)
- **Does not match:** no feature below 60; weakest of the features used: hurst_2_32km Earth 0.66 vs target 0.66 (sub-score 99.0); roughness_20km_m Earth 73 m vs target 71 m (sub-score 99.3); roughness_10km_m Earth 36 m vs target 35 m (sub-score 99.7)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): Rover traverse and driving tests on this slope, relief and roughness profile.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 2. Nearest named place: Port-aux-Francais, Kerguelen, TF (2,376 km away)
Lat -68.13, lon 49.63. Score 99.7 (rank 2 of 3 in this list). Famous-site check: outside all exclusion radii (nearest McMurdo Dry Valleys: 3,216 km, radius 300 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.67 | 0.66 | 99.0 | match |
| relief_20km_m | 427 m | 427 m | 100.0 | match |
| roughness_10km_m | 35 m | 35 m | 99.9 | match |
| roughness_20km_m | 66 m | 71 m | 98.4 | match |
| slope_20km_deg | 1.5 degrees | 1.5 degrees | 99.9 | match |

- **Matches:** relief_20km_m (100.0); roughness_10km_m (99.9); slope_20km_deg (99.9)
- **Does not match:** no feature below 60; weakest of the features used: roughness_20km_m Earth 66 m vs target 71 m (sub-score 98.4); hurst_2_32km Earth 0.67 vs target 0.66 (sub-score 99.0); roughness_10km_m Earth 35 m vs target 35 m (sub-score 99.9)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): Rover traverse and driving tests on this slope, relief and roughness profile.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

#### 3. Nearest named place: Otjimbingwe, Erongo, NA (33 km away)
Lat -22.63, lon 16.03. Score 99.7 (rank 3 of 3 in this list). Famous-site check: outside all exclusion radii (nearest Sahara (Libya/Egypt): 5,202 km, radius 600 km).

| Feature | Earth | Target | Sub-score | Verdict |
|---|---|---|---|---|
| hurst_2_32km | 0.67 | 0.66 | 99.2 | match |
| relief_20km_m | 426 m | 427 m | 100.0 | match |
| roughness_10km_m | 35 m | 35 m | 99.9 | match |
| roughness_20km_m | 68 m | 71 m | 99.1 | match |
| slope_20km_deg | 1.5 degrees | 1.5 degrees | 99.7 | match |

- **Matches:** relief_20km_m (100.0); roughness_10km_m (99.9); slope_20km_deg (99.7)
- **Does not match:** no feature below 60; weakest of the features used: roughness_20km_m Earth 68 m vs target 71 m (sub-score 99.1); hurst_2_32km Earth 0.67 vs target 0.66 (sub-score 99.2); slope_20km_deg Earth 1.5 degrees vs target 1.5 degrees (sub-score 99.7)
- **Within the target's own spread:** relief_20km_m, slope_20km_deg, roughness_10km_m, roughness_20km_m, hurst_2_32km
- **Use for exploration** (guidance, not a finding): Rover traverse and driving tests on this slope, relief and roughness profile.
- **Earth cannot replicate:** Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment. No Mars temperature, mineral or dust data in this ranking; 3.7 km source, 2 km working grid: sub-pixel detail is not resolved.

## What this ranking cannot tell you yet

- Mars: no site-specific temperature values and no cold-trap product, so the thermal and ice checks cannot be scored.
- Moon: Diviner PRP gives only annual mean and max temperature. The minimum and diurnal temperatures are therefore not checked.
- Each target is one median over a disk (Moon: disk of radius 151.7 km around the pole in the Moon 2015 polar stereographic grid; Mars: disk of radius 50 km around 18.38N 77.58E). The p10-p90 spread is used only for the within-spread check.
- An Earth cell is about 5.6 km. A single crater, valley or lava tube is smaller than one cell, so the ranking describes terrain statistics, not a feature.
- Known analogs that fail the rank percentile >= 75 check in `docs/validation.md`: Lunar south pole: Devon Island / Haughton (rank percentile 69.8); Jezero Crater (Mars): Dry Valleys (rank percentile 46.6); Jezero Crater (Mars): Iceland (rank percentile 68.5). The ranking does not reproduce these analogs, and the failures are kept here.

