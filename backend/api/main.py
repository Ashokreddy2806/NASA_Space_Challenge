"""FastAPI application: targets, score maps, top sites, site breakdowns.

Run from ``NASA_Space_Challenge/``::

    python -m uvicorn backend.api.main:app --port 8000

Interactive docs at http://localhost:8000/docs. Everything is served from the
precomputed Phase 1-3 outputs (``python -m backend.engine.run_scoring``).
Custom weights: pass ``weights={"slope_20km_deg": 3, "relief_20km_m": 1}`` (JSON).
"""

from __future__ import annotations

import json
from functools import lru_cache

import numpy as np
from fastapi import FastAPI, HTTPException, Query, Response
from pathlib import Path

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.data import CANNOT_REPLICATE, render_png, store
from backend.engine.similarity import ALL_FEATURES

app = FastAPI(title="Earth Analog Finder API", version="0.1",
              description="Ranks Earth land cells by similarity to a lunar south-pole or Jezero target.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

BOUNDS = [-180.0, -90.0, 180.0, 90.0]  # west, south, east, north


def target_or_404(target: str) -> str:
    if target not in store().targets():
        raise HTTPException(404, f"unknown target '{target}'; choose from {store().targets()}")
    return target


def parse_weights(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        w = json.loads(raw)
        assert isinstance(w, dict) and w
        assert all(k in ALL_FEATURES and isinstance(v, (int, float)) and v >= 0 for k, v in w.items())
    except Exception:
        raise HTTPException(422, f"weights must be a JSON object of non-negative numbers keyed by {ALL_FEATURES}")
    return w


def guarded(fn, *a):
    try:
        return fn(*a)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.get("/health")
def health():
    return {"status": "ok", "targets": store().targets()}


@app.get("/targets")
def targets():
    """Targets with profile summary and what is (not) scored."""
    s = store()
    return [{"id": t, "name": s.profiles[t]["name"], "body": s.profiles[t]["body"],
             "region": s.profiles[t]["region"], "features_scored": s.features(t),
             "not_scored": s.top["targets"][t]["dropped_features"],
             "presets": s.presets(t)} for t in s.targets()]


@app.get("/targets/{target}")
def target_profile(target: str):
    """Full target profile (values, spread, Earth percentile, limitations) plus the standing limits."""
    t = target_or_404(target)
    return {**store().profiles[t], "earth_cannot_replicate": CANNOT_REPLICATE}


@app.get("/presets")
def presets():
    return {"features": ALL_FEATURES, "presets": {t: store().presets(t) for t in store().targets()}}


@app.get("/targets/{target}/top-sites")
def top_sites(target: str, preset: str = "balanced", exclude_famous: bool = False,
              n: int = Query(10, ge=1, le=10), format: str = Query("json", pattern="^(json|geojson)$")):
    """Precomputed top candidates; set exclude_famous to hide the well-known analog regions."""
    t = target_or_404(target)
    block = store().top["targets"][t]["presets"].get(preset)
    if block is None or "status" in block:
        raise HTTPException(422, f"preset '{preset}' is unavailable for this target")
    sites = block["top_without_famous_sites" if exclude_famous else "top_overall"][:n]
    if format == "geojson":
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [p["lon"], p["lat"]]},
             "properties": {"rank": i, **{k: v for k, v in p.items() if k not in ("lat", "lon")}}}
            for i, p in enumerate(sites, 1)]}
    return {"target": t, "preset": preset, "exclude_famous": exclude_famous,
            "features_used": block["features_used"], "sites": sites}


@app.get("/targets/{target}/site")
def site(target: str, lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
         preset: str | None = None, weights: str | None = None):
    """Per-feature breakdown for one Earth location: what matches, what does not, what Earth cannot replicate."""
    t = target_or_404(target)
    out = guarded(store().site, t, lat, lon, preset, parse_weights(weights))
    if out is None:
        raise HTTPException(404, "no land data at this location (ocean or outside the grid)")
    return out


@lru_cache(maxsize=64)
def _png(target: str, preset: str | None, weights: str | None, step: int) -> bytes:
    return render_png(store().score(target, preset, json.loads(weights) if weights else None, step))


@app.get("/targets/{target}/score.png")
def score_png(target: str, preset: str | None = None, weights: str | None = None,
              step: int = Query(5, ge=1, le=20, description="decimation of the 0.05 degree grid; 5 = 0.25 degrees")):
    """Equirectangular RGBA score map (ocean transparent). Bounds: see /score-map-info."""
    t = target_or_404(target)
    parse_weights(weights)
    png = guarded(_png, t, preset, weights, step)
    return Response(png, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/score-map-info")
def score_map_info():
    return {"bounds_west_south_east_north": BOUNDS, "projection": "EPSG:4326 (equirectangular)",
            "colormap": "magma", "value_range": [40, 100], "transparent": "ocean / no data"}


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND.joinpath("index.html").exists():  # keep last: serves the map app at /
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
