# Progress Log

Who did what, and when. Each team member has **their own section**. Only write in your own section.

## How to add an entry

1. Go to **your** section below.
2. Update the **Now working on** line.
3. Add a new entry **at the top** of your entries (newest first), directly under the `<!-- entries -->

#### 2026-11-15 16:01 — Deployed to Vercel with Blob storage
- **Did:** Live at https://analog-earth.vercel.app. Exported every endpoint the globe app calls (26 files, 5.2 MB) to static files, uploaded to a public Vercel Blob store (`analog-earth-data`), and deployed `frontend/` as a static site. Frontend reads Blob when `window.STATIC_DATA_BASE` is set, live FastAPI otherwise.
- **Files:** `backend/api/export_static.py`, `deploy/deploy.sh`, `deploy/README.md`, `frontend/js/config.js`, `frontend/js/globe.js`
- **Next:** none required; rerun `deploy/deploy.sh` after any score rebuild.
- **Blockers:** none
` marker.
4. Use this format:

```markdown
#### YYYY-MM-DD HH:MM — short title
- **Did:** what changed / what was made (1–3 bullets, concrete)
- **Files:** paths touched (e.g. `backend/engine/score.py`)
- **Next:** what comes next
- **Blockers:** anything blocking you or needing a teammate (or "none")
```

Keep entries short. Big decisions also go in the **Decisions log** in [PLAN.md](PLAN.md); workstream status goes in the **Workstreams** table there.

---

## rahul

**Now working on:** Horizon frontend polish (caveat chip, mobile); plan to replace WorldClim with NASA Earthdata products (MODIS LST, GPM IMERG, MODIS land cover); awaiting go-ahead and an Earthdata login

<!-- entries -->

#### 2026-11-15 15:28 — 7-slide submission deck
- **Did:** Built a 7-slide web deck (dark Horizon look, written to be read without a speaker): title, problem, approach, data + pipeline, results (Peruvian Andes 0.80, Eastern Desert Egypt 0.92, known-analog sanity check), app screenshots, limits + next steps. Numbers taken from `README.md` and `docs/SITE_ANALYSIS.md`. Images: `docs/figures/app_globe.png` and two stills from the demo video. Team line: Rahul · Ashok · Mrinalini · Chandu.
- **Files:** deck is hosted, not in the repo: https://claude.ai/artifact/613FGs2KeJvuTSQJBeYUYN (private until shared from its Share menu; exports to .pptx / PDF)
- **Next:** team review of wording; share the link or export a PDF for the submission page; the Compare-chart still shows a faint "Loading chart" label, re-capture if it bothers anyone.
- **Blockers:** none

#### 2026-11-15 15:19 — 30-second demo video
- **Did:** Recorded a 30 s, 1920x1080, 30 fps demo of the live app (headless Chrome screencast, scripted take: intro title, Moon top site in the Peruvian Andes 80%, Compare radar, switch to Mars, Egypt Eastern Desert 92%, end card). Captions are overlaid by the script; the app code is unchanged. Audio is a synthesized ambient pad (ffmpeg), no licensed music.
- **Update 15:27:** re-recorded with Chandu added to the end-card credits (Rahul · Ashok · Mrinalini · Chandu).
- **Update 15:52:** voice-over version redone with the open-source Kokoro TTS model (voice `af_heart`, run locally, more natural than macOS `say`), script rewritten phrase by phrase with deliberate pauses at a relaxed 0.94-0.98x pace, timed to the cuts, ambient bed ducked under the voice: `docs/video/analog_earth_30s_voiceover.mp4`.
- **Files:** `docs/video/analog_earth_30s.mp4` (21 MB, not committed), `docs/video/capture.js`
- **Next:** team review of caption wording; re-record after the frontend polish lands (`node capture.js <framesDir>` with the server on :8000, needs `playwright-core`).
- **Blockers:** none

