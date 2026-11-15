import json

import numpy as np
import reverse_geocoder as rg
from netCDF4 import Dataset

from backend.engine.similarity import FAMOUS, ICE, MATCH, PARTIAL, cold_trap_fraction, km_between
from backend.paths import DOCS_DIR, PROCESSED_DIR

EXTRA_PRESET = {"moon_south_pole": "cold_trap_ice", "mars_jezero": "rover_mobility"}
USE = {
    "balanced": "General terrain and dryness analog for instrument tests and crew training.",
    "rover_mobility": "Rover traverse and driving tests on this slope, relief and roughness profile.",
    "cold_trap_ice": "Ice prospecting and cold-trap operations; the Earth frozen-ground fraction stands in for the lunar cold-trap area.",
}
DECIMALS = {"m": 0, "mm": 1, "degrees": 1, "degC": 1, "fraction": 3, "unitless": 2}


def _verdict(sub):
    if sub >= MATCH:
        return "match"
    if sub >= PARTIAL:
        return "partial"
    return "mismatch"


def _fmt(x, unit):
    suffix = "" if unit == "unitless" else f" {unit}"
    return f"{x:,.{DECIMALS[unit]}f}{suffix}"


def _target(profile, name):
    if name == ICE:
        return profile["ice_cold_trap_proxy"]["cold_trap_area_fraction"], "fraction"
    feature = profile["features"][name]
    return feature["value"], feature["units"]


def _earth_value(ds, name, r, c):
    if name == ICE:
        window = np.ma.filled(ds["temp_max_warmest_c"][r - 2:r + 3, c - 2:c + 3].astype("float32"), np.nan)
        return float(cold_trap_fraction(window)[2, 2])
    return float(np.ma.filled(ds[name][r, c], np.nan))


def _famous_check(lat, lon):
    ratio = {n: float(km_between(lat, lon, la, lo)) / r for n, (la, lo, r) in FAMOUS.items()}
    name = min(ratio, key=ratio.get)
    la, lo, radius = FAMOUS[name]
    km = float(km_between(lat, lon, la, lo))
    if ratio[name] <= 1:
        return f"inside the exclusion radius of {name} ({km:,.0f} km, radius {radius} km)"
    return f"outside all exclusion radii (nearest {name}: {km:,.0f} km, radius {radius} km)"


def _failed_analogs(text):
    section, failed = "", []
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:]
        cells = [x.strip() for x in line.split("|")]
        if len(cells) > 4 and cells[4] == "FAIL":
            failed.append(f"{section}: {cells[1]} (rank percentile {cells[3]})")
    return failed


def _target_limit(key, profile):
    if key == "moon_south_pole":
        tmax = profile["features"]["temp_max_warmest_c"]
        ice = profile["ice_cold_trap_proxy"]["cold_trap_area_fraction"]
        return (f"Permanently shadowed regions ({ice:.1%} of the disk, annual maximum below 110 K) have no Earth "
                f"analogue; the lunar warmest-month maximum median is {tmax['value']:.1f} degC, and the coldest Earth "
                f"warmest-month maximum is {tmax['earth_min']:.1f} degC.")
    return f"No Mars temperature, mineral or dust data in this ranking; {profile['resolution_note']}."


def _card(rank, count, site, preset, features, profile, ds, place, limit):
    r = int(np.abs(ds["lat"][:] - site["lat"]).argmin())
    c = int(np.abs(ds["lon"][:] - site["lon"]).argmin())
    sub = site["sub_scores"]
    vals = {}
    for f in features:
        target, unit = _target(profile, f)
        vals[f] = (_earth_value(ds, f, r, c), target, unit)
    rows = [f"| {f} | {_fmt(e, u)} | {_fmt(t, u)} | {sub[f]:.1f} | {_verdict(sub[f])} |"
            for f, (e, t, u) in vals.items()]
    weak = "; ".join(f"{f} Earth {_fmt(vals[f][0], vals[f][2])} vs target {_fmt(vals[f][1], vals[f][2])} "
                     f"(sub-score {sub[f]:.1f})" for f in site["weakest_matches"])
    clear = "" if any(_verdict(sub[f]) == "mismatch" for f in features) else "no feature below 60; weakest of the features used: "
    best = sorted(features, key=lambda f: -sub[f])[:3]
    within = [f for f in site["within_target_band"] if f in features]
    return [
        f"#### {rank}. Nearest named place: {place}",
        f"Lat {site['lat']:.2f}, lon {site['lon']:.2f}. Score {site['score']:.1f} (rank {rank} of {count} in this list). "
        f"Famous-site check: {_famous_check(site['lat'], site['lon'])}.",
        "",
        "| Feature | Earth | Target | Sub-score | Verdict |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "- **Matches:** " + "; ".join(f"{f} ({sub[f]:.1f})" for f in best),
        f"- **Does not match:** {clear}{weak}",
        f"- **Within the target's own spread:** {', '.join(within) or 'none'}",
        f"- **Use for exploration** (guidance, not a finding): {USE[preset]}",
        f"- **Earth cannot replicate:** {limit}",
        "",
    ]


