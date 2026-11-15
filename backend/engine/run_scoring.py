"""Phase 3 runner: score maps, top sites, validation against known analogs.

Run from ``NASA_Space_Challenge/`` (needs Phase 1 and Phase 2 outputs)::

    python -m backend.engine.run_scoring

Writes ``data/processed/similarity_<target>.nc`` (uint8 scores, 255 = no data),
``docs/top_sites.json``, ``docs/validation.md`` and ``docs/figures/score_*.png``.
"""

from __future__ import annotations

import json
import warnings
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset

from backend.engine.similarity import (
    ALL_FEATURES, ICE, PRESETS, Ecdf, load_earth, score_map, target_percentiles, top_sites,
)
from backend.paths import DOCS_DIR, FIGURES_DIR, PROCESSED_DIR

TARGETS = {"moon_south_pole": "Lunar south pole", "mars_jezero": "Jezero Crater (Mars)"}
# (name, lat, lon, features the site is known for). Sub-score >= 80 on them is the sanity check.
KNOWN = [
    ("Atacama", -23.5, -68.5, ["precip_annual_mm", "precip_driest_month_mm"]),
    ("Dry Valleys", -77.5, 162.0, ["precip_annual_mm", ICE]),
    ("Devon Island / Haughton", 75.4, -89.5, [ICE]),
    ("Death Valley", 36.5, -116.9, ["precip_annual_mm", "relief_20km_m"]),
    ("Iceland", 64.9, -19.0, ["relief_20km_m", "roughness_20km_m"]),
]
PASS = 80.0
CANNOT_REPLICATE = "Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment."


def write_nc(path, lat, lon, layers: dict[str, np.ndarray]) -> None:
    with Dataset(path, "w") as ds:
        ds.createDimension("lat", lat.size)
        ds.createDimension("lon", lon.size)
        ds.createVariable("lat", "f8", ("lat",))[:] = lat
        ds.createVariable("lon", "f8", ("lon",))[:] = lon
        for k, a in layers.items():
            v = ds.createVariable(k, "u1", ("lat", "lon"), zlib=True, complevel=4, fill_value=255,
                                  chunksizes=(360, 720))
            v[:] = np.ma.masked_invalid(np.round(a))
            v.long_name = k + " (0-100, higher = more similar)"


def site_cell(lat, lon, la, lo):
    return int(np.abs(lat - la).argmin()), int(np.abs(lon - lo).argmin())


def describe(sub_at: dict[str, float], notes) -> dict:
    ranked = sorted(sub_at, key=sub_at.get)
    return {"sub_scores": {k: round(v, 1) for k, v in sub_at.items()},
            "best_match": ranked[-3:][::-1], "worst_match": ranked[:3]}


