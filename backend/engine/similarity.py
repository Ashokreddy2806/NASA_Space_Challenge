"""Phase 3 similarity engine: rank similarity *and* absolute gap, per feature.

Both halves are mandatory (Phase 2 contract):

* **absolute** — ``exp(-0.5 * (gap / scale)^2)`` with ``gap = Earth value -
  target median`` and ``scale`` floored by config, so the score is in real units;
* **rank** — ``1 - |p_earth - q|`` where ``p_earth`` is the Earth cell's
  area-weighted percentile and ``q`` is the Earth percentile of the target
  median. Rank similarity is scale-free, so it can look excellent while the
  real-unit gap is enormous; the engine flags exactly that case and never hides
  the gap.

Qualitative thermal features never use a numeric Earth/target comparison: they
are scored by distance between configured bands (band 0 = coldest), with the
target band derived from exact cited polar rows in the target profile.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Iterable

import numpy as np
from netCDF4 import Dataset

from backend.config import AppConfig, FeatureDefinition


@dataclass(frozen=True)
class ScaledFeature:
    """One target feature with the scale/bands the engine needs."""

    id: str
    group: str
    units: str
    qualitative: bool
    median: float = float("nan")
    sigma: float = float("nan")
    floor: float = float("nan")
    scale: float = float("nan")
    floor_rule: str = ""
    bands_c: tuple[float, ...] = ()
    n_bands: int = 0
    target_band: int = -1
    anchor_lo: float = float("nan")
    anchor_hi: float = float("nan")
    anchor_label: str = ""
    anchor_rows: tuple[str, ...] = ()
    label: str = ""
    physical_constraint: bool = False
    declared_distribution: bool = False


def scaled_features(
    config: AppConfig, profile: dict[str, Any]
) -> dict[str, ScaledFeature]:
    """Resolve every usable target feature into an absolute/rank scale."""
    scoring = config.scoring
    out: dict[str, ScaledFeature] = {}
    for definition in config.all_features:
        entry = (profile.get("features") or {}).get(definition.id)
        if not entry:
            continue
        resolution = entry.get("resolution")
        if resolution == "qualitative":
            out[definition.id] = ScaledFeature(
                id=definition.id,
                group=definition.group,
                units=definition.units,
                qualitative=True,
                bands_c=tuple(float(v) for v in entry["bands_c"]),
                n_bands=int(entry["n_bands"]),
                target_band=int(entry["target_band"]),
                anchor_lo=float(entry["anchor_range_c"][0]),
                anchor_hi=float(entry["anchor_range_c"][1]),
                anchor_label=str(entry.get("anchor_label", "")),
                anchor_rows=tuple(entry.get("anchor_rows", ())),
                label="qualitative",
            )
            continue
        if resolution not in {"resolved", "marginal", "constraint"}:
            continue
        median = entry.get("median")
        p16 = entry.get("p16")
        p84 = entry.get("p84")
        if median is None or not math.isfinite(float(median)):
            continue
        median = float(median)
        if p16 is not None and p84 is not None:
            sigma = (float(p84) - float(p16)) / 2.0
        else:
            sigma = float("nan")
        absolute_floor = float(scoring.spread_floor_units.get(definition.id, 0.0))
        fraction_floor = abs(median) * scoring.spread_floor_fraction
        floor = max(absolute_floor, fraction_floor)
        if not math.isfinite(sigma):
            sigma = floor
        scale = max(sigma, floor)
        out[definition.id] = ScaledFeature(
            id=definition.id,
            group=definition.group,
            units=definition.units,
            qualitative=False,
            median=median,
            sigma=sigma,
            floor=floor,
            scale=scale,
            floor_rule=(
                f"max(|median| * {scoring.spread_floor_fraction:g} = "
                f"{fraction_floor:.4g}, measurement floor {absolute_floor:.4g})"
            ),
            physical_constraint=resolution == "constraint",
            declared_distribution=entry.get("distribution") == "declared_tolerance",
        )
    return out


class EarthStore:
    """Read-only access to the Phase 1 Earth feature NetCDF."""

    def __init__(self, config: AppConfig) -> None:
        self.path = config.output("earth_features")
        self.dataset = Dataset(str(self.path), "r")
        self.lat = np.asarray(self.dataset.variables["lat"][:], dtype=np.float64)
        self.lon = np.asarray(self.dataset.variables["lon"][:], dtype=np.float64)
        self.land = np.asarray(self.dataset.variables["land_mask"][:]) > 0
        weight = np.cos(np.radians(self.lat))[:, None] * self.land
        self.cell_weight = np.asarray(weight, dtype=np.float32)
        self.weight_sum = float(self.cell_weight.sum(dtype=np.float64))

    @property
    def shape(self) -> tuple[int, int]:
        return (self.lat.size, self.lon.size)

    def read(self, feature_id: str) -> np.ndarray:
        if feature_id not in self.dataset.variables:
            raise KeyError(f"{feature_id} is not in {self.path}")
        return np.asarray(self.dataset.variables[feature_id][:], dtype=np.float32)

    def window(
        self, feature_id: str, lat_deg: float, lon_deg: float, radius_deg: float
    ) -> np.ndarray:
        """Small area slice around a point (lat/lon are cell centres)."""
        rows = self._indices(self.lat, lat_deg, radius_deg)
        cols = self._indices(self.lon, lon_deg, radius_deg)
        return np.asarray(
            self.dataset.variables[feature_id][rows, cols], dtype=np.float32
        )

    @staticmethod
    def _indices(axis: np.ndarray, centre: float, radius: float) -> slice:
        step = float(abs(axis[1] - axis[0]))
        half = max(1, int(round(radius / step)))
        index = int(np.argmin(np.abs(axis - centre)))
        start = max(0, index - half)
        stop = min(axis.size, index + half + 1)
        return slice(start, stop)

    def close(self) -> None:
        self.dataset.close()


def weighted_cdf_table(
    values: np.ndarray, weights: np.ndarray, quantiles: int
) -> tuple[np.ndarray, np.ndarray]:
    """Area-weighted empirical CDF as ``(probabilities, value quantiles)``.

    ``values`` and ``weights`` are 1-D and already selected to valid cells.
    Duplicate values are fine: the quantile table is monotone and the lookup is
    linear interpolation, so the error is at most one quantile step.
    """
    order = np.argsort(values, kind="stable")
    sorted_values = values[order]
    cumulative = np.cumsum(weights[order].astype(np.float64))
    cumulative /= cumulative[-1]
    probabilities = np.linspace(0.0, 1.0, int(quantiles), dtype=np.float64)
    quantile_values = np.interp(probabilities, cumulative, sorted_values)
    return probabilities, quantile_values.astype(np.float32)


def percentile_of(values: np.ndarray, table: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Earth percentile of each value (area-weighted, from the stored table)."""
    probabilities, quantile_values = table
    return np.interp(values, quantile_values, probabilities).astype(np.float32)


