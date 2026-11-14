"""Mathematical similarity engine for matching Earth grid cells to Mars target profiles.

Calculates:
1. Per-feature sub-scores (0-100%) using Gaussian/exponential decay over defined tolerances.
2. Composite weighted similarity score (0-100%).
3. Feature breakdown: matches, mismatches, and domain divergence.
4. Masking for biophysically non-analogous cells (vegetation, saturated moisture).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class EarthCell:
    """Measurable physical parameters of an Earth geographic cell (e.g. 0.05 deg grid)."""
    location_name: str
    latitude: float
    longitude: float
    vegetation_ndvi: float
    slope_deg: float
    surface_roughness_m: float
    lst_mean_k: float
    lst_diurnal_range_k: float
    soil_moisture_fraction: float
    country: Optional[str] = None
    geological_context: Optional[str] = None


@dataclass
class SimilarityResult:
    """Detailed breakdown of Earth-Mars analog similarity."""
    target_id: str
    location_name: str
    latitude: float
    longitude: float
    overall_score: float  # 0 to 100
    is_masked_out: bool   # True if vegetated or water body
    mask_reason: Optional[str]
    feature_subscores: Dict[str, float]  # Feature -> Score (0-100)
    top_matching_features: List[Tuple[str, float]]
    top_deviating_features: List[Tuple[str, float]]
    exploration_recommendation: str
    irreducible_limits: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "location_name": self.location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "overall_score": round(self.overall_score, 2),
            "is_masked_out": self.is_masked_out,
            "mask_reason": self.mask_reason,
            "feature_subscores": {k: round(v, 2) for k, v in self.feature_subscores.items()},
            "top_matching_features": [(k, round(v, 2)) for k, v in self.top_matching_features],
            "top_deviating_features": [(k, round(v, 2)) for k, v in self.top_deviating_features],
            "exploration_recommendation": self.exploration_recommendation,
            "irreducible_limits": self.irreducible_limits,
        }


def calculate_feature_subscore(
    earth_val: float,
    target_val: float,
    tolerance_sigma: float,
) -> float:
    """Compute Gaussian similarity sub-score in range [0, 100].

    Score = 100 * exp(-0.5 * ((earth_val - target_val) / tolerance_sigma)^2)
    """
    if tolerance_sigma <= 0:
        return 100.0 if earth_val == target_val else 0.0
    delta = earth_val - target_val
    normalized_diff = delta / tolerance_sigma
    score = 100.0 * math.exp(-0.5 * (normalized_diff ** 2))
    return max(0.0, min(100.0, score))


def score_location_against_target(
    earth_cell: EarthCell,
    target_profile: Any,  # MarsTargetProfile or dict
    custom_weights: Optional[Dict[str, float]] = None,
) -> SimilarityResult:
    """Calculate similarity between an Earth location and the Mars target profile."""
    if hasattr(target_profile, "to_dict"):
        target_dict = target_profile.to_dict()
    else:
        target_dict = target_profile

    target_id = target_dict["target_id"]
    target_vector = target_dict["tier1_global_vector"]
    tolerances = target_dict["tier1_tolerances"]
    weights = custom_weights or target_dict["tier1_feature_weights"]
    limits = target_dict.get("irreducible_limits", {})

    # Check strict exclusion filters:
    # 1. Vegetation filter: NDVI > 0.15 is definitively vegetated and non-analogous
    if earth_cell.vegetation_ndvi > 0.15:
        return SimilarityResult(
            target_id=target_id,
            location_name=earth_cell.location_name,
            latitude=earth_cell.latitude,
            longitude=earth_cell.longitude,
            overall_score=0.0,
            is_masked_out=True,
            mask_reason=f"Vegetation detected (NDVI = {earth_cell.vegetation_ndvi:.2f} > 0.15)",
            feature_subscores={},
            top_matching_features=[],
            top_deviating_features=[("vegetation_ndvi", 0.0)],
            exploration_recommendation="Unsuitable: Surface dominated by vascular biology.",
            irreducible_limits=limits,
        )

    # 2. Open water / liquid saturation filter:
    if earth_cell.soil_moisture_fraction > 0.35:
        return SimilarityResult(
            target_id=target_id,
            location_name=earth_cell.location_name,
            latitude=earth_cell.latitude,
            longitude=earth_cell.longitude,
            overall_score=0.0,
            is_masked_out=True,
            mask_reason=f"Water saturation / wetland (Moisture = {earth_cell.soil_moisture_fraction:.2f} > 0.35)",
            feature_subscores={},
            top_matching_features=[],
            top_deviating_features=[("soil_moisture_fraction", 0.0)],
            exploration_recommendation="Unsuitable: Liquid water saturation exceeds planetary boundary.",
            irreducible_limits=limits,
        )

    # Compute per-feature subscores
    subscores: Dict[str, float] = {}
    earth_values = {
        "vegetation_ndvi": max(0.0, earth_cell.vegetation_ndvi),
        "slope_deg": earth_cell.slope_deg,
        "surface_roughness_m": earth_cell.surface_roughness_m,
        "lst_mean_k": earth_cell.lst_mean_k,
        "lst_diurnal_range_k": earth_cell.lst_diurnal_range_k,
        "soil_moisture_fraction": earth_cell.soil_moisture_fraction,
    }

    total_weight = 0.0
    weighted_sum = 0.0

    for feat_name, t_val in target_vector.items():
        e_val = earth_values.get(feat_name, 0.0)
        tol = tolerances.get(feat_name, 1.0)
        w = weights.get(feat_name, 1.0)

        sub = calculate_feature_subscore(e_val, t_val, tol)
        subscores[feat_name] = sub

        weighted_sum += sub * w
        total_weight += w

    overall = weighted_sum / total_weight if total_weight > 0 else 0.0

    # Sort matching vs deviating
    sorted_feats = sorted(subscores.items(), key=lambda x: x[1], reverse=True)
    top_matches = sorted_feats[:3]
    top_deviations = sorted_feats[-2:]

    # Exploration recommendation synthesis
    if overall >= 75.0:
        rec = "High-fidelity analog: Suitable for joint instrument calibration and rover locomotion tests."
    elif subscores.get("slope_deg", 0) > 80 and subscores.get("surface_roughness_m", 0) > 80:
        rec = "Geomorphic/Terrain analog: Excellent for rover mobility, suspension, and obstacle negotiation."
    elif subscores.get("lst_diurnal_range_k", 0) > 80 and subscores.get("lst_mean_k", 0) > 70:
        rec = "Thermal/Environmental analog: Ideal for thermal fatigue testing and payload battery life cycles."
    else:
        rec = "Partial analog: Specialized for specific isolated environmental testing."

    return SimilarityResult(
        target_id=target_id,
        location_name=earth_cell.location_name,
        latitude=earth_cell.latitude,
        longitude=earth_cell.longitude,
        overall_score=overall,
        is_masked_out=False,
        mask_reason=None,
        feature_subscores=subscores,
        top_matching_features=top_matches,
        top_deviating_features=top_deviations,
        exploration_recommendation=rec,
        irreducible_limits=limits,
    )
