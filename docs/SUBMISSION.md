# Submission pack

## One-line pitch

We rank every place on Earth by how closely its measured terrain and dryness match a lunar south-pole or Jezero target, show the feature-by-feature match, and state plainly what Earth can never replicate.

## Demo video storyboard (about 1:45)

| Time | Shot | Voice-over |
|---|---|---|
| 0:00-0:10 | Slow Moon/Mars images, then title card | "Space agencies test rovers and crews at a handful of Earth analog sites chosen by expert intuition. Did we miss better ones?" |
| 0:10-0:25 | Architecture figure (`docs/figures/architecture.png`) | "We measure the same terrain features on Earth, the lunar south pole and Jezero, then place every target on Earth's own percentile scale." |
| 0:25-0:45 | Map app, Moon target, balanced preset; heat layer appears | "Brighter means more similar. Each Earth cell is scored on relief, slope, roughness at three scales, scale-robust roughness and dryness." |
| 0:45-1:05 | Click top Moon site; radar chart and table | "Click anywhere for a breakdown: what matches, how closely, and what does not." |
| 1:05-1:20 | Switch to cold-trap preset; Antarctica lights up; toggle "hide famous sites" | "With the cold-trap priority, Antarctica leads. Hide the famous analog regions and the list changes." |
| 1:20-1:35 | Switch to Jezero; click Nazca, then Lop Nur | "Peru's Nazca desert matches Jezero's relief to within a metre (428 vs 427), and a cold-winter basin in China matches its roughness." |
| 1:35-1:45 | Pan to "Where the analogy breaks down" and "Earth cannot replicate" panels | "We say what Earth cannot reproduce: gravity, vacuum, thin atmosphere and radiation. Temperatures are not scored yet, and we flag that." |

Recording tips: browser at 1600x900 (matches `docs/figures/frontend_*.png`), run `make serve` first, allow ~10 s for the basemap to load, zoom to a site before clicking so markers are visible.

## Slide outline (8 slides)

1. **Title and one-line pitch.**
2. **Problem:** analog sites are chosen by intuition; no site matches everything; judges reward data-backed, overlooked, honest answers.
3. **Approach:** feature vector per cell; same estimators on Earth, Moon and Mars; Earth-percentile normalization (why: within-body percentiles would force a median lunar value to match a median Earth value). Architecture figure.
4. **Data:** LOLA, MOLA, ETOPO 2022, WorldClim 2.1, PSR table, with citations (README credits table).
5. **Validation:** Atacama, Dry Valleys, Devon Island, Death Valley, Iceland pass 9 of 9 expected-feature checks; Devon Island ranks only 72nd percentile for the Moon, reported rather than hidden.
6. **Results:** top sites table ([SITE_ANALYSIS](SITE_ANALYSIS.md)); map screenshots `docs/figures/frontend_moon.png`, `frontend_mars.png`.
7. **Where it breaks down:** temperatures unscored; air vs surface temperature; percentile compression; gravity, vacuum, atmosphere, radiation.
8. **Impact and next steps:** instrument tests, crew training, prospecting rehearsal; add site-specific temperatures, mineral maps (EMIT/ASTER), field verification.

## Judging checklist

| Judge criterion | Where we address it |
|---|---|
| Data-backed similarity, not "looks like" | per-feature values, percentiles and sub-scores in the site panel and `docs/target_profiles.json` |
| Whole-planet systematic search | 0.05° global grid, 8.7 M land cells |
| Not just famous sites | "hide famous sites" toggle and `top_without_famous_sites` lists |
| Scale | features measured in 5-32 km windows; targets 50-300 km regions |
| Honesty about Earth's limits | panels in the app, `earth_cannot_replicate` in every API response, README limits |
| Processes, not just places | Lop Nur wind-erosion story (background knowledge, flagged as such) |
| Visual quality | map app screenshots in `docs/figures/` |

## Before submitting (checklist)

- [ ] Add site-specific temperature values (lunar south pole, Jezero) or keep the "not scored" statements in the video and slides.
- [ ] Verify the place names of the six candidates on a map and in Worldview.
- [ ] Record the video from `make serve`; check it runs from a fresh clone (README steps).
- [ ] Confirm team names and credits.