def plot(path, title, panels):
    fig, axes = plt.subplots(1, len(panels), figsize=(8 * len(panels), 4.6))
    axes = np.atleast_1d(axes)
    for ax, (name, s, sites) in zip(axes, panels):
        h, w = s.shape
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            coarse = np.nanmean(s[: h // 5 * 5, : w // 5 * 5].reshape(h // 5, 5, w // 5, 5), axis=(1, 3))
        im = ax.imshow(coarse, extent=(-180, 180, -90, 90), cmap="magma", vmin=40, vmax=100)
        ax.set_facecolor("#dfe3e8")
        for i, p in enumerate(sites, 1):
            ax.plot(p["lon"], p["lat"], "o", ms=5, mfc="#00d1ff", mec="white")
            ax.text(p["lon"] + 3, p["lat"] + 3, str(i), color="white", fontsize=8, weight="bold")
        ax.set_title(name)
        ax.set_xticks([]), ax.set_yticks([])
        fig.colorbar(im, ax=ax, shrink=0.8, label="similarity score")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)


def main() -> None:
    profiles = json.loads((DOCS_DIR / "target_profiles.json").read_text())["targets"]
    grids, ecdfs, lat, lon = load_earth()
    weights_area = np.broadcast_to(np.cos(np.radians(lat))[:, None], grids[ALL_FEATURES[0]].shape)
    results, validation, panels_by_target = {}, {}, {}

    for key, label in TARGETS.items():
        tpct, dropped, factor = target_percentiles(profiles[key], ecdfs)
        layers, tops, used_by_preset = {}, {}, {}
        for preset, w in PRESETS.items():
            s, subs, used = score_map(grids, tpct, w, factor)
            used_by_preset[preset] = used
            if not used:
                tops[preset] = {"status": "unavailable", "reason": "no target value for any feature of this preset"}
                continue
            layers[f"score_{preset}"] = s
            if preset == "balanced":
                base, base_subs = s, subs
            tops[preset] = {
                "features_used": used,
                "top_overall": top_sites(s, lat, lon),
                "top_without_famous_sites": top_sites(s, lat, lon, exclude_famous=True),
            }
            for lst in ("top_overall", "top_without_famous_sites"):
                for p in tops[preset][lst]:
                    p["sub_scores"] = {k: round(float(v[p["row"], p["col"]]), 1) for k, v in subs.items()}
                    p["weakest_matches"] = sorted(p["sub_scores"], key=p["sub_scores"].get)[:3]
                    del p["row"], p["col"]
        layers.update({f"sub_{k}": v for k, v in base_subs.items()})
        write_nc(PROCESSED_DIR / f"similarity_{key}.nc", lat, lon, layers)

        # validation against known analogs (balanced score)
        valid = np.isfinite(base)
        score_ecdf = Ecdf(base[valid], weights_area[valid])
        rows = []
        for name, la, lo, feats in KNOWN:
            r, c = site_cell(lat, lon, la, lo)
            box = base[max(r - 5, 0):r + 6, max(c - 5, 0):c + 6]
            sub_at = {k: float(v[r, c]) for k, v in base_subs.items()}
            checks = {f: (round(sub_at[f], 1), sub_at[f] >= PASS) for f in feats if f in sub_at}
            rows.append({"site": name, "score": round(float(base[r, c]), 1),
                         "score_best_within_0.25deg": round(float(np.nanmax(box)), 1),
                         "rank_percentile": round(float(score_ecdf.percentile(base[r, c])), 1),
                         "expected_feature_checks": checks, **describe(sub_at, None)})
        validation[key] = rows

        panel2 = "rover_mobility" if key == "mars_jezero" else "cold_trap_ice"
        panels_by_target[key] = [("balanced", base, tops["balanced"]["top_overall"]),
                                 (panel2, layers[f"score_{panel2}"], tops[panel2]["top_overall"])]
        results[key] = {"label": label, "target_percentiles": {k: round(v, 1) for k, v in tpct.items()},
                        "dropped_features": dropped, "feature_weight_factors": factor, "presets": tops}
        plot(FIGURES_DIR / f"score_{key}.png", f"{label}: Earth similarity score",
             panels_by_target[key])
        print(key, "balanced top:", [(round(p["lat"], 1), round(p["lon"], 1), round(p["score"], 1))
                                      for p in tops["balanced"]["top_overall"][:5]])

    out = {"generated": datetime.now(timezone.utc).isoformat(timespec="minutes"), "limits": CANNOT_REPLICATE,
           "method": "Earth-percentile weighted L1 distance; see docs/FEATURES.md", "targets": results}
    (DOCS_DIR / "top_sites.json").write_text(json.dumps(out, indent=2))
    write_validation(validation, results)


def write_validation(validation, results) -> None:
    lines = ["# Validation against known analog sites (Phase 3)", "",
             "Balanced preset. *Score* is the 0-100 similarity at the site's grid cell; *rank pct* is its area-weighted "
             "percentile among all Earth land cells. *Checks* test the features each site is famous for (sub-score >= "
             f"{PASS:.0f} counts as a pass). Failures are reported, not hidden.", ""]
    for key, rows in validation.items():
        lines += [f"## {TARGETS[key]}", "",
                  f"Features dropped (no target value): {', '.join(results[key]['dropped_features']) or 'none'}.", "",
                  "| Site | Score | Rank pct | Checks (sub-score) | Best matches | Worst matches |", "|---|---|---|---|---|---|"]
        for r in rows:
            chk = ", ".join(f"{f} {v[0]} {'OK' if v[1] else 'FAIL'}" for f, v in r["expected_feature_checks"].items()) or "n/a"
            lines.append(f"| {r['site']} | {r['score']} | {r['rank_percentile']} | {chk} | "
                         f"{', '.join(r['best_match'])} | {', '.join(r['worst_match'])} |")
        lines.append("")
    lines += ["## Reading this", "",
              "- Percentile distance treats a gap of N percentile points as equal everywhere on the scale. Near the "
              "extremes of a skewed feature (relief, slope, roughness) that compresses large physical differences.",
              "- Temperatures are not scored: no site-specific literature values exist yet.",
              f"- {CANNOT_REPLICATE}", ""]
    (DOCS_DIR / "validation.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