def band_similarity(values: np.ndarray, feature: ScaledFeature) -> np.ndarray:
    """Band distance similarity; exact band agreement = 1."""
    bands = np.asarray(feature.bands_c, dtype=np.float64)
    band = np.searchsorted(bands, values, side="right")
    distance = np.abs(band - feature.target_band)
    scale = max(feature.n_bands - 1, 1)
    return (1.0 - distance / scale).astype(np.float32)


def qualitative_gap(values: np.ndarray, feature: ScaledFeature) -> np.ndarray:
    """Signed distance to the cited anchor range (0 inside the range)."""
    gap = np.zeros_like(values, dtype=np.float32)
    below = values < feature.anchor_lo
    above = values > feature.anchor_hi
    gap[below] = values[below] - feature.anchor_lo
    gap[above] = values[above] - feature.anchor_hi
    return gap


def absolute_similarity(
    values: np.ndarray, feature: ScaledFeature, kernel: str
) -> np.ndarray:
    """Gaussian (default) likeness in real units, using the floored scale."""
    if feature.qualitative:
        return band_similarity(values, feature)
    gap = (values - feature.median) / feature.scale
    if kernel == "gaussian":
        return np.exp(-0.5 * gap * gap).astype(np.float32)
    if kernel == "exponential":
        return np.exp(-np.abs(gap)).astype(np.float32)
    raise ValueError(f"unknown absolute_similarity kernel {kernel!r}")


