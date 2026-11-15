# Top-site analysis (Phase 6)

Six Earth candidates chosen from the Phase 3 rankings (`docs/top_sites.json`), covering both targets and mixing well-known regions with ones outside our "famous analogs" list. Numbers come from `GET /targets/{t}/site` (0.05° cells, about 5 km); Earth values are the cell's, target values are the Phase 2 medians.

> **Read this first.** (1) Place names are *my identification from coordinates*, not looked up in a gazetteer; check them on a map. (2) "Not in our famous list" means not in the nine regions we excluded, **not** that nobody has studied the place. (3) A score of 98 means the *terrain and dryness percentiles* line up. Temperatures are **not** scored (no site-specific lunar/Martian values yet), so a site can score 98 and be 19 °C warmer than any lunar cold trap. (4) Dryness sub-scores are percentile ranks: a cell with 27 mm/yr of rain scores 95 against a zero-rain target; it is dry for Earth, not rainless.

## Summary

| # | Site (approx.) | Target | Lat, Lon | Score | Story in one line |
|---|---|---|---|---|---|
| 1 | Nazca / Ica desert, Peru | Jezero | -14.93, -74.97 | 98 | Terrain almost identical to Jezero (relief 428 vs 427 m, slope 1.55° vs 1.52°) in a ~3 mm/yr desert |
| 2 | Eastern Desert / Red Sea Hills, Egypt | Jezero | 27.82, 33.08 | 98 | Hyper-arid wadi terrain with matching relief, slope and Hurst exponent |
| 3 | Lop Nur region, NW China | Jezero | 40.47, 91.72 | 97 | Best roughness match (5 km: 15.7 vs 15.7 m); cold-winter desert, known for wind-carved yardangs |
| 4 | Transantarctic region, Antarctica | Lunar pole | -84.68, 171.98 | 98 (cold-trap preset) | The only lunar candidate that is also cold: coldest-month air minimum -63 °C |
| 5 | Western Kunlun / Aksai Chin, Tibetan Plateau | Lunar pole | 36.47, 80.53 | 98 | Near-perfect terrain match (relief 1739 vs 1773 m), but not cold enough |
| 6 | Southern Peruvian Andes (Arequipa area) | Lunar pole | -16.03, -72.57 | 98 | Terrain match next to Atacama, on the less-visited side; warm |

## Moon: lunar south pole (poleward of 85°S)

Target: relief 1773 m, slope 6.9°, roughness 64/152/359 m at 5/10/20 km, Hurst 0.71; permanently shadowed regions cover 9.8% of the disk.

### 4. Transantarctic region, Antarctica (-84.68, 171.98), cold-trap preset 98

- **Matches:** relief 2188 vs 1773 m (100), slope 10.3° vs 6.9° (99), roughness 51/135/536 vs 64/152/359 m (97-99), annual precipitation 22 mm (96), coldest-month minimum -63 °C (the closest Earth gets to a cold-trap story).
- **Does not match:** Hurst 0.60 vs 0.71 (83: smoother at large scale); relief and slope run higher; air temperature is still ~100 K warmer than a permanently shadowed crater (below 110 K annual maximum, Sefton-Nash et al. 2019). Ice here is a glacier, not buried regolith ice.
- **Exploration use:** crew training and traverse planning in polar darkness and cold; testing drills and sample handling at -40 to -60 °C; practising navigation on steep, low-sun terrain; resource-prospecting rehearsal (ground-penetrating radar on ice-rich ground).
- **Earth cannot replicate:** vacuum, 1/6 g, radiation, regolith (this is rock and ice sheet), true 110 K cold traps, and months of near-horizontal sunlight at a fixed spot.

### 5. Western Kunlun / Aksai Chin (36.47, 80.53), balanced 98

- **Matches:** relief 1739 vs 1773 m (100), slope 6.1° vs 6.9° (99), roughness 73/159/364 vs 64/152/359 m (98-100), Hurst 0.70 vs 0.71 (99), annual precipitation 31 mm (95).
- **Does not match:** ice/cold proxy 65: coldest-month minimum is only -14 °C; mean air temperature +7 °C; no mapped permanent shadow. Hurst and terrain match is the whole case.
- **Exploration use:** rover mobility and instrument testing on lunar-like crater-free rugged terrain at high altitude (thin air is a weak, partial atmosphere analog); logistics practice for a remote, hard-to-reach site.
- **Earth cannot replicate:** vacuum, reduced gravity, radiation, regolith dust behaviour, extreme thermal swing (air diurnal range here is 15 K versus roughly 300 K on the lunar equator).

