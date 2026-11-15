"""Phase 2: measure the lunar south-pole and Jezero targets with the Earth estimators.

Writes ``data/processed/target_profiles.json`` (copied to ``docs/target_profiles.json``)
and plots of each target against the Earth feature distributions.

Run from ``NASA_Space_Challenge/`` (needs ``earth_features.nc`` from Phase 1)::

    python -m backend.pipeline.target_profiles

Targets (defaults recorded in PLAN.md Decisions):
  * Moon: poleward of 85 S, i.e. a disk of radius 2R*tan(2.5 deg) = 151.7 km in the
    Moon 2015 south polar stereographic grid. Reprojected, never read as lon/lat.
  * Mars: Jezero Crater (18.38 N, 77.58 E), 50 km radius disk.

Terrain features use ``earth_terrain.compute_terrain_features`` on a 2 km grid, so
every estimator is identical to the Earth one. Temperatures come only from the
cited literature CSVs; no site-specific value exists there yet, so they stay null.
"""

from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from netCDF4 import Dataset
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from rasterio.warp import reproject
from rasterio.windows import Window

from backend.paths import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR, RAW, ensure_output_dirs
from backend.pipeline.earth_terrain import compute_terrain_features, hurst_exponent

PIXEL_M = 2000.0
HALO_KM = 40.0  # covers the 32 km Hurst window and the 20 km filters
MOON_R_M = 1_737_400.0
MARS_R_M = 3_396_190.0
MOON_LAT_LIMIT = -85.0
MOON_RADIUS_M = 2 * MOON_R_M * np.tan(np.radians((90 + MOON_LAT_LIMIT) / 2))
JEZERO = (18.38, 77.58)
MARS_RADIUS_M = 50_000.0
TERRAIN = [
    "relief_20km_m", "slope_20km_deg", "roughness_5km_m", "roughness_10km_m",
    "roughness_20km_m", "hurst_2_32km",
]
TEMPERATURE = [
    "temp_mean_c", "temp_diurnal_range_c", "temp_max_warmest_c",
    "temp_min_coldest_c", "temp_annual_range_c",
]
DRYNESS = ["precip_annual_mm", "precip_driest_month_mm"]


# ---------------------------------------------------------------- Moon

def moon_dem_2km() -> np.ndarray:
    """Area-average the 80 m polar DEM to 2 km over the 85S disk plus a halo."""
    half = MOON_RADIUS_M + HALO_KM * 1000
    n = int(2 * np.ceil(half / PIXEL_M))  # cells across, even so the pole is on a corner
    half = n * PIXEL_M / 2
    with rasterio.open(RAW["moon"] / "LDEM_80S_80MPP_ADJ.tiff") as src:
        res = src.res[0]
        col0 = int(round((-half - src.bounds.left) / res))
        row0 = int(round((src.bounds.top - half) / res))
        side = int(round(2 * half / res))
        return src.read(
            1, window=Window(col0, row0, side, side), out_shape=(n, n),
            resampling=Resampling.average,
        ).astype("float32")


def disk_mask(n: int, radius_m: float) -> np.ndarray:
    """Cells of an n x n 2 km grid centred on the grid middle within radius_m."""
    c = (np.arange(n) + 0.5 - n / 2) * PIXEL_M
    return np.hypot(*np.meshgrid(c, c)) <= radius_m


def moon_published(mask_fn) -> dict[str, dict]:
    """Medians of the published 1 km LDRM products over the same disk (cross-check)."""
    out = {}
    for tag, name in [("rough_800m_m", "ROUGH_800M"), ("rough_1600m_m", "ROUGH_1600M"),
                      ("slope_800m_deg", "SLP_800M"), ("slope_1600m_deg", "SLP_1600M"),
                      ("hurst_published", "H")]:
        with rasterio.open(RAW["moon"] / f"LDRM_80S_1000MPP_ADJ_{name}.tiff") as src:
            a = src.read(1)
            x = src.bounds.left + (np.arange(a.shape[1]) + 0.5) * src.res[0]
            y = src.bounds.top - (np.arange(a.shape[0]) + 0.5) * src.res[1]
            m = np.hypot(*np.meshgrid(x, y)) <= mask_fn
            out[tag] = summarize(a[m & np.isfinite(a)])
    return out


