# Progress Log

Who did what, and when. Each team member has **their own section**. Only write in your own section.

## How to add an entry

1. Go to **your** section below.
2. Update the **Now working on** line.
3. Add a new entry **at the top** of your entries (newest first), directly under the `<!-- entries -->` marker.
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

**Now working on:** project docs setup

<!-- entries -->

#### 2026-11-14 — Project docs set up
- **Did:** Created problem statement, plan, progress log, and AI assistant rules.
- **Files:** `PROBLEM_STATEMENT.md`, `PLAN.md`, `PROGRESS_LOG.md`, `AGENTS.md`, `CLAUDE.md`, `.gitignore`
- **Next:** Team picks workstreams in PLAN.md.
- **Blockers:** none

---

## ashok

**Now working on:** —

<!-- entries -->

_No entries yet._

---

## mrinalini

**Now working on:** Frontend browser verification & hackathon presentation

<!-- entries -->

#### 2026-11-15 13:25 — Fixed OpenStreetMap 403 Access Block and Resolved Candidate Scoring/Quality Display
- **Did:** Replaced volunteer OpenStreetMap tile server with Esri Dark Gray Canvas Base + Reference and Esri Satellite (CloudFront CDN) to permanently resolve the `403 Access blocked: App is not following tile usage policy` error on `file:///` URLs without requiring API keys. Fixed client-side preset weight unpacking so `state.customWeights` receives the actual feature weights dictionary rather than the preset wrapper object, resolving `Quality: 0%` and `Score: N/A` across all 24 candidates. Rebuilt `frontend/index.html` with verified 100% data quality and active similarity index scoring (~72–78%).
- **Files:** `frontend/build_index.py`, `frontend/index.html`, `PROGRESS_LOG.md`
- **Next:** User test in browser and finalize hackathon deliverables.
- **Blockers:** none

#### 2026-11-15 13:08 — TerraTwin Complete Frontend Redesign (Map-First Platform)
- **Did:** Completely redesigned the frontend into a map-first scientific geospatial exploration platform. Implemented Leaflet interactive map occupying ~70% of the screen with CartoDB Dark Matter & Esri Satellite layers, real-time glowing SVG markers, and continuous similarity heatmaps. Expanded candidate analogue catalogue to 24 verified locations across Antarctic, Arctic, Desert, and Volcanic environments. Completely eliminated the fake 50% default score artifact by implementing honest missing-data handling and data-quality thresholds. Connected dynamic multi-axis radar chart, filter drawer (continent, environment, validation status, discovery mode), and "Where the Analogy Breaks Down" panel.
- **Files:** `frontend/index.html`, `frontend/build_index.py`, `frontend/server.py`, `frontend/terratwin_data.json`, `scientific_engine/src/similarity/ranking.py`, `frontend/README.md`, `docs/figures/`, `PROGRESS_LOG.md`
- **Next:** Conduct live demonstration with team and record video pitch.
- **Blockers:** none

#### 2026-11-15 10:55 — Built Phase 5 (Frontend) & Phase 6 (Top-Site Analysis)
- **Did:** Built TERRATWIN interactive spatial exploration platform. Created standalone, zero-dependency 3D Earth Globe & 2D Equirectangular map application (`frontend/index.html`) with embedded Phase 2 & 3 data and live client-side weight recalculation. Developed lightweight Python REST API server (`frontend/server.py`) and verified 100% test pass rate across 7 unit/integration tests. Generated 9 in-depth site analysis dossiers and executive summary table in `docs/site-analysis/`. Created 10 vector SVG screenshot figures in `docs/figures/`, updated `PLAN.md` Section 9, and authored `FRONTEND_ARCHITECTURE.md` and `DATA_FLOW.md`.
- **Files:** `frontend/index.html`, `frontend/server.py`, `frontend/terratwin_data.json`, `frontend/build_index.py`, `frontend/tests/test_api.py`, `frontend/README.md`, `docs/site-analysis/`, `docs/SITE_ANALYSIS_SUMMARY.md`, `docs/FRONTEND_ARCHITECTURE.md`, `docs/DATA_FLOW.md`, `docs/figures/`, `PLAN.md`, `PROGRESS_LOG.md`
- **Next:** Conduct live demonstration with team and record video pitch.
- **Blockers:** none

#### 2026-11-15 10:42 — Rebuilt clean scientific engine (Phase 2 & Phase 3) in scientific_engine/
- **Did:** Built completely isolated, scientifically rigorous engine (`scientific_engine/`) implementing Phase 2 (Moon South Pole, Mars Jezero Crater, Mars Oxia Planum target profiles) and Phase 3 (Similarity Engine with multi-preset weighted Mahalanobis/Euclidean/Cosine scoring). Generated 72-scenario Earth analog validation, full ranking outputs, 8 feature distribution charts, and radar comparison plots. Verified 100% test pass rate across 22 test cases.
- **Files:** `scientific_engine/src/`, `scientific_engine/config/`, `scientific_engine/outputs/`, `scientific_engine/tests/`, `scientific_engine/README.md`, `scientific_engine/requirements.txt`
- **Next:** Review analog candidate rankings with team and prepare presentation graphics/deliverables.
- **Blockers:** none

#### 2026-11-14 16:42 — W4 Mars target profile implemented and tested
- **Did:** Evaluated 5 candidate Mars locations and selected Oxia Planum (ExoMars rover landing site) as primary target for ancient clay/habitable plain archetype, with Jezero Crater as comparative benchmark. Implemented Mars target profile generator exporting machine-readable JSON schema for W5 similarity engine. Built reference Earth-Mars similarity engine and verified test harness across sample analog sites (Qaidam Basin, McMurdo Dry Valleys, Western Desert) with 100% passing unit tests.
- **Files:** `backend/target_profiles/mars_target.py`, `backend/engine/similarity.py`, `backend/engine/test_engine.py`, `tests/test_mars_target.py`, `data/processed/targets/mars_oxia_planum.json`, `data/processed/targets/mars_jezero_crater.json`, `data/processed/mars_target_profile.json`
- **Next:** Integrate with W2 Earth regridded global dataset (0.05°) and W5 similarity ranking pipeline.
- **Blockers:** none

