"""FastAPI application: targets, score maps, top sites, site evidence.

Run from ``NASA_Space_Challenge/``::

    python -m uvicorn backend.api.main:app --port 8000

Interactive docs at http://localhost:8000/docs. Serves the precomputed Phase 1-3
outputs (``make all``). Targets are ``moon`` and ``mars``. Scores are 0-1 and
Earth-relative: a Moon score and a Mars score are never comparable.
Custom weights: ``weights={"relief": 1, "slope": 2}`` (JSON over the scored groups).
"""

from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.data import CANNOT_REPLICATE, render_png, store

@asynccontextmanager
async def lifespan(_: FastAPI):
    threading.Thread(target=lambda: (store(), store().tables()), daemon=True).start()  # warm the Earth CDF tables
    yield


app = FastAPI(lifespan=lifespan, title="Earth Analog Finder API", version="0.2",
              description="Ranks Earth land cells by similarity to a lunar south-pole or Jezero target.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

BOUNDS = [-180.0, -90.0, 180.0, 90.0]  # west, south, east, north
GROUPS = ["relief", "slope", "roughness", "scale_robust_roughness", "temperature", "dryness"]


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
        assert all(k in GROUPS and isinstance(v, (int, float)) and v >= 0 for k, v in w.items())
    except Exception:
        raise HTTPException(422, f"weights must be a JSON object of non-negative numbers keyed by {GROUPS}")
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
    """Targets with scored groups, group status/reasons, and presets."""
    s = store()
    return [{"id": t, "name": s.profiles[t]["label"], "body": s.profiles[t]["body"],
             "extent": s.profiles[t]["extent"], "groups": s.groups(t), "scored_groups": s.scored_groups(t),
             "not_scored": s.not_scored(t), "presets": s.presets(t),
             "coverage": s.top["targets"][t]["coverage"]} for t in s.targets()]


@app.get("/targets/{target}")
def target_profile(target: str):
    """Target profile: feature distributions, resolution status, ice proxy, thermal references."""
    t = target_or_404(target)
    p = store().profiles[t]
    return {"id": t, "label": p["label"], "source": p["source"], "extent": p["extent"], "features": p["features"],
            "ice_proxy": p.get("ice_proxy"), "groups": p["groups"], "thermal": p.get("thermal"),
            "earth_cannot_replicate": CANNOT_REPLICATE}


@app.get("/presets")
def presets():
    return {"groups": GROUPS, "presets": {t: store().presets(t) for t in store().targets()}}


@app.get("/targets/{target}/top-sites")
def top_sites(target: str, preset: str = "balanced", exclude_famous: bool = False,
              n: int = Query(10, ge=1, le=25), format: str = Query("json", pattern="^(json|geojson)$")):
    """Non-maximum-suppressed candidates with per-feature evidence; optionally without famous analogs."""
    t = target_or_404(target)
    p = store().top["targets"][t]["presets"].get(preset)
    if p is None or not p["weighting"]["weights_used"]:
        raise HTTPException(422, f"preset '{preset}' is unavailable for this target")
    sites = p["sites_excluding_famous" if exclude_famous else "sites"][:n]
    if format == "geojson":
        return {"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [x["lon"], x["lat"]]},
             "properties": {"rank": i, **{k: v for k, v in x.items() if k not in ("lat", "lon", "polygon", "features")}}}
            for i, x in enumerate(sites, 1)]}
    return {"target": t, "preset": preset, "label": p["label"], "exclude_famous": exclude_famous,
            "weights_used": p["weighting"]["weights_used"], "weights_dropped": p["weighting"]["weights_dropped"],
            "min_separation_km": p["min_separation_km"], "sites": sites}


@app.get("/targets/{target}/validation")
def validation(target: str, preset: str = "balanced"):
    """Known analog and spot-check sites scored by the engine (with land-percentile rank)."""
    t = target_or_404(target)
    p = store().top["targets"][t]["presets"].get(preset)
    if p is None:
        raise HTTPException(422, f"unknown preset '{preset}'")
    return {"target": t, "preset": preset, "sites": p["validation"], "score_stats": p["score_stats"]}


@app.get("/targets/{target}/site")
def site(target: str, lat: float = Query(..., ge=-90, le=90), lon: float = Query(..., ge=-180, le=180),
         preset: str | None = None, weights: str | None = None):
    """Evidence for one Earth cell: absolute gap in real units, rank similarity, hidden-gap flags, what is not scored."""
    t = target_or_404(target)
    out = guarded(store().site, t, lat, lon, preset, parse_weights(weights))
    if out is None:
        raise HTTPException(404, "no land data at this location (ocean or outside the grid)")
    return out


@lru_cache(maxsize=64)
def _png(target: str, preset: str | None, weights: str | None, step: int) -> bytes:
    s = store()
    score = s.score(target, preset, json.loads(weights) if weights else None, step)
    lo, hi = s.score_range(target, preset if not weights else "balanced")
    return render_png(score, lo, hi)


@app.get("/targets/{target}/score.png")
def score_png(target: str, preset: str | None = None, weights: str | None = None,
              step: int = Query(5, ge=1, le=20, description="decimation of the 0.05 degree grid; 5 = 0.25 degrees")):
    """Equirectangular RGBA score map (ocean transparent), scaled from the land median to the best site."""
    t = target_or_404(target)
    parse_weights(weights)
    png = guarded(_png, t, preset, weights, step)
    return Response(png, media_type="image/png", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/score-map-info")
def score_map_info():
    return {"bounds_west_south_east_north": BOUNDS, "projection": "EPSG:4326 (equirectangular)",
            "colormap": "magma", "scaling": "land area-weighted median -> best site peak score, per target and preset",
            "transparent": "ocean / no data"}


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND.joinpath("index.html").exists():  # keep last: serves the map app at /
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")