def psr_fraction() -> dict:
    """Fraction of the 85S disk covered by mapped PSRs (>= 1 km2 polygons)."""
    csv.field_size_limit(10**9)
    shapes, area, count = [], 0.0, 0
    with open(RAW["moon"] / "LPSR_80S_20MPP_ADJ_1km2.csv", newline="") as f:
        for row in csv.DictReader(f):
            polys = []
            for poly in re.findall(r"\(\((.*?)\)\)", row["WKT"], flags=re.S):
                rings = [[tuple(map(float, p.split()[:2])) for p in ring.strip("() ").split(",")]
                         for ring in re.split(r"\)\s*,\s*\(", poly)]
                polys.append({"type": "Polygon", "coordinates": rings})
            shapes += [(g, 1) for g in polys]
    res = 100.0
    n = int(2 * MOON_RADIUS_M / res)
    t = from_origin(-MOON_RADIUS_M, MOON_RADIUS_M, res, res)
    covered = rasterize(shapes, out_shape=(n, n), transform=t, fill=0, dtype="uint8").astype(bool)
    c = (np.arange(n) + 0.5 - n / 2) * res
    inside = np.hypot(*np.meshgrid(c, c)) <= MOON_RADIUS_M
    return {
        "psr_area_fraction": float((covered & inside).sum() / inside.sum()),
        "psr_area_km2": float((covered & inside).sum() * res**2 / 1e6),
        "region_area_km2": float(inside.sum() * res**2 / 1e6),
    }


# ---------------------------------------------------------------- Mars

def mars_dem_2km() -> np.ndarray:
    """Reproject MOLA 16 ppd around Jezero onto a local 2 km equidistant grid."""
    lat, lon = JEZERO
    n = int(2 * np.ceil((MARS_RADIUS_M + HALO_KM * 1000) / PIXEL_M))
    mola = np.memmap(RAW["mars"] / "megt90n000eb.img", dtype=">i2", mode="r", shape=(2880, 5760))
    r0, c0 = int((90 - lat - 4) * 16), int((lon - 5) * 16)
    win = mola[r0:r0 + 128, c0:c0 + 160].astype("float32")
    dst = np.full((n, n), np.nan, dtype="float32")
    half = n * PIXEL_M / 2
    reproject(
        win, dst,
        src_transform=from_origin(c0 / 16, 90 - r0 / 16, 1 / 16, 1 / 16),
        src_crs=CRS.from_proj4(f"+proj=longlat +R={MARS_R_M} +no_defs"),
        dst_transform=from_origin(-half, half, PIXEL_M, PIXEL_M),
        dst_crs=CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +R={MARS_R_M} +units=m +no_defs"),
        resampling=Resampling.bilinear,
    )
    return dst


# ------------------------------------------------------- shared helpers

def summarize(values: np.ndarray) -> dict:
    p10, p50, p90 = np.percentile(values, [10, 50, 90])
    return {"value": float(p50), "p10": float(p10), "p90": float(p90), "n_cells": int(values.size)}


def terrain_summary(dem: np.ndarray, radius_m: float, hurst_lags=None) -> dict:
    feats = compute_terrain_features(dem, PIXEL_M)
    if hurst_lags:
        feats["hurst_2_32km"] = hurst_exponent(dem, PIXEL_M, lags_km=hurst_lags)
    m = disk_mask(dem.shape[0], radius_m)
    return {k: summarize(feats[k][m & np.isfinite(feats[k])]) for k in TERRAIN}


def read_reference(path) -> dict:
    """Literature reference values (never site-specific numbers)."""
    with open(path, newline="") as f:
        return {r["feature"]: {"value": float(r["value"]), "units": r["units"], "source": r["source"]}
                for r in csv.DictReader(f)}


