"""Shared feature registry and per-body feature execution."""

from backend.features.registry import (
    FUNCTIONS,
    Availability,
    attributes,
    availability,
    compute,
    compute_all,
    prepare_dem,
)

__all__ = [
    "FUNCTIONS",
    "Availability",
    "attributes",
    "availability",
    "compute",
    "compute_all",
    "prepare_dem",
]
