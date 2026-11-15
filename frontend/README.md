# Frontend (Phase 5)

Vite + vanilla JS interactive map: MapLibre GL JS basemap, deck.gl top-site markers, Plotly radar. The similarity score map is reprojected to Web Mercator in the browser so its latitudes line up with the basemap.

Run the API first, from the repo root:

```bash
.venv/Scripts/python -m uvicorn backend.api.main:app --port 8000   # Windows
python -m uvicorn backend.api.main:app --port 8000                 # macOS / Linux
```

Then, in a second terminal:

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to http://localhost:8000
npm run build      # production bundle in dist/
```

The dev server proxies `/api/*` to the API, so the API must be running. The basemap is loaded from `basemaps.cartocdn.com`, so an internet connection is needed for the basemap tiles.

Known limits: the Mercator map cannot show latitudes beyond about 85 degrees, so the polar caps are cut at the top and bottom edges. Top-site markers are precomputed for the presets only and do not change with custom weights.
