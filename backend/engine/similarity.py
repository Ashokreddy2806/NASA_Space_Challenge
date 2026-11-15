"""Phase 3 similarity engine: scaled physical distance to a target.

Method (docs/FEATURES.md, "Normalization and scoring"):
  1. Relief, slope and roughness are log1p-transformed, precipitation is log1p(x / ~Earth P5); Hurst and
     temperatures are used as they are. Each feature's scale is the area-weighted
     Earth land P95 - P5 of the transformed values.
  2. Per-feature distance d = min(1, |t_cell - t_target| / scale); sub-score = 100*(1 - d).
  3. ice_proxy = fraction of land cells within 0.25 deg whose warmest month stays below 0 C
     (Earth) or the Diviner area fraction below 110 K (Moon); d = |sqrt(f_cell) - sqrt(f_target)|.
  4. Overall distance D = sum(w*d)/sum(w) over features that have a target value; score = 100*(1 - D).

Features without a target value (e.g. Mars temperatures) are dropped and reported, never guessed.
"""

from __future__ import annotations

import numpy as np
from netCDF4 import Dataset
from scipy.ndimage import uniform_filter

from backend.paths import PROCESSED_DIR

TEMPS = ["temp_mean_c", "temp_diurnal_range_c", "temp_max_warmest_c", "temp_min_coldest_c", "temp_annual_range_c"]
GRID_FEATURES = [
    "relief_20km_m", "slope_20km_deg", "roughness_5km_m", "roughness_10km_m", "roughness_20km_m",
    "hurst_2_32km", "precip_annual_mm", "precip_driest_month_mm", *TEMPS,
]
LOG_FEATURES = {"relief_20km_m", "slope_20km_deg", "roughness_5km_m", "roughness_10km_m", "roughness_20km_m"}
# Precipitation is log1p(x / ref) with ref near Earth's driest 5%, so a 15 mm desert stays close to a 0 mm target.
PRECIP_REF_MM = {"precip_annual_mm": 30.0, "precip_driest_month_mm": 3.0}
ICE = "ice_proxy"
ALL_FEATURES = [*GRID_FEATURES, ICE]

# Relative weights per preset. The ice proxy is reported as its own sub-score and
# is mixed into the overall score by the balanced and cold-trap presets.
PRESETS: dict[str, dict[str, float]] = {
    "balanced": {"relief_20km_m": 1, "slope_20km_deg": 1, "roughness_5km_m": 1 / 3, "roughness_10km_m": 1 / 3,
                 "roughness_20km_m": 1 / 3, "hurst_2_32km": 0.5, "precip_annual_mm": 0.5,
                 "precip_driest_month_mm": 0.5, ICE: 0.5},
    "rover_mobility": {"slope_20km_deg": 3, "relief_20km_m": 1, "roughness_5km_m": 2 / 3,
                       "roughness_10km_m": 2 / 3, "roughness_20km_m": 2 / 3, "hurst_2_32km": 0.5},
    "cold_trap_ice": {ICE: 3, "relief_20km_m": 0.5, "slope_20km_deg": 0.5, "precip_annual_mm": 0.5,
                      "precip_driest_month_mm": 0.5},
    "thermal_cycling": {"temp_mean_c": 1, "temp_max_warmest_c": 1},
}
# Target status -> weight multiplier. measured_surface (Diviner skin temperature) is not air
# temperature, so it counts half.
STATUS_FACTOR = {"measured": 1.0, "measured_surface": 0.5, "reduced_lags": 0.5, "resolution_limited": 0.0}


# ------------------------------------------------------------ distributions

class Ecdf:
    """Area-weighted empirical distribution of one Earth feature."""

    def __init__(self, values: np.ndarray, weights: np.ndarray):
        order = np.argsort(values)
        self.values = values[order]
        cw = np.concatenate([[0.0], np.cumsum(weights[order], dtype="float64")])
        self.cum = cw / cw[-1]

    def percentile(self, x: np.ndarray | float) -> np.ndarray:
        """Mid-rank percentile (0-100) of x on the Earth scale."""
        x = np.asarray(x)
        lo = np.searchsorted(self.values, x, "left")
        hi = np.searchsorted(self.values, x, "right")
        return ((self.cum[lo] + self.cum[hi]) / 2 * 100).astype("float32")

    def value_at(self, p: float) -> float:
        return float(self.values[np.searchsorted(self.cum, p / 100) - 1])


def transform(name: str, x):
    if name in PRECIP_REF_MM:
        return np.log1p(x / PRECIP_REF_MM[name])
    return np.log1p(x) if name in LOG_FEATURES else x


def cold_trap_fraction(tmax_warmest: np.ndarray) -> np.ndarray:
    valid = np.isfinite(tmax_warmest)
    frozen = valid & (tmax_warmest < 0)
    num = uniform_filter(frozen.astype("float32"), size=5)
    den = uniform_filter(valid.astype("float32"), size=5)
    # Ocean windows can hold no valid cell, so the ratio is only taken where the cell is land.
    return np.divide(num, den, out=np.full(valid.shape, np.nan, "float32"), where=valid)


