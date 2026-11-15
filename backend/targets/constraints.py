"""Physical constraints: target values that are bounds, not measurements.

The Moon and Mars have no rainfall and no vegetation, so their target
precipitation is 0 mm. That value is a physical bound rather than a sampled
distribution, so the band around it is *declared* in config and every entry
built here is labelled ``declared_tolerance``. The similarity engine then scores
it with exactly the same rank and absolute maths as any measured target feature.

Nothing here invents a number: the target value, the tolerance band, the label
and the per-body reason all come from ``config/config.yaml`` and
``config/targets.yaml``.
"""

from __future__ import annotations

from typing import Any

from backend.config import AppConfig, PhysicalConstraint


def physical_constraint(
    config: AppConfig, name: str
) -> PhysicalConstraint:
    """Look up one declared physical constraint or fail loudly."""
    for constraint in config.physical_constraints:
        if constraint.name == name:
            return constraint
    raise KeyError(f"no physical constraint named {name!r} in config/config.yaml")


def dryness_constraint_entries(
    config: AppConfig, target: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Target-vector entries for the no-precipitation constraint.

    Returns an empty mapping when the body disables the constraint, so a target
    that genuinely has a precipitation record can opt out in config.
    """
    body = target.get("dryness_constraint") or {}
    if not body.get("enabled"):
        return {}
    constraint = physical_constraint(config, "dryness")
    reason = str(body.get("reason", "")).strip()
    definitions = {definition.id: definition for definition in config.all_features}
    entries: dict[str, dict[str, Any]] = {}
    for feature in constraint.features:
        definition = definitions[feature.id]
        note = (
            f"{constraint.label}: target value "
            f"{constraint.target_value:g} {definition.units}; the band "
            f"{feature.p16:g}-{feature.p84:g} {definition.units} is declared in "
            "config as a tolerance, not measured"
        )
        if reason:
            note = f"{note}. {reason}"
        entries[feature.id] = {
            "units": definition.units,
            "long_name": definition.long_name,
            "group": definition.group,
            "registry_function": definition.function,
            "params": dict(definition.params),
            "resolution": "constraint",
            "distribution": "declared_tolerance",
            "resolution_note": note,
            "n_cells": 0,
            "median": float(constraint.target_value),
            "p16": float(feature.p16),
            "p84": float(feature.p84),
            "spread": float(feature.p84 - feature.p16),
            "min": float(constraint.target_value),
            "max": float(feature.p84),
            "mean": float((feature.p16 + feature.p84) / 2.0),
            "sampled": False,
            "physical_constraint": True,
            "constraint_label": constraint.label,
        }
    return entries
