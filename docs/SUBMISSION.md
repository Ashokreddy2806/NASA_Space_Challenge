# Submission pack

## One-line pitch

We score every land cell on Earth for how closely its measured terrain and dryness match the lunar south pole or Jezero crater, show the match feature by feature, and state plainly what Earth can never replicate.

## Demo video storyboard (about 1:45)

| Time | Shot | Voice-over |
|---|---|---|
| 0:00-0:10 | Globe rotating slowly, title on screen | "Space agencies test rovers and crews at a handful of Earth analog sites chosen by expert judgement. Did we miss better ones?" |
| 0:10-0:25 | Pipeline diagram from the README | "We measure the same terrain features on Earth, the lunar south pole and Jezero, over the same window sizes, and score all 8.7 million land cells." |
| 0:25-0:45 | Moon target, balanced preset; amber glow and pins | "The glow marks the land most like the lunar south pole. The pins are the top sites, at least 50 km apart." |
| 0:45-1:05 | Select the Peruvian Andes site; panel bars, then Compare | "Each site shows its match by group. Here relief and roughness match the Moon; dryness and temperature do not, and the panel says so." |
| 1:05-1:20 | Switch to cold-trap / ice; Antarctica; toggle "Hide famous" | "Prioritise cold and Antarctica leads. Hide the famous analogs and the list changes." |
| 1:20-1:35 | Switch to Mars; select the Eastern Desert site | "For Jezero, Egypt's Eastern Desert matches slope and roughness at six millimetres of rain a year. Atacama, a known Mars analog, scores in the top 7% without being tuned for." |
| 1:35-1:45 | Panel line "Not replicable on Earth" | "No site matches everything. Gravity, vacuum, thin atmosphere and radiation cannot be reproduced on Earth, and Mars temperature is not scored at all." |

Recording tips: browser at 1600 × 900, run `make serve` first, wait about 10 seconds for imagery to load, and interact with the globe once to stop the idle rotation before selecting a site.

## Slide outline (8 slides)

1. **Title and one-line pitch.**
2. **Problem.** Analog sites are chosen by judgement; no single site matches everything; the challenge rewards data-backed, overlooked and honest answers.
3. **Approach.** One feature registry for three bodies; kilometre-sized windows so different data resolutions stay comparable; per-feature evidence in real units and by rank; preset weights. Pipeline diagram.
4. **Data.** LOLA, MOLA, ETOPO 2022, WorldClim 2.1, the lunar PSR table, with citations (README credits table).
5. **Validation.** Known analogs scored as found: Atacama 0.85 and Rio Tinto 0.82 for Jezero; Licancabur 0.79 and Dry Valleys 0.61 for the Moon; the Amazon negative control scores low for both. Devon Island scores only 0.22 for the Moon, reported and explained.
6. **Results.** Site table from [SITE_ANALYSIS.md](SITE_ANALYSIS.md); app screenshot `figures/app_globe.png`.
7. **Where it breaks down.** Air versus surface temperature; no Mars temperature; no composition or ice layer; terrain-only presets can pick rainforest; gravity, vacuum, atmosphere, radiation.
8. **Impact and next steps.** Instrument tests, crew training, prospecting rehearsal; NASA surface temperature and precipitation, mineral maps (EMIT, ASTER), field verification.

## Judging checklist

| Judge criterion | Where we address it |
|---|---|
| Data-backed similarity, not "looks like" | Per-feature Earth and target values, real-unit gaps and rank similarity in the API and reports |
| Whole-planet systematic search | 0.05° global grid, 8.7 million land cells |
| Not just famous sites | "Hide famous" toggle; `sites_excluding_famous` in every ranking |
| Scale | Features measured in 5 to 32 km windows; targets are a 300 km polar cap and a 150 km disc |
| Honesty about Earth's limits | Panel line in the app, `earth_cannot_replicate` and `not_scored` in API responses, README limits, warnings in the site analysis |
| Visual quality | Full-screen globe with satellite imagery, 3D terrain and a comparison chart |

## Before submitting

- [ ] Verify the place names of the candidate sites on a map and in NASA Worldview.
- [ ] Record the video from `make serve`.
- [ ] Check the project runs from a fresh clone using the README steps.
- [ ] Confirm team names and credits.
- [ ] Decide whether the WorldClim replacement lands before submission; if not, keep the temperature limits in the video and slides.
