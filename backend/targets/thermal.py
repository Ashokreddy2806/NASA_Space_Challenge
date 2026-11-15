"""Moon and Mars thermal values, read from the hand-made, cited CSVs.

The project rule is strict: Moon and Mars temperatures and thermal inertia come
only from the literature tables the team authored. No value is estimated,
interpolated or guessed here. If a table is missing, the affected features are
reported as **unavailable with the exact path that is missing** — the pipeline
never substitutes a number.

Expected schema (long format, one row per quantity)::

    body,feature,statistic,value,units,source,notes
    moon,temp_mean_k,median,215,K,"Williams et al. 2017 (Diviner)","..."
    moon,temp_diurnal_range_k,median,280,K,"Vasavada et al. 2012","..."

Required columns: ``feature`` and ``value``. Optional: ``body``, ``statistic``
(default ``median``), ``units``, ``source``, ``notes``, ``min``, ``max``,
``n_cells``. A feature may appear several times with different statistics.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from backend.config import AppConfig


def thermal_path(config: AppConfig, body: str) -> Path:
    """Configured path of a body's hand-made thermal table."""
    key = config.targets[body].get("thermal_csv", "thermal")
    try:
        filename = config.sources[body][key]
    except KeyError as exc:
        raise KeyError(f"no configured thermal file for {body}.{key}") from exc
    from backend.paths import RAW

    return RAW[body] / str(filename)


def load_thermal_table(path: Path) -> dict[str, dict[str, Any]]:
    """Read a thermal table into ``{feature: {statistic: value, ...}}``."""
    if not path.exists():
        raise FileNotFoundError(path)

    table: dict[str, dict[str, Any]] = {}
    sources: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "feature" not in reader.fieldnames:
            raise ValueError(f"{path} must have a 'feature' column; got {reader.fieldnames}")
        if "value" not in reader.fieldnames:
            raise ValueError(f"{path} must have a 'value' column; got {reader.fieldnames}")
        for row in reader:
            feature = str(row["feature"]).strip()
            if not feature:
                continue
            statistic = str(row.get("statistic") or "median").strip()
            entry = table.setdefault(
                feature,
                {
                    "units": str(row.get("units") or "").strip(),
                    "values": {},
                    "notes": str(row.get("notes") or "").strip(),
                },
            )
            entry["values"][statistic] = float(row["value"])
            for optional in ("min", "max", "n_cells"):
                raw = row.get(optional)
                if raw not in (None, ""):
                    entry["values"][optional] = float(raw)
            source = str(row.get("source") or "").strip()
            if source and source not in sources:
                sources.append(source)
    for entry in table.values():
        entry["source"] = "; ".join(sources)
        entry["values"].setdefault("n", entry["values"].get("n_cells"))
    return table


def thermal_availability(config: AppConfig, body: str) -> dict[str, Any]:
    """Describe whether the body's thermal table exists, without inventing values."""
    path = thermal_path(config, body)
    if not path.exists():
        return {
            "available": False,
            "path": str(path),
            "reason": (
                f"cited thermal table {path} is not on disk; Moon/Mars temperatures and "
                "thermal inertia are not estimated"
            ),
            "table": {},
        }
    table = load_thermal_table(path)
    return {"available": True, "path": str(path), "reason": "", "table": table}


def _kelvin_to_celsius(value: float, units: str) -> tuple[float, float | None]:
    """Convert a Kelvin literature value to degrees Celsius (exact offset)."""
    if units.strip().lower() in {"k", "kelvin", "kelvins"}:
        return value - 273.15, -273.15
    return value, None


def match_thermal_features(
    config: AppConfig,
    availability: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Map configured thermal features onto the cited literature table.

    A feature is only populated when the table has a row for it. Otherwise the
    entry is ``unavailable`` with the exact reason (missing table or missing
    row); no number is ever invented. Kelvin values are converted to the
    configured unit with an explicit, recorded offset.
    """
    groups = set(target.get("thermal_groups", []))
    members = [
        member
        for group in config.groups
        if group.name in groups
        for member in group.members
    ]
    definitions = {definition.id: definition for definition in config.all_features}
    table = availability.get("table", {})
    out: dict[str, dict[str, Any]] = {}

    for feature_id in members:
        definition = definitions.get(feature_id)
        if definition is None:
            continue
        if not availability["available"]:
            out[feature_id] = {
                "units": definition.units,
                "long_name": definition.long_name,
                "group": definition.group,
                "resolution": "unavailable",
                "resolution_note": availability["reason"],
                "n_cells": 0,
                "median": float("nan"),
            }
            continue

        candidates = [
            feature_id,
            feature_id.replace("_c", "_k"),
            feature_id.removesuffix("_c"),
        ]
        row = next((table[name] for name in candidates if name in table), None)
        if row is None:
            out[feature_id] = {
                "units": definition.units,
                "long_name": definition.long_name,
                "group": definition.group,
                "resolution": "unavailable",
                "resolution_note": (
                    f"no row for {feature_id} in the cited thermal table "
                    f"{availability['path']}"
                ),
                "n_cells": 0,
                "median": float("nan"),
            }
            continue

        values = row["values"]
        units = str(row.get("units") or definition.units)
        offset = None
        converted = {}
        for key, value in values.items():
            if isinstance(value, (int, float)):
                converted[key], step = _kelvin_to_celsius(float(value), units)
                offset = step if step is not None else offset
            else:
                converted[key] = value
        if offset is not None:
            units = definition.units

        median = converted.get("median")
        minimum = converted.get("min")
        maximum = converted.get("max")
        p16 = converted.get("p16")
        p84 = converted.get("p84")
        spread = (
            p84 - p16
            if p16 is not None and p84 is not None
            else (maximum - minimum if minimum is not None and maximum is not None else float("nan"))
        )
        out[feature_id] = {
            "units": units,
            "long_name": definition.long_name,
            "group": definition.group,
            "registry_function": "cited_literature",
            "resolution": "literature",
            "resolution_note": "",
            "median": median if median is not None else float("nan"),
            "min": minimum if minimum is not None else float("nan"),
            "max": maximum if maximum is not None else float("nan"),
            "spread": spread,
            "n_cells": int(converted.get("n_cells") or converted.get("n") or 0),
            "sampled": False,
            "source": row.get("source", ""),
            "notes": row.get("notes", ""),
            "conversion": (
                "K -> degC (subtract 273.15)" if offset is not None else None
            ),
            "table": availability["path"],
        }
    return out