#### 2026-11-15 15:16 — Documentation and repository cleanup
- **Did:** Rewrote `README.md` (pitch, results, pipeline diagram, macOS/Linux/Windows quick start, credits, limits); new `docs/README.md` index; rewrote `docs/API.md`, `frontend/README.md`, `docs/SITE_ANALYSIS.md` and `docs/SUBMISSION.md` against the current engine outputs (0-1 scores, `moon`/`mars` targets, Horizon frontend). Untracked 35 files: 28 `docs/figures/proof_*.png` and the two `docs/proof_*_report.md` (regenerable, now git-ignored), stale `docs/make_architecture.py` + `architecture.png`, old-UI screenshots `frontend_{moon,mars}.png`, empty `notebooks/`. Tracked files 29 MB -> 14 MB. New screenshot `docs/figures/app_globe.png`. Moved two log entries that had landed inside the "How to add an entry" instructions into this section. Fixed `tests/test_phase4.py::test_frontend_served` for the Horizon frontend (122 tests pass).
- **Files:** `README.md`, `.gitignore`, `docs/{README,API,SITE_ANALYSIS,SUBMISSION}.md`, `frontend/README.md`, `tests/test_phase4.py`, `PLAN.md`, `PROGRESS_LOG.md`
- **Next:** team review, then commit; decide on a LICENSE; commit the two thermal literature CSVs or document where to get them.
- **Blockers:** proof outputs and `hardcode_audit.md` are Ashok's, removal of the proof outputs needs his OK before commit.

#### 2026-11-15 15:10 — Horizon frontend (globe, elevation, detail panel)
- **Did:** Picked the "Horizon" design (3 options mocked in a design canvas). Rebuilt `frontend/` as a full-bleed MapLibre 5.6 globe: Esri imagery + AWS Terrarium hillshade/3D terrain, soft amber similarity glow, pins with pulsing ring and match-% pill, Moon/Mars toggle, preset dropdown, "Hide famous" toggle, detail panel (group bars, elevation + relief, one-line "not replicable on Earth", Plotly Compare modal). Minimal text. Checked in browser pane against the live API, no console errors.
- **Files:** `frontend/index.html`, `frontend/style.css`, `frontend/panel.css`, `frontend/js/globe.js`, `frontend/js/panel.js`; `frontend/app.js` deleted (staged, not committed)
- **Next:** restore ice/substrate caveat chip in the panel; fix `/presets` listing `thermal_cycling` as available while `/top-sites` returns 422; add place names; test mobile (<900px) and pin click on globe; cross-check Antarctic elevation (-52 m).
- **Blockers:** none (globe needs internet for imagery/DEM tiles)

#### 2026-11-15 14:26 — main repaired; plan to replace WorldClim with NASA data
- **Did:** `main` did not start (`backend/api/data.py` missing after the revert `6b2cae8`); re-applied the merge locally (`10adde3`, not pushed), 122 tests pass, app runs. Reviewed data against the challenge resources: WorldClim is not NASA and is air temperature. Drafted the replacement plan (MOD11C3/MYD11C3 LST, GPM_3IMERGM precipitation, MCD12C1 land mask); sizes checked in CMR (74 MB/month, 18 MB/month, 1.2 GB).
- **Files:** `PLAN.md` (decision + open question), `PROGRESS_LOG.md`
- **Next:** on go-ahead: download script, new climate pipeline, rebuild features/targets/scores, re-approve Moon temperature bands.
- **Blockers:** no Earthdata login on this machine (`~/.netrc` missing); HDF4 reader (`pyhdf`) not installed; ETOPO is NOAA, team to decide whether it stays.