def hidden_gap_mask(
    config: AppConfig,
    rank_similarity: np.ndarray,
    absolute_like: np.ndarray,
) -> np.ndarray:
    """Cells where a good rank match hides a large real-unit gap.

    The flag is evidence for the reader only; it never changes a score.
    """
    return (rank_similarity >= config.scoring.hidden_gap_rank_similarity) & (
        absolute_like <= config.scoring.hidden_gap_absolute_similarity
    )


@dataclass
class FeatureDiagnostics:
    """Per-feature, per-target evidence for the report and the JSON."""

    feature_id: str
    group: str
    units: str
    qualitative: bool
    target_median: float
    scale: float
    sigma: float
    floor: float
    floor_rule: str
    earth_percentile_of_median: float = float("nan")
    mean_absolute_similarity: float = float("nan")
    mean_rank_similarity: float = float("nan")
    hidden_gap_area_fraction: float = 0.0
    band_area_fractions: list[float] = field(default_factory=list)
    target_band: int = -1
    anchor_range_c: tuple[float, float] = (float("nan"), float("nan"))
    anchor_label: str = ""
    physical_constraint: bool = False
    declared_distribution: bool = False

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "group": self.group,
            "units": self.units,
            "qualitative": self.qualitative,
            "target_median": _finite(self.target_median),
            "scale": _finite(self.scale),
            "sigma": _finite(self.sigma),
            "floor": _finite(self.floor),
            "floor_rule": self.floor_rule,
            "mean_absolute_similarity": _finite(self.mean_absolute_similarity),
            "mean_rank_similarity": _finite(self.mean_rank_similarity),
            "hidden_gap_area_fraction": self.hidden_gap_area_fraction,
            "physical_constraint": self.physical_constraint,
            "declared_distribution": self.declared_distribution,
        }
        if self.qualitative:
            payload.update(
                {
                    "target_band": self.target_band,
                    "band_area_fractions": self.band_area_fractions,
                    "anchor_range_c": list(self.anchor_range_c),
                    "anchor_label": self.anchor_label,
                    "earth_percentile_of_median": None,
                }
            )
        else:
            payload["earth_percentile_of_median"] = _finite(
                self.earth_percentile_of_median
            )
        return payload


def _finite(value: float) -> float | None:
    return float(value) if isinstance(value, (int, float)) and math.isfinite(value) else None


@dataclass
class GroupAccumulator:
    total: np.ndarray
    count: np.ndarray

    @classmethod
    def create(cls, shape: tuple[int, int]) -> "GroupAccumulator":
        return cls(
            total=np.zeros(shape, dtype=np.float32),
            count=np.zeros(shape, dtype=np.uint8),
        )

    def add(self, similarity: np.ndarray, valid: np.ndarray) -> None:
        self.total[valid] += similarity[valid]
        self.count[valid] += 1

    def grid(self) -> np.ndarray:
        out = np.full(self.total.shape, np.nan, dtype=np.float32)
        has = self.count > 0
        out[has] = self.total[has] / self.count[has]
        return out


