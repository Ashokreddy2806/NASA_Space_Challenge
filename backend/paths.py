"""Shared filesystem paths for the project.

The team keeps the project (docs, plan, code) in ``NASA_Space_Challenge/`` while
the downloaded raw data lives next to it in ``Datasets/`` (Moon/, Mars/, Earth/).
This module is the single place that knows about that split, so the rest of the
code can refer to logical names such as ``RAW["moon"]``.

Override the data location with the ``NASA_DATA_ROOT`` environment variable if
the datasets are moved (for example on a teammate's laptop).
"""

from __future__ import annotations

import os
from pathlib import Path

# .../NASA_Space_Challenge/backend/paths.py -> .../NASA_Space_Challenge
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# .../NASA_Space_Project
REPO_ROOT = PROJECT_ROOT.parent

# Downloaded source data. Do not copy it into the repo: it is git-ignored.
DATA_ROOT = Path(os.environ.get("NASA_DATA_ROOT", REPO_ROOT / "Datasets")).resolve()

RAW: dict[str, Path] = {
    "moon": DATA_ROOT / "Moon",
    "mars": DATA_ROOT / "Mars",
    "earth": DATA_ROOT / "Earth",
}

PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DOCS_DIR = PROJECT_ROOT / "docs"
FIGURES_DIR = DOCS_DIR / "figures"
BACKEND_DIR = PROJECT_ROOT / "backend"


def ensure_output_dirs() -> None:
    """Create the output directories used by the pipeline if they do not exist."""
    for path in (PROCESSED_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)
