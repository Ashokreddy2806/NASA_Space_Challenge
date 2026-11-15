"""Export every endpoint the globe app calls as static files, for hosting without a Python server.

    python -m backend.api.export_static            # writes deploy/static/

Layout (served from Vercel Blob; the frontend maps API paths to these):
    score-map-info.json, presets.json
    top-sites/<target>_<preset>_<all|nofamous>.json     (n = 8, what the app requests)
    score/<target>_<preset>.png                         (step 5, 0.25 degrees)
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

OUT = Path(__file__).resolve().parents[2] / "deploy" / "static"
TOP_N = 8


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> None:
    c = TestClient(app)
    get = lambda url: c.get(url).raise_for_status().content
    write(OUT / "score-map-info.json", get("/score-map-info"))
    presets = json.loads(get("/presets"))
    write(OUT / "presets.json", json.dumps(presets).encode())
    for target, ps in presets["presets"].items():
        for name, p in ps.items():
            if not p["available"]:
                continue
            for famous, tag in ((False, "all"), (True, "nofamous")):
                write(OUT / f"top-sites/{target}_{name}_{tag}.json",
                      get(f"/targets/{target}/top-sites?preset={name}&exclude_famous={str(famous).lower()}&n={TOP_N}"))
            write(OUT / f"score/{target}_{name}.png", get(f"/targets/{target}/score.png?preset={name}&step=5"))
    files = [p for p in OUT.rglob("*") if p.is_file()]
    print(f"{len(files)} files, {sum(p.stat().st_size for p in files) / 1e6:.1f} MB in {OUT}")


if __name__ == "__main__":
    main()