def earth_scale() -> dict:
    """Area-weighted Earth land distribution per feature (sorted values + cumulative weight)."""
    out = {}
    with Dataset(PROCESSED_DIR / "earth_features.nc") as ds:
        w = np.cos(np.radians(ds["lat"][:]))[:, None] * np.ones((1, ds["lon"].size))
        for k in TERRAIN + DRYNESS + TEMPERATURE:
            a = np.ma.filled(ds[k][:], np.nan)
            ok = np.isfinite(a)
            order = np.argsort(a[ok])
            vals, cw = a[ok][order], np.cumsum(w[ok][order])
            out[k] = (vals, cw / cw[-1])
    return out


def earth_context(scale, key, value) -> dict:
    vals, cw = scale[key]
    pct = float(np.interp(value, vals, cw) * 100)
    q = lambda p: float(vals[np.searchsorted(cw, p / 100)])
    return {"earth_percentile": round(pct, 2), "beyond_earth_range": bool(value < vals[0] or value > vals[-1]),
            "earth_min": float(vals[0]), "earth_p5": q(5), "earth_median": q(50),
            "earth_p95": q(95), "earth_max": float(vals[-1])}


# ------------------------------------------------------------ profiles

def build_profile(meta, terrain, scale, notes, extra) -> dict:
    features = {}
    for k in TERRAIN:
        features[k] = {**terrain[k], "units": TERRAIN_UNITS[k], **earth_context(scale, k, terrain[k]["value"]),
                       **notes.get(k, {"status": "measured"})}
    for k in TEMPERATURE:
        features[k] = {"value": None, "status": "missing_site_specific_literature_value", "units": "degC",
                       "limitation": "No site-specific cited value yet; reference values below are equatorial/global "
                                     "and must not be used as the target."}
    for k in DRYNESS:
        features[k] = {"value": 0.0, "units": "mm", "status": "one_sided_constraint",
                       "limitation": meta["dryness_note"], **earth_context(scale, k, 0.0)}
    return {**{k: meta[k] for k in ("name", "body", "region", "method", "resolution_note")},
            "features": features, **extra}


TERRAIN_UNITS = {"relief_20km_m": "m", "slope_20km_deg": "degrees", "roughness_5km_m": "m",
                 "roughness_10km_m": "m", "roughness_20km_m": "m", "hurst_2_32km": "unitless"}


