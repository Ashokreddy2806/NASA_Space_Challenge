# Top-site analysis

Six Earth candidates from the current rankings (`data/processed/top_sites.json`, also served by `GET /targets/{target}/top-sites`), plus two results we show as warnings. Full tables for every preset are in [phase3_report.md](phase3_report.md).

> **Read this first.**
> 1. Place names are our reading of the coordinates, not a gazetteer lookup. Check them on a map before quoting them.
> 2. Scores are 0 to 1 and Earth-relative. Moon and Mars scores are not comparable.
> 3. "Site score" is the average over a 25 km radius, so it is lower than the best single cell.
> 4. None of these sites is on our famous-analog list. That does not mean nobody has studied them.
> 5. No site matches everything. Each entry says what it is good for and what it is not.

## Summary

| # | Site (approx.) | Target | Lat, Lon | Preset | Site score | In one line |
|---|---|---|---|---|---|---|
| 1 | Peruvian Andes, western slope | Moon | -10.28, -77.58 | balanced | 0.80 | Lunar-like relief and multi-scale roughness with a nearly dry driest month |
| 2 | New Guinea highlands | Moon | -5.93, 146.53 | rover mobility | 0.86 | Best terrain match on Earth, in a rainforest: terrain only |
| 3 | Hindu Kush, Afghanistan | Moon | 35.13, 68.88 | balanced | 0.77 | Rugged, seasonally dry mountain terrain |
| 4 | Transantarctic region, Antarctica | Moon | -84.33, 175.53 | cold-trap / ice | 0.78 | The only candidate that is also cold and dry; on an ice sheet |
| 5 | Eastern Desert, Egypt | Mars | 25.68, 34.58 | balanced | 0.92 | Jezero-like slope and roughness at 6 mm of rain a year |
| 6 | Southern Libya | Mars | 22.53, 19.03 | balanced | 0.90 | Same family as 5, deeper in the Sahara |

## Moon: south polar cap (poleward of 85°S)

Target medians: relief 1789 m, slope 9.3°, roughness 77 / 170 / 374 m at 5 / 10 / 20 km, Hurst exponent 0.68. Permanently shadowed regions cover 9.8% of the cap (7,107 of 72,308 km²); that figure is context, not a scored feature, because Earth has no equivalent map. Temperature enters only as two qualitative bands at low weight.

### 1. Peruvian Andes, western slope (-10.28, -77.58), balanced 0.80

- **Matches:** relief 1749 m vs 1789 m; Hurst 0.68 vs 0.68; roughness at 10 km 191 m vs 170 m and at 20 km 340 m vs 374 m; driest month 0.2 mm.
- **Does not match:** slope 7.2° vs 9.3°; roughness at 5 km 107 m vs 77 m (rougher at fine scale); 279 mm of rain a year against a target of zero; warm, so the temperature group scores only 0.26.
- **Stability:** stays in the top list in 7 of 9 thermal sensitivity runs.
- **Exploration use:** rover mobility and traverse planning on steep, lunar-scale relief; instrument field tests during the dry season.

### 2. New Guinea highlands (-5.93, 146.53), rover mobility 0.86

- **Matches:** relief 1831 m vs 1789 m; roughness at 20 km 348 m vs 374 m; slope 7.8° vs 9.3°. It tops the terrain-only preset and stays in the balanced top list in all 9 sensitivity runs.
- **Does not match:** 2,405 mm of rain a year and 82 mm in the driest month: the dryness group scores 0. It is warm and wet enough to be forested (background knowledge; vegetation is not in our data). Roughness at 5 km is 127 m vs 77 m.
- **What this shows:** terrain geometry alone finds this site; nothing else about it resembles the Moon. It is the clearest case for reading the per-group bars and not just the headline score.
- **Exploration use:** limited to terrain-shape studies (slope and roughness statistics for mobility models). Not a field analog.

### 3. Hindu Kush, Afghanistan (35.13, 68.88), balanced 0.77

- **Matches:** roughness at 10 km 191 m vs 170 m; relief 1443 m vs 1789 m; Hurst 0.64 vs 0.68; driest month 2.4 mm.
- **Does not match:** slope 6.7° vs 9.3°; 773 mm of precipitation a year; roughness at 5 km 117 m vs 77 m.
- **Stability:** 7 of 9 sensitivity runs.
- **Exploration use:** rugged-terrain mobility analog with cold winters. Access is a practical obstacle.

### 4. Transantarctic region, Antarctica (-84.33, 175.53), cold-trap / ice 0.78

