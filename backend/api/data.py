"""Read-only data layer for the API: precomputed Phase 1-3 outputs, no heavy compute."""

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

from backend.engine.similarity import ALL_FEATURES, ICE, PRESETS
from backend.paths import DOCS_DIR, PROCESSED_DIR

LAT0, RES = 89.975, 0.05
MATCH, PARTIAL = 80.0, 60.0
ICE_WINDOW = 2
CANNOT_REPLICATE = ["reduced gravity (Moon 1/6 g, Mars 0.38 g)", "vacuum / thin atmosphere",
                    "radiation environment", "WorldClim is air temperature, not surface skin temperature"]
_lock = threading.Lock()


class Store:
    def __init__(self) -> None:
        self.profiles = json.loads((DOCS_DIR / "target_profiles.json").read_text())["targets"]
        self.top = json.loads((DOCS_DIR / "top_sites.json").read_text())
        self.sim = {k: Dataset(PROCESSED_DIR / f"similarity_{k}.nc") for k in self.profiles}
        self.earth = Dataset(PROCESSED_DIR / "earth_features.nc")

    def targets(self) -> list[str]:
        return list(self.profiles)

    def presets(self, target: str) -> dict:
        have = self.sim[target].variables
        return {p: {"weights": w, "available": f"score_{p}" in have} for p, w in PRESETS.items()}

    def features(self, target: str) -> list[str]:
        return [f for f in ALL_FEATURES if f"sub_{f}" in self.sim[target].variables]

    def factors(self, target: str) -> dict:
        return self.top["targets"][target]["feature_weight_factors"]

    # ---- raster access
    def layer(self, target: str, name: str, step: int = 1) -> np.ndarray:
        with _lock:
            a = self.sim[target][name][::step, ::step]
        return np.ma.filled(a.astype("float32"), np.nan) if np.ma.isMaskedArray(a) else a.astype("float32")

    def custom_score(self, target: str, weights: dict[str, float], step: int = 1) -> np.ndarray:
        fac = self.factors(target)
        used = {k: w * fac.get(k, 1.0) for k, w in weights.items() if f"sub_{k}" in self.sim[target].variables}
        used = {k: w for k, w in used.items() if w > 0}
        if not used:
            raise ValueError("no weighted feature has a target value for this target")
        dist = sum(w * (100 - self.layer(target, f"sub_{k}", step)) for k, w in used.items())
        return 100 - dist / sum(used.values())

    def score(self, target: str, preset: str | None, weights: dict | None, step: int = 1) -> np.ndarray:
        if weights:
            return self.custom_score(target, weights, step)
        name = preset or "balanced"
        if f"score_{name}" not in self.sim[target].variables:
            raise ValueError(f"preset '{name}' is unavailable for this target")
        return self.layer(target, f"score_{name}", step)

    # ---- site details
    def cell(self, lat: float, lon: float) -> tuple[int, int]:
        return int(round((LAT0 - lat) / RES)), int(round((lon + 179.975) / RES))

    def earth_value(self, name: str, r: int, c: int) -> float | None:
        if name == ICE:
            return self.frozen_fraction(r, c)
        with _lock:
            v = self.earth[name][r, c]
        return None if np.ma.is_masked(v) or not np.isfinite(v) else float(v)

    def frozen_fraction(self, r: int, c: int) -> float | None:
        with _lock:
            w = np.ma.filled(self.earth["temp_max_warmest_c"][max(r - ICE_WINDOW, 0):r + ICE_WINDOW + 1,
                                                              max(c - ICE_WINDOW, 0):c + ICE_WINDOW + 1], np.nan)
        valid = np.isfinite(w)
        return float((w[valid] < 0).mean()) if valid.any() and valid[min(r, ICE_WINDOW), min(c, ICE_WINDOW)] else None

    def site(self, target: str, lat: float, lon: float, preset: str | None, weights: dict | None) -> dict | None:
        r, c = self.cell(lat, lon)
        score = self.score_at(target, preset, weights, r, c)
        if score is None:
            return None
        fac, prof = self.factors(target), self.profiles[target]
        used = weights or PRESETS[preset or "balanced"]
        rows = []
        for f in self.features(target):
            with _lock:
                sub = float(self.sim[target][f"sub_{f}"][r, c])
            pf = prof["features"].get(f, {})
            tv = prof["ice_cold_trap_proxy"].get("cold_trap_area_fraction") if f == ICE else pf.get("value")
            w = used.get(f, 0) * fac.get(f, 1.0)
            rows.append({
                "feature": f, "earth_value": self.earth_value(f, r, c), "target_value": tv,
                "units": "fraction" if f == ICE else pf.get("units", ""), "sub_score": round(sub, 1),
                "verdict": "match" if sub >= MATCH else "partial" if sub >= PARTIAL else "mismatch",
                "weight": round(w, 3),
                "note": (pf.get("limitation") or "") if f != ICE else
                        "Share of the area whose annual maximum stays frozen: Earth warmest month below 0 C within 0.25 deg, "
                        "Moon Diviner annual maximum below 110 K.",
            })
        return {"target": target, "lat": float(LAT0 - r * RES), "lon": float(-179.975 + c * RES),
                "score": round(score, 1), "features": rows,
                "does_not_match": [x["feature"] for x in rows if x["verdict"] == "mismatch"],
                "not_scored": self.top["targets"][target]["dropped_features"],
                "earth_cannot_replicate": CANNOT_REPLICATE}

    def score_at(self, target, preset, weights, r, c) -> float | None:
        if not (0 <= r < 3600 and 0 <= c < 7200):
            return None
        with _lock:
            probe = self.sim[target]["sub_relief_20km_m"][r, c]
        if np.ma.is_masked(probe):
            return None
        if weights:
            fac = self.factors(target)
            used = {k: w * fac.get(k, 1.0) for k, w in weights.items() if f"sub_{k}" in self.sim[target].variables}
            used = {k: w for k, w in used.items() if w > 0}
            if not used:
                raise ValueError("no weighted feature has a target value for this target")
            with _lock:
                vals = {k: float(self.sim[target][f"sub_{k}"][r, c]) for k in used}
            return 100 - sum(w * (100 - vals[k]) for k, w in used.items()) / sum(used.values())
        name = preset or "balanced"
        if f"score_{name}" not in self.sim[target].variables:
            raise ValueError(f"preset '{name}' is unavailable for this target")
        with _lock:
            return float(self.sim[target][f"score_{name}"][r, c])


@lru_cache(maxsize=1)
def store() -> Store:
    return Store()


def render_png(score: np.ndarray, vmin: float = 40.0, vmax: float = 100.0) -> bytes:
    """Colour a score grid (NaN = transparent) as an RGBA PNG."""
    from PIL import Image

    norm = np.clip((score - vmin) / (vmax - vmin), 0, 1)
    rgba = (cm.magma(norm) * 255).astype("uint8")
    rgba[~np.isfinite(score), 3] = 0
    buf = io.BytesIO()
    Image.fromarray(rgba).save(buf, format="PNG", optimize=True)
    return buf.getvalue()
