"""Distribution summaries for target features.

A target profile is a distribution, never a single number: median, a robust
spread (p16–p84, i.e. ±1σ for a normal distribution), min/max and the number of
cells that actually contributed.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from backend.features.registry import Availability


def summarise(
    values: np.ndarray, *, sampled: bool, percentiles: tuple[float, float]
) -> dict[str, Any]:
    """Summarise a 1-D array of feature values."""
    finite = np.asarray(values, dtype="float64")
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {
            "n": 0,
            "median": float("nan"),
            "p16": float("nan"),
            "p84": float("nan"),
            "spread": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "mean": float("nan"),
            "sampled": sampled,
        }
    p16, median, p84 = np.percentile(finite, [percentiles[0], 50.0, percentiles[1]])
    return {
        "n": int(finite.size),
        "median": float(median),
        "p16": float(p16),
        "p84": float(p84),
        "spread": float(p84 - p16),
        "min": float(finite.min()),
        "max": float(finite.max()),
        "mean": float(finite.mean()),
        "sampled": sampled,
    }


def profile_entry(
    definition,
    values: np.ndarray,
    verdict: Availability,
    *,
    n_cells: int,
    sampled: bool,
    percentiles: tuple[float, float],
) -> dict[str, Any]:
    """One feature's distribution plus how its window was resolved."""
    summary = summarise(values, sampled=sampled, percentiles=percentiles)
    return {
        "units": definition.units,
        "long_name": definition.long_name,
        "group": definition.group,
        "registry_function": definition.function,
        "params": dict(definition.params),
        "resolution": verdict.resolution,
        "resolution_note": verdict.reason,
        "window_span_px": verdict.detail.get("window_span_px"),
        "n_cells": int(n_cells),
        **summary,
    }
