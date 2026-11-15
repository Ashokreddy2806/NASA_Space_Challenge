"""Phase 3 similarity engine: Earth-percentile weighted distance to a target.

Method (docs/FEATURES.md, "Normalization and scoring"):
  1. Every feature is converted to its percentile in the area-weighted Earth land
     distribution (mid-rank for ties). Targets are placed on the same scale.
  2. Per-feature distance d = |pct_cell - pct_target| / 100  (0 = identical).
  3. Overall distance D = sum(w*d)/sum(w) over features that have a target value;
     score = 100*(1 - D). Sub-score of a feature = 100*(1 - d).

Features without a target value (e.g. temperatures) are dropped and reported,
never guessed. Dryness is one-sided: the target sits at Earth percentile 0.
"""

from __future__ import annotations

import numpy as np
from netCDF4 import Dataset

from backend.paths import PROCESSED_DIR

TEMPS = ["temp_mean_c", "temp_diurnal_range_c", "temp_max_warmest_c", "temp_min_coldest_c", "temp_annual_range_c"]
GRID_FEATURES = [
    "relief_20km_m", "slope_20km_deg", "roughness_5km_m", "roughness_10km_m", "roughness_20km_m",
    "hurst_2_32km", "precip_annual_mm", "precip_driest_month_mm", *TEMPS,
]
# "ice_proxy" is the coldest-month minimum air temperature (Earth proxy for persistent cold).
ICE = "ice_proxy"
ALL_FEATURES = [*GRID_FEATURES, ICE]
GRID_OF = {ICE: "temp_min_coldest_c"}

# Relative weights per preset. The ice proxy is reported as its own sub-score and
# is only mixed into the overall score by the cold-trap preset.
PRESETS: dict[str, dict[str, float]] = {
    "balanced": {"relief_20km_m": 1, "slope_20km_deg": 1, "roughness_5km_m": 1 / 3, "roughness_10km_m": 1 / 3,
                 "roughness_20km_m": 1 / 3, "hurst_2_32km": 0.5, "precip_annual_mm": 0.5,
                 "precip_driest_month_mm": 0.5},
    "rover_mobility": {"slope_20km_deg": 3, "relief_20km_m": 1, "roughness_5km_m": 2 / 3,
                       "roughness_10km_m": 2 / 3, "roughness_20km_m": 2 / 3, "hurst_2_32km": 0.5},
    "cold_trap_ice": {ICE: 3, "relief_20km_m": 0.5, "slope_20km_deg": 0.5, "precip_annual_mm": 0.5,
                      "precip_driest_month_mm": 0.5},
    # Needs diurnal/annual range and minimum, which the Diviner polar table does not provide:
    # stays unavailable until those target values exist.
    "thermal_cycling": {"temp_diurnal_range_c": 2, "temp_annual_range_c": 1, "temp_min_coldest_c": 1},
    # Annual mean and annual maximum temperature. Moon values are Diviner SURFACE temperatures,
    # Earth values are WorldClim AIR temperatures; the Moon sits beyond Earth's cold end, so this
    # preset ranks Earth cells by coldness only.
    "thermal_surface": {"temp_mean_c": 1, "temp_max_warmest_c": 1},
}
# Target status -> weight multiplier (resolution-limited values must not drive the ranking).
STATUS_FACTOR = {"measured": 1.0, "reduced_lags": 0.5, "resolution_limited": 0.0}


# ------------------------------------------------------------ percentiles

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


def load_earth(path=None) -> tuple[dict[str, np.ndarray], dict[str, Ecdf], np.ndarray, np.ndarray]:
    """Return per-feature Earth percentile grids (float16, NaN off land), ECDFs, lat, lon."""
    with Dataset(path or PROCESSED_DIR / "earth_features.nc") as ds:
        lat, lon = np.asarray(ds["lat"][:]), np.asarray(ds["lon"][:])
        w = np.broadcast_to(np.cos(np.radians(lat))[:, None], (lat.size, lon.size))
        grids, ecdfs = {}, {}
        for name in GRID_FEATURES:
            a = np.ma.filled(ds[name][:], np.nan).astype("float32")
            ok = np.isfinite(a)
            ecdfs[name] = Ecdf(a[ok], w[ok])
            pct = np.full(a.shape, np.nan, dtype="float16")
            pct[ok] = ecdfs[name].percentile(a[ok])
            grids[name] = pct
    grids[ICE] = grids["temp_min_coldest_c"]
    ecdfs[ICE] = ecdfs["temp_min_coldest_c"]
    return grids, ecdfs, lat, lon


# ------------------------------------------------------------ targets

def target_percentiles(profile: dict, ecdfs: dict[str, Ecdf]) -> tuple[dict[str, float], dict[str, str], dict[str, float]]:
    """Target percentile per feature, dropped-feature reasons, and per-feature status factors."""
    pct, dropped, factor = {}, {}, {}
    for name, f in profile["features"].items():
        if f["value"] is None:
            dropped[name] = f["status"]
        elif f["status"] == "one_sided_constraint":
            pct[name], factor[name] = 0.0, 1.0  # drier than any Earth desert
        else:
            pct[name] = float(ecdfs[name].percentile(f["value"]))
            factor[name] = STATUS_FACTOR.get(f["status"], 1.0)
    ice = profile.get("ice_cold_trap_proxy", {})
    if ice.get("status") == "measured":
        # Lunar PSRs stay below 110 K (-163 C) all year, colder than any Earth land cell
        # (grid minimum about -72 C), so the target sits beyond Earth's cold end.
        pct[ICE], factor[ICE] = 0.0, 1.0
    else:
        dropped[ICE] = ice.get("status", "missing")
    return pct, dropped, factor


def score_map(grids: dict[str, np.ndarray], target_pct: dict[str, float], weights: dict[str, float],
              factor: dict[str, float] | None = None) -> tuple[np.ndarray, dict[str, np.ndarray], list[str]]:
    """Overall score (0-100, NaN off land), per-feature sub-scores, and the features used."""
    factor = factor or {}
    used = {k: w * factor.get(k, 1.0) for k, w in weights.items() if k in target_pct and w * factor.get(k, 1.0) > 0}
    shape = next(iter(grids.values())).shape
    dist, total = np.zeros(shape, dtype="float32"), 0.0
    subs = {}
    for k in ALL_FEATURES:
        if k not in target_pct:
            continue
        d = np.abs(grids[k].astype("float32") - target_pct[k]) / 100
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