def _target_lines(key, target, profile, ds, limits):
    extra = EXTRA_PRESET[key]
    groups = [("balanced", target["presets"]["balanced"]["top_without_famous_sites"][:5]),
              (extra, target["presets"][extra]["top_overall"][:3])]
    places = iter(rg.search([(s["lat"], s["lon"]) for _, g in groups for s in g], mode=1, verbose=False))
    used = set(target["presets"]["balanced"]["features_used"]) | set(target["presets"][extra]["features_used"])
    notes = {}
    for name, f in {**profile["features"], "ice_cold_trap_proxy": profile["ice_cold_trap_proxy"]}.items():
        if name in used and "limitation" in f:
            notes.setdefault(f["limitation"], []).append(name)
    lines = [f"## {profile['name']}", "",
             f"Target: {profile['region']}. Method: {profile['method']}. Resolution: {profile['resolution_note']}.", "",
             "- Not used (no target value): "
             + ", ".join(f"{k} ({v})" for k, v in target["dropped_features"].items()) + ".",
             *[f"- {', '.join(names)}: {text}" for text, names in notes.items()], ""]
    spread = [s["score"] for s in groups[0][1]]
    lines += [f"Balanced scores without famous sites span {max(spread) - min(spread):.1f} points "
              f"({min(spread):.1f} to {max(spread):.1f}).", ""]
    for preset, group in groups:
        heading = ("balanced preset, without famous sites (top 5)" if preset == "balanced"
                   else f"{preset} preset, all sites (top 3; flagged if inside a famous exclusion radius)")
        lines += [f"### {heading}", ""]
        for rank, site in enumerate(group, 1):
            p = next(places)
            km = float(km_between(site["lat"], site["lon"], float(p["lat"]), float(p["lon"])))
            place = f"{', '.join(x for x in (p['name'], p['admin1'], p['cc']) if x)} ({km:,.0f} km away)"
            lines += _card(rank, len(group), site, preset, target["presets"][preset]["features_used"], profile,
                           ds, place, f"{limits} {_target_limit(key, profile)}")
    return lines


def write_sites() -> None:
    top = json.loads((DOCS_DIR / "top_sites.json").read_text())
    profiles = json.loads((DOCS_DIR / "target_profiles.json").read_text())["targets"]
    validation = (DOCS_DIR / "validation.md").read_text(encoding="utf-8")
    lines = ["# Site write-ups: Earth analogs for the lunar south pole and Jezero Crater", "",
             "Generated from `docs/top_sites.json`, `docs/target_profiles.json`, `docs/validation.md` and "
             "`data/processed/earth_features.nc` by `backend/engine/write_sites.py`.", "",
             "## How to read this", "",
             "- Candidates are Earth 0.05 degree land cells (about 5.6 km north-south). Each list keeps sites at least "
             "300 km apart.",
             "- Score (0-100) = 100 x (1 - D). D is a weighted average of scaled physical distances: each feature is "
             "log1p-transformed (dryness uses log1p(x / reference)) and divided by its Earth P95-P5 span.",
             "- Sub-score = 100 x (1 - distance) per feature. Verdict: match >= 80, partial >= 60, mismatch < 60, as in the API.",
             "- Rank is the position in the list under each site. It is not a probability, and neighbouring scores are close.",
             "- Place names are the nearest GeoNames place with population over 1,000, found offline with the "
             "`reverse_geocoder` package (GeoNames data, CC BY 4.0). They name the nearest settlement, not the site.",
             "- Famous-site check: a site is flagged when it lies inside the exclusion radius of a region in "
             "`backend/engine/similarity.py` (FAMOUS).",
             "", "## What Earth cannot replicate", "",
             f"- {top['limits']} Moon gravity is 1/6 g and Mars gravity is 0.38 g.",
             "- Moon temperatures are Diviner surface (skin) values compared with WorldClim air temperature. This is not "
             "like-for-like.",
             "- Mars has no temperature, mineral or dust data in this ranking.",
             "- Scores within each top list are near-ties (spreads are given under each target), so the order inside a "
             "list is provisional.", ""]
    with Dataset(PROCESSED_DIR / "earth_features.nc") as ds:
        for key, target in top["targets"].items():
            lines += _target_lines(key, target, profiles[key], ds, top["limits"])
    failed = _failed_analogs(validation)
    lines += ["## What this ranking cannot tell you yet", "",
              "- Mars: no site-specific temperature values and no cold-trap product, so the thermal and ice checks "
              "cannot be scored.",
              "- Moon: " + profiles["moon_south_pole"]["features"]["temp_min_coldest_c"]["limitation"]
              + " The minimum and diurnal temperatures are therefore not checked.",
              f"- Each target is one median over a disk (Moon: {profiles['moon_south_pole']['region']}; Mars: "
              f"{profiles['mars_jezero']['region']}). The p10-p90 spread is used only for the within-spread check.",
              "- An Earth cell is about 5.6 km. A single crater, valley or lava tube is smaller than one cell, so the "
              "ranking describes terrain statistics, not a feature.",
              "- Known analogs that fail the rank percentile >= 75 check in `docs/validation.md`: "
              + "; ".join(failed) + ". The ranking does not reproduce these analogs, and the failures are kept here.",
              ""]
    (DOCS_DIR / "site_writeups.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_sites()
