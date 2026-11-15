"""Moon and Mars thermal values, read from the hand-made, cited CSVs.

The project rule is strict: Moon and Mars temperatures and thermal inertia come
only from the literature tables the team authored. No value is estimated,
interpolated or guessed here. If a table is missing, the affected features are
reported as **unavailable with the exact path that is missing** — the pipeline
never substitutes a number.

Two schemas are accepted, and which one a file uses is detected from its header:

**Long format** — one row per statistic of a named feature::

    body,feature,statistic,value,units,source,notes
    moon,temp_mean_k,median,215,K,"Williams et al. 2017 (Diviner)","..."

**Flat reference format** — one row per cited quantity, no statistic column::

    feature,value,units,source
    moon_night_surface_temp_typical,100,K,"Paige et al. 2010 ..."

The flat format is what the team's tables use. It records *reference numbers*
(bracketing extremes, thresholds), not per-cell feature maps, so it is exposed
as ``references`` and never silently turned into a target distribution. Bracketing
``*_min``/``*_max`` rows may be combined into a derived range; every derived value
is labelled with the rule and the two cited inputs it came from.

Required columns: ``feature`` and ``value``. Optional: ``body``, ``statistic``,
``units``, ``source``, ``notes``, ``min``, ``max``, ``n_cells``.
"""

from __future__ import annotations

import bisect
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


def load_reference_table(path: Path) -> list[dict[str, Any]]:
    """Read a flat ``feature,value,units,source`` table into ordered rows.

    Each row is one cited quantity. Nothing is combined or interpreted here;
    ``derive_reference_ranges`` does the (explicitly labelled) arithmetic.
    """
    if not path.exists():
        raise FileNotFoundError(path)

    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "feature" not in reader.fieldnames:
            raise ValueError(f"{path} must have a 'feature' column; got {reader.fieldnames}")
        if "value" not in reader.fieldnames:
            raise ValueError(f"{path} must have a 'value' column; got {reader.fieldnames}")
        for order, row in enumerate(reader):
            name = str(row["feature"]).strip()
            if not name:
                continue
            raw = str(row["value"]).strip()
            if not raw:
                continue
            units = str(row.get("units") or "").strip()
            value = float(raw)
            entry: dict[str, Any] = {
                "name": name,
                "value": value,
                "units": units,
                "source": str(row.get("source") or "").strip(),
                "notes": str(row.get("notes") or "").strip(),
                "order": order,
            }
            converted, offset = _kelvin_to_celsius(value, units)
            if offset is not None:
                entry["value_degc"] = converted
                entry["conversion"] = "K -> degC (subtract 273.15)"
            rows.append(entry)
    return rows