def compute_group_scores(
    config: AppConfig,
    profiles: dict[str, dict[str, Any]],
    store: EarthStore,
    targets: Iterable[str] = ("moon", "mars"),
) -> tuple[
    dict[str, dict[str, np.ndarray]],
    dict[str, dict[str, FeatureDiagnostics]],
    dict[str, dict[str, tuple[np.ndarray, np.ndarray]]],
]:
    """Area-weighted group scores plus per-feature diagnostics and CDF tables."""
    targets = tuple(targets)
    scales = {target: scaled_features(config, profiles[target]) for target in targets}
    groups: dict[str, dict[str, GroupAccumulator]] = {t: {} for t in targets}
    diagnostics: dict[str, dict[str, FeatureDiagnostics]] = {t: {} for t in targets}
    tables: dict[str, dict[str, tuple[np.ndarray, np.ndarray]]] = {
        t: {} for t in targets
    }
    scoring = config.scoring
    land = store.land

    for definition in config.all_features:
        used = [t for t in targets if definition.id in scales[t]]
        if not used:
            continue
        values = store.read(definition.id)
        valid = land & np.isfinite(values)
        if not valid.any():
            continue
        probabilities, quantile_values = weighted_cdf_table(
            values[valid], store.cell_weight[valid], scoring.cdf_quantiles
        )
        table = (probabilities, quantile_values)
        for target in used:
            feature = scales[target][definition.id]
            if feature.qualitative:
                similarity = band_similarity(values, feature)
                diag = FeatureDiagnostics(
                    feature_id=definition.id,
                    group=feature.group,
                    units=feature.units,
                    qualitative=True,
                    target_median=float("nan"),
                    scale=float("nan"),
                    sigma=float("nan"),
                    floor=float("nan"),
                    floor_rule="banded qualitative anchor",
                    target_band=feature.target_band,
                    anchor_range_c=(feature.anchor_lo, feature.anchor_hi),
                    anchor_label=feature.anchor_label,
                )
                band = np.searchsorted(
                    np.asarray(feature.bands_c), values, side="right"
                )
                weights = store.cell_weight[valid]
                diag.band_area_fractions = [
                    float((weights[band[valid] == index]).sum() / weights.sum())
                    for index in range(feature.n_bands)
                ]
                diag.mean_absolute_similarity = float(
                    (similarity[valid] * weights).sum() / weights.sum()
                )
                diag.mean_rank_similarity = diag.mean_absolute_similarity
            else:
                similarity = absolute_similarity(
                    values, feature, scoring.absolute_kernel
                )
                percentiles = percentile_of(values, table)
                q = float(np.interp(feature.median, quantile_values, probabilities))
                rank_similarity = 1.0 - np.abs(percentiles - q)
                hidden = hidden_gap_mask(config, rank_similarity, similarity)
                weights = store.cell_weight[valid]
                diag = FeatureDiagnostics(
                    feature_id=definition.id,
                    group=feature.group,
                    units=feature.units,
                    qualitative=False,
                    target_median=feature.median,
                    scale=feature.scale,
                    sigma=feature.sigma,
                    floor=feature.floor,
                    floor_rule=feature.floor_rule,
                    earth_percentile_of_median=q,
                    physical_constraint=feature.physical_constraint,
                    declared_distribution=feature.declared_distribution,
                    mean_absolute_similarity=float(
                        (similarity[valid] * weights).sum() / weights.sum()
                    ),
                    mean_rank_similarity=float(
                        (rank_similarity[valid] * weights).sum() / weights.sum()
                    ),
                    hidden_gap_area_fraction=float(
                        (hidden[valid] * weights).sum() / weights.sum()
                    ),
                )
            diagnostics[target][definition.id] = diag
            tables[target][definition.id] = table
            accumulator = groups[target].setdefault(
                feature.group, GroupAccumulator.create(store.shape)
            )
            accumulator.add(similarity, valid)

    scored = {
        target: {group: acc.grid() for group, acc in groups[target].items()}
        for target in targets
    }
    return scored, diagnostics, tables


def preset_score(
    config: AppConfig,
    target: str,
    groups: dict[str, np.ndarray],
    weights: dict[str, float],
) -> tuple[np.ndarray, dict[str, Any]]:
    """Weighted mean over available groups, with config-driven renormalisation."""
    usable = {
        name: weight
        for name, weight in weights.items()
        if weight > 0 and name in groups
    }
    if not usable:
        raise ValueError(f"preset has no usable group for target {target}")
    denominator = float(sum(usable.values()))
    numerator = np.zeros(next(iter(groups.values())).shape, dtype=np.float32)
    valid = np.ones(numerator.shape, dtype=bool)
    for name, weight in usable.items():
        numerator += (weight / denominator) * groups[name]
        valid &= np.isfinite(groups[name])
    score = np.full(numerator.shape, np.nan, dtype=np.float32)
    score[valid] = numerator[valid]
    dropped = sorted(set(weights) - set(usable))
    return score, {
        "weights_used": usable,
        "weights_dropped": {name: weights[name] for name in dropped},
        "weight_sum": denominator,
    }


def score_coverage(
    config: AppConfig,
    score: np.ndarray,
    store: EarthStore,
) -> float:
    """Area fraction of Earth land that has a finite score."""
    weights = store.cell_weight[store.land]
    return float(
        (np.isfinite(score[store.land]) * weights).sum() / store.weight_sum
    )