### 6. Southern Peruvian Andes (-16.03, -72.57), balanced 98

- **Matches:** relief 1926 vs 1773 m (100), slope 6.3° vs 6.9° (99), roughness 67/170/387 m (99-100), Hurst 0.72 vs 0.71 (99), annual precipitation 27 mm (95).
- **Does not match:** ice/cold proxy 28 (coldest-month minimum +10 °C, mean 19 °C). It is a terrain and dryness analog only.
- **Exploration use:** same family as Atacama (which it neighbours) for rover and instrument field tests, with a second, less congested site; useful as a control when separating "terrain effect" from "site fame".
- **Earth cannot replicate:** as above. Also note it sits close to Atacama, so it adds little independent information about the lunar pole.

## Mars: Jezero Crater (18.38°N, 77.58°E, 50 km disk)

Target: relief 427 m, slope 1.52°, roughness 16/35/71 m, Hurst 0.66 (reduced lags, indicative). Mars 5 km roughness is resolution-limited and given weight 0; Mars temperatures are not scored.

### 1. Nazca / Ica desert, Peru (-14.93, -74.97), score 98 (highest-ranked Mars cell)

- **Matches:** relief 428 vs 427 m (100), slope 1.55° vs 1.52° (100), roughness 10/20 km 34/68 vs 35/71 m (99), Hurst 0.66 vs 0.66 (99), annual precipitation 2.9 mm (99).
- **Does not match:** 5 km roughness 11 vs 16 m (94; Mars value is a biased-low, resolution-limited estimate); air temperature mean 20 °C and diurnal range 11 K, nowhere near Mars's (Viking 1 diurnal range 58 K, global mean 214 K); no clay-bearing delta deposits are mapped here.
- **Exploration use:** rover drive tests and autonomous navigation on low-relief desert terrain; instrument calibration under hyper-arid conditions; low-cost, accessible field campaign site.
- **Earth cannot replicate:** 0.38 g, a 6 mbar CO2 atmosphere, radiation, perchlorate soils, and Jezero's specific fluvial-lacustrine geology.

### 2. Eastern Desert / Red Sea Hills, Egypt (27.82, 33.08), score 98

- **Matches:** relief 405 vs 427 m (99), slope 1.55° vs 1.52° (100), roughness 22/36/64 vs 16/35/71 m (95-100), Hurst 0.66 (100), annual precipitation 6.3 mm (99).
- **Does not match:** warm (mean 22 °C, warmest month 36 °C); 5 km roughness a little high; weights are terrain and dryness only.
- **Exploration use:** dry wadi and basement-rock traverses for rover navigation; sample-selection training; a natural comparison for ancient channel systems (Jezero's inlet valley is a dry river system).
- **Earth cannot replicate:** gravity, atmosphere, radiation, global dust storms.

### 3. Lop Nur region, NW China (40.47, 91.72), score 97

- **Matches:** relief 394 vs 427 m (98), slope 1.52° vs 1.52° (100), roughness 15.7/35.5/75 vs 15.7/35/71 m (99-100), Hurst 0.69 vs 0.66 (96), annual precipitation 20 mm (97).
- **Does not match:** relief about 8% low; much colder winters than Nazca (coldest-month minimum -15 °C, a little closer to Mars) but its mean air temperature (+9.5 °C) is still about 70 K above Mars's global mean (214 K).
- **Exploration use:** aeolian-process study: this basin is widely described as having wind-carved yardangs, which is the process-not-place angle the challenge rewards for Mars dust and wind erosion; also dry-lake-bed (playa) deposit sampling. The yardang claim is background knowledge, not something our data verifies.
- **Earth cannot replicate:** gravity and atmosphere set Mars's wind and sediment transport; dust-storm dynamics differ.

## What to do next

1. **Add temperatures.** The one decisive gap: site-specific literature values for the lunar south pole (Diviner / Williams et al. 2019) and Jezero (MEDA) would let us score thermal analogs and demote sites such as #5 and #6.
2. **Verify each cell** in Worldview/Earthdata before claiming it in the pitch (place name, imagery, access).
3. **Look for minerals.** Our features are geometry and dryness only; EMIT or ASTER mineral maps are the natural next layer for Jezero-style clay/carbonate analogs.
4. **Sensitivity check.** Rerun with Phase 3 weights changed to confirm these sites stay on top.

## Honest limits of this write-up

- Percentile distance compresses real differences near the extremes; many cells score 97-98, so rank order among them is weak evidence.
- Earth cells are about 5 km; the Moon region is 300 km across and Jezero 50 km, so a "match" is a regional statistical resemblance, not a one-to-one landform.
- Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment.
