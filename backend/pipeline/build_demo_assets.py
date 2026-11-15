"""Build small, presentation-ready assets for the static Vercel demo.

The deployed map only needs downsampled score images and the top-site evidence
already calculated by the Phase 3 engine. It does not need to ship or open the
full Earth feature and score NetCDF files at request time.

Run from the repository root::

    python -m backend.pipeline.build_demo_assets
"""

from __future__ import annotations

import json
from pathlib import Path

from backend.api.data import render_png, store

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "frontend" / "demo-data"
MAP_INFO = {
    "bounds_west_south_east_north": [-180.0, -90.0, 180.0, 90.0],
    "projection": "EPSG:4326 (equirectangular)",
    "colormap": "magma",
    "scaling": "land area-weighted median -> best site peak score, per target and preset",
    "transparent": "ocean / no data",
}


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")


def build() -> None:
    api = store()
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "presets.json", {
        "groups": ["relief", "slope", "roughness", "scale_robust_roughness", "temperature", "dryness"],
        "presets": {target: api.presets(target) for target in api.targets()},
    })
    write_json(OUT / "score-map-info.json", MAP_INFO)

    for target in api.targets():
        presets = api.top["targets"][target]["presets"]
        for preset, details in presets.items():
            if not details["weighting"]["weights_used"]:
                continue

            image_path = OUT / "scores" / target / f"{preset}.png"
            image_path.parent.mkdir(parents=True, exist_ok=True)
            score = api.score(target, preset, None, step=5)
            lo, hi = api.score_range(target, preset)
            image_path.write_bytes(render_png(score, lo, hi))

            site_path = OUT / "sites" / target / f"{preset}.json"
            write_json(site_path, {
                "target": target,
                "preset": preset,
                "label": details["label"],
                "weights_used": details["weighting"]["weights_used"],
                "weights_dropped": details["weighting"]["weights_dropped"],
                "min_separation_km": details["min_separation_km"],
                "sites": details["sites"][:8],
                "sites_excluding_famous": details["sites_excluding_famous"][:8],
            })

    print(f"Built demo assets in {OUT}")
    print("Upload the contents of this folder to a public Vercel Blob store.")


if __name__ == "__main__":
    build()