- **Matches:** roughness at 20 km 373 m vs 374 m; relief 1568 m vs 1789 m; coldest temperature band (temperature group 1.0); 24 mm of precipitation a year and none in the driest month.
- **Does not match:** Hurst 0.57 vs 0.68 (smoother across scales); slope 7.1° vs 9.3°. Even here, air temperature is far above a lunar cold trap.
- **Flag:** inside the Antarctic ice-sheet region. Our data cannot tell ice cover from bare ground, so the terrain match may be an ice surface, not rock.
- **Exploration use:** crew operations and drilling in sustained cold and low sun angles; logistics rehearsal for a remote polar base.

## Mars: Jezero crater (18.36°N, 77.59°E, 150 km disc)

Target medians: relief 472 m, slope 1.47°, roughness 40 m at 10 km and 85 m at 20 km. Roughness at 5 km and the Hurst exponent are not scored because MOLA (about 3.7 km per pixel) cannot resolve them. **No temperature is scored for Mars.** The ranking is terrain plus dryness.

### 5. Eastern Desert, Egypt (25.68, 34.58), balanced 0.92

- **Matches:** slope 1.44° vs 1.47°; roughness at 10 km 35 m vs 40 m; relief 393 m vs 472 m; 6 mm of rain a year and none in the driest month.
- **Does not match:** roughness at 20 km 61 m vs 85 m (smoother at long scale); hot, which the score does not see.
- **Exploration use:** rover drive and autonomous-navigation tests on low-relief, hyper-arid ground; dry channel (wadi) systems as a comparison for Jezero's inlet valley. The wadi comparison is background knowledge, not something our data verifies.

### 6. Southern Libya (22.53, 19.03), balanced 0.90

- **Matches:** roughness at 10 km 38 m vs 40 m; slope 1.34° vs 1.47°; 13 mm of rain a year.
- **Does not match:** relief 322 m vs 472 m; roughness at 20 km 62 m vs 85 m.
- **Exploration use:** as for site 5. It is an independent second location of the same terrain type, useful as a control.

## Two results to read as warnings

- **Solomon Islands region (-6.73, 156.43), Mars rover mobility 0.95.** Slope 1.44° vs 1.47° and roughness at 20 km 85.0 m vs 85.2 m, with 3,441 mm of rain a year. The terrain-only preset ignores climate by definition, so a rainforest island can lead it.
- **West Antarctica (-71.73, -72.83), Mars rover mobility 0.95.** The top terrain-only Mars cell lies in the ice-sheet region and carries the ice flag. A smooth ice surface is not a Jezero analog.

## How the known analogs score

They were scored as found and never tuned for.

| Target | Higher | Lower |
|---|---|---|
| Moon (balanced) | Mauna Kea summit 0.81, Licancabur 0.79, Dry Valleys 0.61 (98th percentile of land), Death Valley 0.49, Iceland 0.48, Atacama 0.44 | Sahara 0.22, Devon Island 0.22, Mistastin Lake 0.20, Amazon 0.14 |
| Mars (balanced) | Atacama 0.85 (93rd percentile), Rio Tinto 0.82, Devon Island 0.77, Iceland 0.73 | Sahara 0.61, Death Valley 0.58, Amazon 0.44, Dry Valleys 0.08, Licancabur 0.04, Mauna Kea 0.00 |

The Amazon is a deliberate negative control and scores low for both. Devon Island scoring low for the Moon, and the volcanic summits scoring near zero for Jezero, follow from terrain: these features measure shape and dryness, not geology or process.

## What Earth cannot replicate

- Reduced gravity: about 1/6 g on the Moon, 0.38 g on Mars.
- Vacuum on the Moon; a thin carbon dioxide atmosphere on Mars.
- The radiation environment.
- Lunar regolith and permanently shadowed cold traps; Martian soil chemistry and global dust storms.

## Limits of this analysis

- The features describe terrain shape and dryness. There is no mineralogy, substrate or ice layer.
- Earth temperature is air temperature (WorldClim), compared with lunar surface values only as coarse bands.
- Earth cells are about 5 km; the lunar cap is about 300 km across and the Jezero disc 150 km. A match is a regional statistical resemblance, not a one-to-one landform.
- Many cells score within a few hundredths of each other, so the order among the top sites is weak evidence. The stability values show this.

## Next steps

1. Check each site in satellite imagery (NASA Worldview) and confirm the place names.
2. Replace WorldClim with NASA surface-temperature and precipitation products (see the decisions log in [PLAN.md](../PLAN.md)).
3. Add a composition layer (EMIT or ASTER minerals) for Jezero-style clay and carbonate analogs.
4. Add a land-cover or ice mask so ice sheets and vegetation are separated in the data, not only flagged.
