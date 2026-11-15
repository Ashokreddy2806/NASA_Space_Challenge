"""Read-only data layer for the API, built on the Phase 1-3 outputs (Ashok's engine).

Nothing heavy runs at request time: scores come from ``scores_<target>.nc`` and
``top_sites.json``; per-site evidence reuses ``build_scores.feature_site_rows``;
custom weights recombine the stored group grids.
"""

from __future__ import annotations

import io
import json
import threading
from functools import lru_cache

import matplotlib

matplotlib.use("Agg")
import numpy as np
from matplotlib import cm
from netCDF4 import Dataset

from backend.config import load_config
from backend.engine import similarity, top_sites
from backend.engine.build_scores import feature_site_rows

CANNOT_REPLICATE = [
    "reduced gravity (Moon about 1/6 g, Mars 0.38 g)",
    "vacuum / thin atmosphere",
    "radiation environment",
    "Earth temperatures are air temperatures (WorldClim), not surface skin temperatures",
]
_lock = threading.Lock()
POINT_RADIUS_KM = 5.0  # 3 x 3 cells around a clicked point


class Store:
    def __init__(self) -> None:
        self.config = load_config()
        out = self.config.output
        self.profiles = json.loads(out("target_profiles").read_text(encoding="utf-8"))
        self.top = json.loads(out("top_sites").read_text(encoding="utf-8"))
        self.scores = {t: Dataset(str(out(f"scores_{t}")), "r") for t in self.targets()}
        self.earth = similarity.EarthStore(self.config)
        self._tables: dict[str, dict] | None = None

    def targets(self) -> list[str]:
        return [t for t in ("moon", "mars") if t in self.top["targets"]]

    # ---- metadata
    def presets(self, target: str) -> dict:
        out = {}
        for name, p in self.top["targets"][target]["presets"].items():
            used = p["weighting"]["weights_used"]
            out[name] = {"label": p["label"], "weights": p["weights"], "weights_used": used,
                         "weights_dropped": p["weighting"]["weights_dropped"],
                         "available": bool(used), "coverage": p["coverage"]}
        return out

    def groups(self, target: str) -> list[dict]:
        return [{"group": g["group"], "weight": g["weight"], "status": g["status"], "reason": g["reason"],
                 "members": g["available_members"]} for g in self.profiles[target]["groups"]]

    def scored_groups(self, target: str) -> list[str]:
        return [v[len("group_"):] for v in self.scores[target].variables if v.startswith("group_")]

    # ---- rasters
    def _read(self, target: str, name: str, step: int) -> np.ndarray:
        with _lock:
            a = self.scores[target][name][::step, ::step]
        return np.ma.filled(np.ma.masked_invalid(a).astype("float32"), np.nan)

    def score(self, target: str, preset: str | None, weights: dict | None, step: int = 1) -> np.ndarray:
        if not weights:
            name = preset or "balanced"
            if name not in self.top["targets"][target]["presets"] or f"score_{name}" not in self.scores[target].variables:
                raise ValueError(f"unknown preset '{name}'")
            if not self.presets(target)[name]["available"]:
                raise ValueError(f"preset '{name}' is unavailable for this target")
            return self._read(target, f"score_{name}", step)
        groups = {g: self._read(target, f"group_{g}", step) for g in self.scored_groups(target)}
        score, _ = similarity.preset_score(self.config, target, groups, weights)
        return score

    def score_range(self, target: str, preset: str | None) -> tuple[float, float]:
        p = self.top["targets"][target]["presets"][preset or "balanced"]
        sites = p["sites"]
        return p["score_stats"]["land_area_weighted_p50"], (sites[0]["peak_score"] if sites else 1.0)

    # ---- site evidence
    def tables(self) -> dict:
        """Earth percentile tables per target, built once on first use (about 15 s)."""
        with _lock:
            if self._tables is None:
                scaled = {t: similarity.scaled_features(self.config, self.profiles[t]) for t in self.targets()}
                ids = {f for t in scaled for f, s in scaled[t].items() if not s.qualitative}
                shared = {}
                for fid in sorted(ids):
                    v = self.earth.read(fid)
                    ok = self.earth.land & np.isfinite(v)
                    shared[fid] = similarity.weighted_cdf_table(v[ok], self.earth.cell_weight[ok],
                                                                self.config.scoring.cdf_quantiles)
                self._tables = {t: {f: shared[f] for f, s in scaled[t].items() if not s.qualitative}
                                for t in scaled}
        return self._tables

    def cell(self, lat: float, lon: float) -> tuple[int, int]:
        return top_sites.nearest_cell(self.earth.lat, self.earth.lon, lat, lon)

    def site(self, target: str, lat: float, lon: float, preset: str | None, weights: dict | None) -> dict | None:
        r, c = self.cell(lat, lon)
        if not self.earth.land[r, c]:
            return None
        clat, clon = float(self.earth.lat[r]), float(self.earth.lon[c])
        groups = {}
        for g in self.scored_groups(target):
            with _lock:
                v = self.scores[target][f"group_{g}"][r, c]
            if not np.ma.is_masked(v) and np.isfinite(v):
                groups[g] = float(v)
        if weights:
            w = weights
        else:
            name = preset or "balanced"
            p = self.top["targets"][target]["presets"].get(name)
            if p is None or not p["weighting"]["weights_used"]:
                raise ValueError(f"preset '{name}' is unavailable for this target")
            w = p["weights"]
        usable = {g: x for g, x in w.items() if x > 0 and g in groups}
        if not usable:
            raise ValueError("no weighted group is available for this target")
        score = sum(groups[g] * x for g, x in usable.items()) / sum(usable.values())
        tables = self.tables()[target]
        with _lock:
            rows = feature_site_rows(self.config, self.earth, self.profiles[target], tables,
                                     clat, clon, POINT_RADIUS_KM)
        famous, famous_name = top_sites.is_famous(self.config, clat, clon)
        return {"target": target, "lat": clat, "lon": clon, "score": float(score),
                "weights_used": usable, "group_scores": groups, "features": rows,
                "hidden_gaps": [x["feature"] for x in rows if x.get("hidden_real_unit_gap")],
                "not_scored": self.not_scored(target), "famous_near": famous_name if famous else None,
                "earth_cannot_replicate": CANNOT_REPLICATE}

    def not_scored(self, target: str) -> list[dict]:
        out = []
        for fid, f in self.profiles[target]["features"].items():
            if f.get("resolution") in ("unavailable", "marginal", "qualitative") or f.get("median") is None and not f.get("qualitative"):
                out.append({"feature": fid, "status": f.get("resolution"), "note": f.get("resolution_note", "")})
        return out


@lru_cache(maxsize=1)
def store() -> Store:
    return Store()


def render_png(score: np.ndarray, vmin: float, vmax: float) -> bytes:
    from PIL import Image

    norm = np.clip((score - vmin) / max(vmax - vmin, 1e-6), 0, 1)
    rgba = (cm.magma(norm) * 255).astype("uint8")
    rgba[~np.isfinite(score), 3] = 0
    buf = io.BytesIO()
    Image.fromarray(rgba).save(buf, format="PNG", optimize=True)
    return buf.getvalue()