def derive_reference_ranges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine bracketing ``*_min``/``*_max`` rows into labelled ranges.

    Only exact stems are paired, so ``foo_min`` needs ``foo_max``. The result
    records the rule and both cited inputs; it is arithmetic on cited numbers,
    never an estimate.
    """
    by_name = {row["name"]: row for row in rows}
    derived: list[dict[str, Any]] = []
    for row in rows:
        name = row["name"]
        if not name.endswith("_min"):
            continue
        stem = name[: -len("_min")]
        other = by_name.get(f"{stem}_max")
        if other is None:
            continue
        if row["units"] != other["units"]:
            continue
        low, high = row["value"], other["value"]
        if high < low:
            low, high = high, low
        entry: dict[str, Any] = {
            "name": stem,
            "kind": "derived_range",
            "units": row["units"],
            "min": low,
            "max": high,
            "width": high - low,
            "rule": f"{stem}_max - {stem}_min of the two cited rows",
            "inputs": [f"{stem}_min", f"{stem}_max"],
            "sources": [source for source in (row["source"], other["source"]) if source],
        }
        converted_low, offset = _kelvin_to_celsius(low, row["units"])
        if offset is not None:
            converted_high, _ = _kelvin_to_celsius(high, row["units"])
            entry.update(
                {
                    "min_degc": converted_low,
                    "max_degc": converted_high,
                    "width_degc": converted_high - converted_low,
                    "conversion": "K -> degC (subtract 273.15)",
                }
            )
        derived.append(entry)
    return derived


def _header_fields(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        return [field.strip() for field in next(reader, [])]


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
            "schema": None,
            "table": {},
            "references": [],
            "derived": [],
        }

    fields = _header_fields(path)
    if "statistic" in fields:
        return {
            "available": True,
            "path": str(path),
            "reason": "",
            "schema": "long",
            "table": load_thermal_table(path),
            "references": [],
            "derived": [],
        }

    references = load_reference_table(path)
    return {
        "available": True,
        "path": str(path),
        "reason": "",
        "schema": "flat_reference",
        "table": {},
        "references": references,
        "derived": derive_reference_ranges(references),
    }


def qualitative_thermal_features(
    config: AppConfig,
    availability: dict[str, Any],
    target: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build banded qualitative entries from the cited polar anchors.

    Approved mapping (2026-11-15, option A): every thermal feature keeps its
    qualitative label, Earth cells are classified into the configured bands, and
    the target band is derived from exact cited rows only. The build fails if the
    cited anchors do not all land in the same band, so a band cannot be invented
    or silently averaged. Equatorial rows are never used here.
    """
    mapping = target.get("thermal_mapping") or {}
    if str(mapping.get("mode", "")) != "banded":
        return {}

    references = {row["name"]: row for row in availability.get("references", [])}
    definitions = {definition.id: definition for definition in config.all_features}
    out: dict[str, dict[str, Any]] = {}

    for feature_id, spec in (mapping.get("features") or {}).items():
        definition = definitions.get(feature_id)
        if definition is None:
            raise KeyError(f"thermal_mapping references unknown feature {feature_id}")
        bands = [float(value) for value in spec["bands_c"]]
        if bands != sorted(bands):
            raise ValueError(f"{feature_id}: bands_c must be ascending")
        if len(set(bands)) != len(bands):
            raise ValueError(f"{feature_id}: bands_c must be distinct")

        values: list[float] = []
        sources: list[str] = []
        for name in spec["anchor_rows"]:
            row = references.get(name)
            if row is None:
                raise KeyError(
                    f"{feature_id} anchor {name} is not in {availability['path']}"
                )
            if "value_degc" not in row:
                raise ValueError(
                    f"{feature_id} anchor {name} has units {row['units']!r}; only "
                    "cited Kelvin temperatures can be banded"
                )
            values.append(float(row["value_degc"]))
            if row.get("source"):
                sources.append(str(row["source"]))

        band_hits = sorted({_band_index(value, bands) for value in values})
        if bool(spec.get("require_single_band", True)) and len(band_hits) != 1:
            raise ValueError(
                f"{feature_id}: cited anchors map to different bands {band_hits} "
                f"with edges {bands}; refusing to invent a target band"
            )

        low, high = min(values), max(values)
        out[feature_id] = {
            "units": definition.units,
            "long_name": definition.long_name,
            "label": definition.label,
            "group": definition.group,
            "registry_function": "cited_literature_banded",
            "resolution": "qualitative",
            "qualitative": True,
            "resolution_note": (
                "qualitative banded anchor: cited polar reference values, not a "
                "per-cell measurement and not numerically comparable to WorldClim"
            ),
            "median": float("nan"),
            "spread": float("nan"),
            "p16": None,
            "p84": None,
            "min": low,
            "max": high,
            "n_cells": 0,
            "sampled": False,
            "bands_c": bands,
            "n_bands": len(bands) + 1,
            "target_band": band_hits[0],
            "anchor_values_c": values,
            "anchor_range_c": [low, high],
            "anchor_label": str(spec.get("anchor_label", "")).strip(),
            "anchor_rows": list(spec["anchor_rows"]),
            "source": "; ".join(dict.fromkeys(sources)),
            "table": availability["path"],
            "scoring": "band_distance",
            "conversion": "K -> degC (subtract 273.15)",
        }
    return out


def apply_thermal_unavailable(
    entries: dict[str, dict[str, Any]], target: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Apply the configured per-feature reasons for features with no polar anchor."""
    mapping = target.get("thermal_mapping") or {}
    reasons = mapping.get("unavailable_features") or {}
    for feature_id, reason in reasons.items():
        entry = entries.get(feature_id)
        if entry is None:
            continue
        entry.update(
            {
                "resolution": "unavailable",
                "resolution_note": str(reason).strip(),
                "median": float("nan"),
                "n_cells": 0,
            }
        )
    return entries


def thermal_context(
    config: AppConfig,
    availability: dict[str, Any],
    target: dict[str, Any],
) -> list[dict[str, Any]]:
    """Cited rows shown on the target card but never used in scoring."""
    mapping = target.get("thermal_mapping") or {}
    context = mapping.get("context_only") or {}
    references = {row["name"]: row for row in availability.get("references", [])}
    rows: list[dict[str, Any]] = []
    for name, label in context.items():
        row = references.get(name)
        if row is None:
            continue
        rows.append(
            {
                "name": name,
                "label": str(label),
                "value": row["value"],
                "units": row["units"],
                "value_degc": row.get("value_degc"),
                "source": row.get("source", ""),
                "scored": False,
            }
        )
    return rows


def _band_index(value: float, bands: list[float]) -> int:
    """Band index for an ascending edge list; band 0 is the cold end."""
    return bisect.bisect_right(bands, value)


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
            if availability.get("references"):
                note = (
                    f"the cited table lists {len(availability['references'])} reference "
                    "quantities, not per-cell rows; no qualitative band mapping is "
                    "defined for this feature"
                )
            else:
                note = (
                    f"no row for {feature_id} in the cited thermal table "
                    f"{availability['path']}"
                )
            out[feature_id] = {
                "units": definition.units,
                "long_name": definition.long_name,
                "group": definition.group,
                "resolution": "unavailable",
                "resolution_note": note,
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