def load_earth(path=None) -> tuple[dict[str, np.ndarray], dict[str, Ecdf], dict[str, float], np.ndarray, np.ndarray]:
    """Return per-feature transformed grids (float16, NaN off land), ECDFs, scales, lat, lon."""
    with Dataset(path or PROCESSED_DIR / "earth_features.nc") as ds:
        lat, lon = np.asarray(ds["lat"][:]), np.asarray(ds["lon"][:])
        w = np.broadcast_to(np.cos(np.radians(lat))[:, None], (lat.size, lon.size))
        grids, ecdfs, scales = {}, {}, {}
        for name in GRID_FEATURES:
            t = transform(name, np.ma.filled(ds[name][:], np.nan).astype("float32"))
            ok = np.isfinite(t)
            ecdfs[name] = Ecdf(t[ok], w[ok])
            scales[name] = ecdfs[name].value_at(95) - ecdfs[name].value_at(5)
            grids[name] = t.astype("float16")
    ice = cold_trap_fraction(grids["temp_max_warmest_c"])
    ok = np.isfinite(ice)
    ecdfs[ICE] = Ecdf(ice[ok], w[ok])
    grids[ICE] = ice.astype("float16")
    return grids, ecdfs, scales, lat, lon


# ------------------------------------------------------------ targets

def target_values(profile: dict) -> tuple[dict[str, float], dict[str, str], dict[str, float]]:
    """Transformed target value per feature, dropped-feature reasons, and per-feature status factors."""
    vals, dropped, factor = {}, {}, {}
    for name, f in profile["features"].items():
        if f["value"] is None:
            dropped[name] = f["status"]
        else:
            vals[name] = float(transform(name, f["value"]))
            factor[name] = STATUS_FACTOR.get(f["status"], 1.0)
    ice = profile.get("ice_cold_trap_proxy", {})
    if ice.get("status") == "measured":
        vals[ICE], factor[ICE] = ice["cold_trap_area_fraction"], 1.0
    else:
        dropped[ICE] = ice.get("status", "missing")
    return vals, dropped, factor


def feature_distance(name: str, cell: np.ndarray, target: float, scales: dict[str, float]) -> np.ndarray:
    if name == ICE:
        return np.abs(np.sqrt(cell.astype("float32")) - np.sqrt(target))
    return np.minimum(1, np.abs(cell.astype("float32") - target) / scales[name])


def score_map(grids: dict[str, np.ndarray], target: dict[str, float], weights: dict[str, float],
              scales: dict[str, float], factor: dict[str, float] | None = None,
              ) -> tuple[np.ndarray, dict[str, np.ndarray], list[str]]:
    """Overall score (0-100, NaN off land), per-feature sub-scores, and the features used."""
    factor = factor or {}
    used = {k: w * factor.get(k, 1.0) for k, w in weights.items() if k in target and w * factor.get(k, 1.0) > 0}
    shape = next(iter(grids.values())).shape
    dist, total = np.zeros(shape, dtype="float32"), 0.0
    subs = {}
    for k in ALL_FEATURES:
        if k not in target:
            continue
        d = feature_distance(k, grids[k], target[k], scales)
        subs[k] = (100 * (1 - d)).astype("float32")
        if k in used:
            dist += used[k] * d
            total += used[k]
    if total == 0:
        return np.full(shape, np.nan, dtype="float32"), subs, []
    return (100 * (1 - dist / total)).astype("float32"), subs, sorted(used)


# ------------------------------------------------------------ sites

FAMOUS = {  # name: (lat, lon, exclusion radius km): the sites "everyone already knows"
    "Atacama": (-24.0, -69.5, 400), "McMurdo Dry Valleys": (-77.5, 162.0, 300),
    "Devon Island / Haughton": (75.4, -89.5, 300), "Death Valley": (36.5, -116.9, 300),
    "Iceland": (64.8, -18.5, 400), "Hawaii": (19.7, -155.5, 300), "Mojave": (35.0, -116.0, 300),
    "Svalbard": (78.5, 16.0, 300), "Sahara (Libya/Egypt)": (24.0, 20.0, 600),
}


def km_between(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def top_sites(score: np.ndarray, lat: np.ndarray, lon: np.ndarray, n: int = 10, min_sep_km: float = 300,
              exclude_famous: bool = False) -> list[dict]:
    """Greedy non-maximum suppression on 0.5 degree block maxima."""
    h, w = score.shape
    k = 10
    blocks = np.nanmax(score[: h // k * k, : w // k * k].reshape(h // k, k, w // k, k), axis=(1, 3))
    arg = np.nan_to_num(blocks, nan=-1)
    blat = lat[: h // k * k].reshape(h // k, k).mean(axis=1)
    blon = lon[: w // k * k].reshape(w // k, k).mean(axis=1)
    LA, LO = np.meshgrid(blat, blon, indexing="ij")
    if exclude_famous:
        for la, lo, r in FAMOUS.values():
            arg[km_between(LA, LO, la, lo) <= r] = -1
    picks = []
    while len(picks) < n:
        i = np.unravel_index(np.argmax(arg), arg.shape)
        if arg[i] < 0:
            break
        # refine to the best 0.05 degree cell inside the block
        sub = score[i[0] * k:(i[0] + 1) * k, i[1] * k:(i[1] + 1) * k]
        j = np.unravel_index(np.nanargmax(sub), sub.shape)
        r, c = i[0] * k + j[0], i[1] * k + j[1]
        picks.append({"row": int(r), "col": int(c), "lat": float(lat[r]), "lon": float(lon[c]),
                      "score": float(score[r, c])})
        arg[km_between(LA, LO, lat[r], lon[c]) <= min_sep_km] = -1
    return picks
