# Frontend (Phase 5)

deck.gl (heat layer, site markers) + MapLibre GL JS (dark basemap) + Plotly (radar), plain ES, no build step.
Libraries load from jsDelivr and the basemap from CARTO, so the browser needs internet.

```bash
python -m uvicorn backend.api.main:app --port 8000    # serves the API and this app
# open http://localhost:8000/            (or /?target=mars_jezero)
```

Needs the Phase 1-3 outputs (see `docs/API.md`). Features: target picker, preset chips, per-feature weight sliders
(custom weights recompute the map and clicked sites), top-10 list with a "hide famous sites" toggle, click-anywhere
site panel with radar chart, feature table, **Where the analogy breaks down** and **Earth cannot replicate**.
Screenshots: `docs/figures/frontend_moon.png`, `docs/figures/frontend_mars.png`.