#### 2026-11-15 13:40 — Merge plan: rahul/data-setup into main
- **Did:** Confirmed origin/main is an ancestor of this branch (fast-forward, no conflicts); restored regenerated-timestamp noise in `docs/`; pushing the branch and opening a PR (merge commit, no squash, so Ashok's commits stay authored).
- **Files:** `PROGRESS_LOG.md`, `PLAN.md`
- **Next:** teammate review, merge, then everyone rebases onto main.
- **Blockers:** `backend/api/data.py` has uncommitted in-progress edits (porting API onto Ashok's engine); deliberately not included in the PR.

#### 2026-11-15 13:14 — Diviner lunar temperatures
- **Did:** Read the already-downloaded Diviner PRP table (563k triangles poleward of 85S) and set the lunar target's `temp_mean_c` (-171 C) and `temp_max_warmest_c` (-42 C); both beyond Earth's range. Cold-trap area from Diviner (9.81%) matches the LOLA PSR table (9.81%). Added preset `thermal_surface`; `thermal_cycling` stays unavailable (table has no min/range). Reran scoring; `balanced` results unchanged. 55 tests pass.
- **Files:** `backend/pipeline/target_profiles.py`, `backend/engine/similarity.py`, `frontend/app.js`, `tests/test_phase2.py`, `docs/target_profiles.json`, `docs/top_sites.json`, `docs/validation.md`
- **Next:** MODIS MOD11C3 surface temperature for Earth (needs Earthdata login) so the comparison is surface vs surface; Mars thermal inertia.
- **Blockers:** Earth side is still WorldClim air temperature; Jezero temperatures still null.

#### 2026-11-15 14:00 — Phase 7 submission pack
- **Did:** Final README (reproduction, credits, limits), `docs/SUBMISSION.md` (1:45 storyboard, 8-slide outline, judging checklist), architecture figure, Makefile `all/serve/targets/score`, `GridStore` creates its output dir. Fresh-clone reproduction test run (result below in PLAN/summary).
- **Files:** `README.md`, `docs/SUBMISSION.md`, `docs/make_architecture.py`, `docs/figures/architecture.png`, `Makefile`, `backend/pipeline/feature_store.py`
- **Next:** decide with Ashok which Phase 2/3 implementation is canonical (main has his; this branch has mine); record the demo video.
- **Blockers:** merge conflicts with origin/main in `backend/engine/similarity.py`, `tests/test_phase2.py`, `tests/test_phase3.py`, `PLAN.md`, `docs/FEATURES.md`; temperatures still unscored.

#### 2026-11-15 13:20 — Phase 6 top-site analysis
- **Did:** Wrote `docs/SITE_ANALYSIS.md`: six candidates (3 Jezero, 3 lunar pole) with matches, mismatches, exploration use, what Earth cannot replicate, and next steps; added them to PLAN.md section 9. Flags: place names approximate, temperatures unscored, sub-scores are percentile ranks.
- **Files:** `docs/SITE_ANALYSIS.md`, `PLAN.md`
- **Next:** Phase 7 submission pack (awaiting approval).
- **Blockers:** site-specific temperatures (lunar pole, Jezero); minerals not in the feature set.

#### 2026-11-15 12:50 — Phase 5 frontend
- **Did:** Interactive map app: Moon/Mars target picker, preset chips, weight sliders, top-10 with hide-famous toggle, click-anywhere site panel (radar, feature table, "where the analogy breaks down", "Earth cannot replicate"). Verified end to end in a browser incl. custom weights; screenshots captured. 54 tests pass.
- **Files:** `frontend/{index.html,style.css,app.js,README.md}`, `backend/api/main.py` (serves `/`), `docs/figures/frontend_{moon,mars}.png`
- **Next:** Phase 6 top-site analysis (awaiting approval).
- **Blockers:** needs internet for CDN libs and basemap; temperatures still unscored.

#### 2026-11-15 10:30 — Phase 4 backend API
- **Did:** FastAPI app with targets, presets, top sites (JSON/GeoJSON, with/without famous sites), per-site feature breakdown (match/partial/mismatch, not-scored, Earth-cannot-replicate), score PNG with preset or custom weights. Latency 2–270 ms. 53 tests pass.
- **Files:** `backend/api/main.py`, `backend/api/data.py`, `docs/API.md`, `tests/test_phase4.py`, `requirements.txt`
- **Next:** Phase 5 frontend (awaiting approval).
- **Blockers:** none for the API; temperature scoring still needs site-specific values.

#### 2026-11-15 10:05 — Phase 3 similarity engine
- **Did:** Percentile-distance engine with 4 presets, score maps for both targets, top-10 sites with and without famous sites, validation vs Atacama / Dry Valleys / Devon / Death Valley / Iceland (all 9 expected-feature checks pass). Top Moon sites: Andes–Atacama, Kunlun (36N 81E), East Antarctica; Mars: Andes, Egypt/Sudan desert. 46 tests pass.
- **Files:** `backend/engine/similarity.py`, `backend/engine/run_scoring.py`, `tests/test_phase3.py`, `docs/top_sites.json`, `docs/validation.md`, `docs/figures/score_*.png`; scores in `data/processed/similarity_*.nc` (git-ignored)
- **Next:** Phase 4 API (awaiting approval).
- **Blockers:** thermal_cycling preset and all temperature scoring need site-specific temperatures.

#### 2026-11-15 09:40 — Phase 1 merged, Phase 2 target profiles
- **Did:** Merged Ashok's Phase 1 from main, rebuilt the Earth grid locally (matches his report). Measured the lunar south pole (<85°S) and Jezero with the Earth estimators on a 2 km grid; placed each on Earth's area-weighted percentile scale (Moon relief 99th pct, slope 99th; Jezero relief 83rd). Moon PSR cover 9.8% of the disk. 39 tests pass.
- **Files:** `backend/pipeline/target_profiles.py`, `tests/test_phase2.py`, `docs/target_profiles.json`, `docs/figures/target_{moon,mars}_vs_earth.png`, `PLAN.md`
- **Next:** Phase 3 similarity engine (awaiting approval).
- **Blockers:** site-specific temperatures (south pole, Jezero) still missing; targets' temperature features are null.

#### 2026-11-14 21:53 — Thermal CSVs from NASA sources, normalization fix, Phase 0 alignment
- **Did:** Wrote `Datasets/Moon/moon_thermal_literature.csv` and `Datasets/Mars/mars_thermal_literature.csv` from NASA NSSDC fact sheets and Sefton-Nash 2019 (only values actually read; equator / Viking 1 / global, not south pole or Jezero). Changed `docs/FEATURES.md` normalization to the Earth reference distribution (Decision logged). Phase 0 alignment: pyproj in requirements, cross-platform Makefile, macOS README, `Datasets/` in .gitignore.
- **Files:** `docs/FEATURES.md`, `PLAN.md`, `requirements.txt`, `Makefile`, `README.md`, `.gitignore`, `Datasets/{Moon,Mars}/*_thermal_literature.csv` (git-ignored)
- **Next:** South-pole temperatures and Jezero values still missing (Williams 2019 and MEDA papers are paywalled or blocked).
- **Blockers:** need open-access copies of Williams et al. 2019 (JGR, doi:10.1029/2019JE006028) and a Jezero MEDA paper, or values supplied by a teammate.

#### 2026-11-14 21:46 — Data downloaded, adopted Ashok's Datasets layout, HF upload
- **Did:** Downloaded all of `docs/DATASETS.md` plus PDS Diviner/LOLA/MOLA (~2.2 GB). Replicated Ashok's Phase 0 on macOS (Python 3.11 venv, 13 tests pass). Moved everything to `../Datasets/{Moon,Mars,Earth}` with his file names (PDS extras in `Moon/pds/`). Uploading to private HF dataset `rahuloruganti/nasa-analog-data` in the same layout.
- **Files:** `backend/pipeline/download.py`, `download_datasets.py`, `publish_hf.py` (run with `python -m backend.pipeline.<name>`), `docs/DATA_CATALOG.md`
- **Next:** Teammates can fetch the HF repo into `Datasets/`. Makefile/README need macOS lines.
- **Blockers:** only 7 of 19 WorldClim layers downloaded; both thermal-literature CSVs still missing.

#### 2026-11-14 15:36 — Data catalog + PDS downloader
- **Did:** Wrote `docs/DATA_CATALOG.md` (data kinds, formats, per-product files/sizes checked against live PDS listings, download tiers). Wrote `backend/pipeline/download.py` (open PDS products, `--list` verified all URLs). No data downloaded yet.
- **Files:** `docs/DATA_CATALOG.md`, `backend/pipeline/download.py`
- **Next:** Approve and run `python backend/pipeline/download.py T1`; Earth products need an Earthdata login in `~/.netrc`.
- **Blockers:** Earthdata account/credentials needed from a teammate for Earth data.

#### 2026-11-14 15:21 — Added resources folder
- **Did:** Added a "Resources" subsection with the challenge's NASA/CSA/ESA/JAXA links to PROBLEM_STATEMENT.md (also kept a local-only `resources/` folder, excluded via .git/info/exclude).
- **Files:** `PROBLEM_STATEMENT.md`
- **Next:** Team picks specific data products and records them in PLAN.md.
- **Blockers:** none

#### 2026-11-14 15:17 — No AI attribution in commits
- **Did:** Added a git rule to AGENTS.md: no Claude/AI co-author trailers or "Generated with" lines in commits or PRs.
- **Files:** `AGENTS.md`
- **Next:** Team picks workstreams in PLAN.md.
- **Blockers:** none

#### 2026-11-14 — Project docs set up
- **Did:** Created problem statement, plan, progress log, and AI assistant rules.
- **Files:** `PROBLEM_STATEMENT.md`, `PLAN.md`, `PROGRESS_LOG.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`
- **Next:** Team picks workstreams in PLAN.md.
- **Blockers:** none

---

## ashok

**Now working on:** 7-slide submission deck awaiting team review

<!-- entries -->

#### 2026-11-15 16:08 — Public presentation map and README
- **Did:** Deployed the interactive Moon/Mars map publicly on Vercel and its 18 compact result assets (~5.2 MB) to public Vercel Blob. Confirmed the anonymous production link opens and the map loads ranked sites and controls. Rewrote the README for nontechnical visitors with a live link, visual walkthrough, plain-language score/limits explanations, expandable details, and setup links.
- **Files:** `frontend/`, `backend/pipeline/build_demo_assets.py`, `vercel.json`, `.vercelignore`, `.gitignore`, `README.md`, `PLAN.md`, `PROGRESS_LOG.md`
- **Next:** team review of the public demo and submission deck
- **Blockers:** none

#### 2026-11-15 15:32 — Non-technical README walkthrough and Vercel deployment check
- **Did:** Reworked the repository landing page with a plain-language project summary, illustrated Moon/Mars map tour, clickable evidence links, expandable science/setup details and an architecture diagram. Pulled `origin/main` fast-forward to `9a62b91`. Checked Vercel readiness; no CLI, project link or local login is configured, and the API depends on about 709 MB of local processed data.
- **Files:** `README.md`, `PROGRESS_LOG.md`
- **Next:** Identify a public API/data host and connect a Vercel project before deploying a working map.
- **Blockers:** Vercel cannot serve a functional app from a static upload alone; the API and large result files need an available deployment/storage path and account connection.

#### 2026-11-15 15:30 — 7-slide submission deck (data-driven, no app screenshots)
- **Did:** Built `docs/Earth_Analog_Finder_Deck.pptx` — 7 slides, 16:9, white, BTU logo left and NASA Space Apps logo right on every slide, speaker notes on all 7. All figures are generated from `data/processed` (`scores_moon.nc`, `scores_mars.nc`, `deck_summary.json`) rather than screenshots of the local app. Slides: title/team, challenge, Moon–Earth–Mars data, method pipeline + feature groups + four priorities, global score maps with headline sites (Moon 80/100 High Andes, Peru; Mars 92/100 Eastern Desert, Egypt), priority winners + known-analog validation, and uses vs. what Earth cannot replicate. Scores shown as 25 km area-weighted 0–100 site scores; Moon/Mars never compared.
- **Files:** `docs/make_deck.py`, `docs/make_deck_assets.py`, `docs/figures/deck/` (incl. trimmed BTU + Space Apps logos), `docs/deck_preview/`, `docs/Earth_Analog_Finder_Deck.pptx`
- **Next:** team review and any copy/layout edits; then commit the deck (currently untracked).
- **Blockers:** none. Deck uses Segoe UI, so non-Windows machines will substitute the font.

#### 2026-11-15 13:33 — Phase 3b: no-precipitation constraint, site stability, caveats and provenance
- **Did:** Added the **dryness constraint** on both targets (target 0 mm, declared tolerance 0–50 mm annual / 0–4 mm driest month, labelled `constraint` / `declared_tolerance`, same rank + absolute engine, weight 0.25 in `balanced`/`cold_trap_ice`, 0 in `rover_mobility`/`thermal_cycling`). Added **per-site stability** from the nine sensitivity settings (fraction staying in the top-N within 25 km), ranked beside the score. Fixed `aggregate_candidates` so sensitivity runs rank sites exactly like the report list (stability no longer spuriously 0). Added **ice/substrate caveat** boxes (Greenland, Antarctic) with "our data cannot distinguish ice cover from bare ground", and **analog provenance** (`reviewed`, `display_source`, `citation_verified`); Mauna Kea's source is never emitted. Rebuilt profiles (303.8 s) and engine (286.9 s). Coverage now Moon 10/13, 6/7; Mars 6/13, 4/7. Top sites: Moon balanced −10.275, −77.575 (0.795, stability 0.78); Moon cold_trap −84.325, 175.525 (0.783); Mars balanced 25.675, 34.575 (0.917); Mars cold_trap no longer equivalent to balanced. **114 tests pass.**
- **Files:** `backend/targets/constraints.py`, `backend/engine/build_scores.py`, `backend/engine/similarity.py`, `backend/engine/top_sites.py`, `backend/targets/build_target_profiles.py`, `backend/targets/moon_target.py`, `backend/targets/mars_target.py`, `backend/config.py`, `config/config.yaml`, `config/presets.yaml`, `config/features.yaml`, `config/targets.yaml`, `config/validation_sites.yaml`, `tests/test_phase3.py`, `tests/test_config.py`, `docs/phase3_report.md`, `docs/FEATURES.md`, `docs/hardcode_audit.md`, `README.md`, `PLAN.md`
- **Next:** Phase 4 — minimal FastAPI serving the precomputed files; every score-bearing response keeps the Mars coverage note and "Moon and Mars scores are never compared".
- **Blockers:** the instruction said both "set all four analogs reviewed: true" and "leave reviewed: false"; implemented `true` per the preamble and flagged the conflict at the gate. New famous sites (McMurdo, Ross Island, Erebus, Dry Valleys) are `reviewed: false` for team review. Rio Tinto citation still needs a spot-check; Mauna Kea has no citation.

#### 2026-11-15 12:16 — Phase 3 similarity engine, presets and top sites
- **Did:** Built the engine end-to-end (`~82 s`): area-weighted percentile table → per-feature absolute similarity `exp(−0.5·(gap/scale)²)` with a floored scale, rank similarity `1−|p_earth−q|`, hidden-gap flag, group accumulation and four config presets. Writes `scores_moon.nc`/`scores_mars.nc` (per-group grids + one grid per preset + coverage), `top_sites.json` (weights, weight share/coverage, NMS sites with and without famous sites, per-feature gaps, analog checks, sensitivity) and `docs/phase3_report.md`. Moon coverage 8/13 features, 5/7 groups; Mars 4/13, 3/7 — raw Moon/Mars scores are never compared. Top sites: Moon balanced −5.925, 146.525 (0.830); Moon cold_trap_ice −77.525, 167.725 (0.808); Mars balanced −71.725, −72.825 (0.951, terrain only, Antarctic plateau). Mars `cold_trap_ice` is flagged `equivalent_to: balanced` because it has no thermal/dryness feature. Thermal sensitivity over band shifts ±5 °C and weights {0, 0.25, 0.5}: minimum top-N overlap 0.20, minimum rho 0.975, verdict "rankings change materially", reported honestly. **99 tests pass.**
- **Files:** `backend/engine/similarity.py`, `backend/engine/top_sites.py`, `backend/engine/build_scores.py`, `backend/targets/thermal.py`, `backend/config.py`, `config/presets.yaml`, `config/config.yaml`, `config/targets.yaml`, `config/validation_sites.yaml`, `tests/test_phase3.py`, `tests/test_config.py`, `tests/test_phase2.py`, `docs/phase3_report.md`, `docs/FEATURES.md`, `docs/hardcode_audit.md`, `Makefile`, `README.md`, `PLAN.md`
- **Next:** Phase 4 (FastAPI) serving presets, sites and per-feature evidence from `top_sites.json` and the score grids.
- **Blockers:** four proposed analog sites (Licancabur, Mistastin Lake, Mauna Kea, Rio Tinto) are still `reviewed: false`; no Earth substrate/thermal-inertia map, so the Mars ranking is a terrain result only.

#### 2026-11-15 10:50 — Thermal CSVs ingested as cited reference values; PSR slope recorded as expected
- **Did:** Both literature tables arrived and are now read from disk. They use a flat `feature,value,units,source` schema, so the reader detects it and exposes them as **references**, never as target distributions: **10 Moon quantities** (subsolar 400 K, night 100 K, PSR/cold-crater 40–90 K, Cabeus 37 K, cold-craze threshold 110 K) and **4 Mars quantities, all thermal inertia (180–605 and 200–400 J m⁻² K⁻¹ s⁻¹ᐟ²) — Mars has no temperatures at all**. Kelvin→°C is an exact −273.15 offset; two bracketing `*_min`/`*_max` pairs per body become **derived ranges** that name both inputs and the subtraction rule. Temperature features stay `unavailable` and are excluded from scores, and nothing is compared numerically to WorldClim. Re-ran the Phase 2 build (185.2 s) so the JSON and all three reports carry the real values. Also rewrote the PSR slope verdict as **expected, not a failure** (PSR polygons include the shadowed crater walls that cast the shadow), keeping every number; the 1,213 m topographic-low offset and 77% below-background figure remain the alignment evidence. Report headers now take `created_utc` from the artifact instead of wall-clock time. **75 tests pass.**
- **Files:** `backend/targets/thermal.py`, `backend/targets/moon_target.py`, `backend/targets/mars_target.py`, `backend/targets/build_target_profiles.py`, `config/targets.yaml`, `tests/test_phase2.py`, `data/processed/target_profiles.json`, `docs/phase2_report.md`, `docs/psr_verification.md`, `docs/FEATURES.md`, `docs/hardcode_audit.md`, `PLAN.md`
- **Next:** present qualitative thermal-mapping options (banded anchors / cold-tail ordinal / context-only) and wait for approval, then build the Phase 3 engine with rank + absolute-gap output, area weighting, coverage-aware scoring, NMS top sites and config presets.
- **Blockers:** thermal mapping choice pending user approval; validation-site coordinates/sources to be reviewed before they are used for rank reporting.

#### 2026-11-15 01:24 — Phase 2: Moon/Mars target profiles, PSR and Hurst checks
- **Did:** Built the target side with the **same feature registry** as Earth. Moon = disc poleward of 85°S (151.713 km, 11,298,124 cells, 16 blocks on the 80 m LDEM): relief 1789 m, slope 9.29°, roughness 5/10/20 km = 77/170/374 m, Hurst 0.683, PSR area fraction 0.0983 (7,110 of 72,308 km²). Mars = Jezero 18.3628°N 77.5945°E, 150 km (5,169 cells from raw MOLA): relief 472 m, slope 1.47°, 10 km roughness 40 m; 5 km roughness and Hurst unavailable at 3.7 km/px. Verified PSRs are inside the DEM (1,531/1,531), on topographic lows (−1,213 m, 77% below background median) but slightly *steeper* than background (10.30° vs 9.18°) — reported as found. Earth Hurst without the 2 km lag shifts +0.040 with r=0.990 → robust. Reran Phase 1 (climate 51.8 s, terrain 471.4 s, merge 50.0 s) and both config-only proofs (window 20→30 km changes only relief, median 78.70→104.36 m; Sahara bbox 1200×600, 18 tiles). **72 tests pass.**
- **Files:** `config/` (+ `config/proofs/`), `backend/config.py`, `backend/features/registry.py`, `backend/targets/` (`psr.py`, `thermal.py`, `moon_target.py`, `mars_target.py`, `hurst_sensitivity.py`, `distribution.py`, `geometry.py`, `build_target_profiles.py`), `tests/test_config.py`, `tests/test_phase2.py`, `data/processed/target_profiles.json`, `docs/phase2_report.md`, `docs/psr_verification.md`, `docs/hurst_sensitivity.md`, `docs/hardcode_audit.md`, `docs/FEATURES.md`, `README.md`, `PLAN.md`, `Makefile`
- **Next:** Phase 3 — similarity engine with **rank percentile + absolute gap in real units** per feature, weight renormalisation for unavailable features, global score maps.
- **Blockers:** `moon_thermal_literature.csv` and `mars_thermal_literature.csv` are still missing, so Moon/Mars temperature is reported unavailable by exact path — supply both before thermal scoring can run.

#### 2026-11-14 22:07 — Phase 1: global 0.05° Earth feature grid
- **Did:** Built the Earth side of the analog search: a 7200×3600 (0.05°) grid from ETOPO 2022 + WorldClim 2.1 with 13 features + land mask. Terrain is computed per 10° tile on a 2 km local azimuthal-equidistant grid in km windows (relief p95−p5 at 20 km, mean slope at 20 km, high-pass roughness at 5/10/20 km, Hurst from 2–32 km lags), then area-averaged; ocean cells are filled with the nearest land elevation before filtering so bathymetry cannot fake coastal relief. Climate is five temperature statistics + two precipitation variables; WorldClim ocean nodata supplies the land mask (8,712,831 land cells, 29.3% area-weighted). Wrote `earth_features.nc` (~300 MB), `docs/earth_grid_report.md`, 13 feature maps + overview, and 21 Phase 1 tests (34 total passing).
- **Files:** `backend/pipeline/earth_grid.py`, `earth_climate.py`, `earth_terrain.py`, `build_earth_features.py`, `feature_store.py`, `tests/test_phase1.py`, `docs/FEATURES.md`, `docs/earth_grid_report.md`, `docs/figures/earth_*.png`, `README.md`, `Makefile`, `PLAN.md`, `requirements.txt`
- **Next:** Phase 2 — Moon (LOLA polar DEM + PSR table) and Mars (MOLA) target profiles using the same estimators, plus the cited thermal CSVs.
- **Blockers:** await Phase 2 approval; confirm lunar target region (poleward of 85°S vs named sites), confirm Mars site (Jezero?), and receive `moon_thermal_literature.csv` + `mars_thermal_literature.csv`.

#### 2026-11-14 16:38 — Phase 0: inventory, environment, scaffold
- **Did:** Verified every downloaded raster/CSV (CRS, resolution, nodata, sampled range, units) in `docs/data_inventory.md`; found `mars_elev.npy` absent but the raw MOLA `.img` present, both literature CSVs missing, and the WorldClim layers at 2.5 arc-min. Added pinned `requirements.txt`, repo scaffold, README, proposed `docs/FEATURES.md`, Makefile and 13 passing smoke tests.
- **Files:** `backend/paths.py`, `backend/pipeline/inspect_datasets.py`, `docs/data_inventory.md`, `docs/FEATURES.md`, `README.md`, `requirements.txt`, `Makefile`, `tests/test_phase0.py`, `.gitignore`
- **Next:** Phase 1 — regrid ETOPO/WorldClim to the 0.05° grid and derive terrain/climate features.
- **Blockers:** await approval of frontend stack and MVP feature list; confirm lunar/Mars target regions in Phase 2.

#### 2026-11-14 15:56 — Added dataset catalog
- **Did:** Added the Moon, Mars, and Earth dataset inventory with source links, feature mappings, and limitations.
- **Files:** `docs/DATASETS.md`
- **Next:** Team integrates the documented datasets into the processing pipeline.
- **Blockers:** none

---

## mrinalini

**Now working on:** —

<!-- entries -->

_No entries yet._