def plot_target(name, color, profile, scale, path):
    keys = TERRAIN + DRYNESS[:1]
    fig, axes = plt.subplots(2, 4, figsize=(15, 6.5))
    for ax, k in zip(axes.flat, keys):
        vals, cw = scale[k]
        sample = vals[np.searchsorted(cw, np.random.default_rng(0).random(60000))]
        ax.hist(sample if k != "precip_annual_mm" else np.log10(sample + 1), bins=60, color="#b8bec6")
        f = profile["features"][k]
        v = f["value"] if k != "precip_annual_mm" else np.log10(f["value"] + 1)
        ax.axvline(v, color=color, lw=2.5)
        if "p10" in f:
            lo, hi = (f["p10"], f["p90"])
            ax.axvspan(lo, hi, color=color, alpha=0.2)
        ax.set_title(k + (" (log10 +1)" if k == "precip_annual_mm" else ""), fontsize=10)
        pct = f["earth_percentile"]
        ax.text(0.97, 0.9, "beyond Earth range" if f["beyond_earth_range"] else f"Earth pct {pct:.0f}",
                transform=ax.transAxes, ha="right", fontsize=9, color=color)
        ax.set_yticks([])
    axes.flat[-1].axis("off")
    fig.suptitle(f"{name}: target vs Earth land distribution (area-weighted)", fontsize=13)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    ensure_output_dirs()
    scale = earth_scale()

    dem = moon_dem_2km()
    moon_terrain = terrain_summary(dem, MOON_RADIUS_M)
    moon_extra = {
        "ice_cold_trap_proxy": {**psr_fraction(), "status": "measured",
            "limitation": "PSR table lists shadowed areas > 1 km2 only (lower bound); CRS assumed equal to the DEM "
                          "grid. Earth has no PSR analogue; its proxy temp_min_coldest_c is a different quantity."},
        "published_cross_check": moon_published(MOON_RADIUS_M),
        "thermal_reference_values": read_reference(RAW["moon"] / "moon_thermal_literature.csv"),
    }
    moon = build_profile(
        {"name": "Lunar south pole (poleward of 85S)", "body": "Moon",
         "region": f"disk of radius {MOON_RADIUS_M / 1000:.1f} km around the pole in the Moon 2015 polar stereographic grid",
         "method": "LOLA LDEM_80S_80MPP_ADJ area-averaged to a 2 km grid; Earth estimators applied; median and "
                   "p10-p90 over the disk",
         "resolution_note": "80 m source, 2 km working grid, windows 5-32 km",
         "dryness_note": "Airless body: no precipitation by definition. Treated as 'drier than any Earth desert', "
                         "not a measured value."},
        moon_terrain, scale, {}, moon_extra)

    mars_terrain = terrain_summary(mars_dem_2km(), MARS_RADIUS_M, hurst_lags=(8, 16, 32))
    mars_notes = {
        "roughness_5km_m": {"status": "resolution_limited", "limitation": "5 km window is about 1.4 MOLA pixels "
                            "(3.7 km); value is not comparable with Earth's 1.85 km source and is an underestimate."},
        "hurst_2_32km": {"status": "reduced_lags", "limitation": "Lags 2 and 4 km are below MOLA resolution; fitted over "
                         "8/16/32 km only, so the exponent is indicative."},
    }
    for k in ("relief_20km_m", "slope_20km_deg", "roughness_10km_m", "roughness_20km_m"):
        mars_notes[k] = {"status": "measured", "limitation": "3.7 km MOLA pixels bilinearly resampled to 2 km smooth "
                         "fine-scale terrain, biasing slope and roughness low."}
    mars = build_profile(
        {"name": "Jezero Crater, Mars", "body": "Mars",
         "region": f"disk of radius {MARS_RADIUS_M / 1000:.0f} km around {JEZERO[0]}N {JEZERO[1]}E",
         "method": "MOLA MEGDR 16 ppd reprojected (bilinear) to a 2 km azimuthal equidistant grid on R=3396.19 km; "
                   "Earth estimators applied; median and p10-p90 over the disk",
         "resolution_note": "3.7 km source, 2 km working grid: sub-pixel detail is not resolved",
         "dryness_note": "Hyper-arid: no liquid precipitation. Treated as a one-sided constraint, not a measured value."},
        mars_terrain, scale, mars_notes,
        {"thermal_reference_values": read_reference(RAW["mars"] / "mars_thermal_literature.csv"),
         "ice_cold_trap_proxy": {"status": "not_in_mvp", "limitation": "No mapped cold-trap product downloaded for Mars."}})

    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
           "earth_reference": "area-weighted Earth land cells of data/processed/earth_features.nc",
           "earth_limits": "Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment.",
           "targets": {"moon_south_pole": moon, "mars_jezero": mars}}
    path = PROCESSED_DIR / "target_profiles.json"
    path.write_text(json.dumps(out, indent=2))
    shutil.copy(path, DOCS_DIR / "target_profiles.json")
    plot_target("Lunar south pole", "#2b6cb0", moon, scale, FIGURES_DIR / "target_moon_vs_earth.png")
    plot_target("Jezero Crater", "#c05621", mars, scale, FIGURES_DIR / "target_mars_vs_earth.png")
    for key, p in out["targets"].items():
        print(key)
        for k in TERRAIN:
            f = p["features"][k]
            print(f"  {k:20s} {f['value']:10.3f} [{f['p10']:.3f}..{f['p90']:.3f}] earth pct "
                  f"{f['earth_percentile']:.1f} {'BEYOND' if f['beyond_earth_range'] else ''}")


if __name__ == "__main__":
    main()
