"""Similarity scoring module.

Converts distances into intuitive similarity scores [0, 100]%,
providing per-feature subscores, data quality metrics, and exploration suitability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

from scientific_engine.src.similarity.distance import calculate_feature_distance, calculate_weighted_distance
from scientific_engine.src.similarity.normalization import PercentileNormalizer
from scientific_engine.src.similarity.weights import WeightManager


@dataclass
class SimilarityScoreResult:
    target_id: str
    preset_name: str
    overall_score: float  # 0 to 100%
    data_quality: float   # 0 to 100%
    feature_subscores: Dict[str, float]  # feature -> 0 to 100%
    feature_percentiles_earth: Dict[str, float]
    feature_percentiles_target: Dict[str, float]
    top_matching_features: List[Tuple[str, float]]
    top_deviating_features: List[Tuple[str, float]]
    missing_features: List[str]
    exploration_suitability: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_id": self.target_id,
            "preset_name": self.preset_name,
            "overall_score": round(self.overall_score, 2),
            "data_quality": round(self.data_quality * 100.0, 1),
            "feature_subscores": {k: round(v, 1) for k, v in self.feature_subscores.items()},
            "top_matching_features": [(k, round(v, 1)) for k, v in self.top_matching_features],
            "top_deviating_features": [(k, round(v, 1)) for k, v in self.top_deviating_features],
            "missing_features": self.missing_features,
            "exploration_suitability": self.exploration_suitability,
        }


class SimilarityScorer:
    """Computes similarity scores between Earth cells and planetary target profiles."""

    def __init__(self, normalizer: Optional[PercentileNormalizer] = None, weight_manager: Optional[WeightManager] = None):
        self.normalizer = normalizer or PercentileNormalizer()
        self.weight_manager = weight_manager or WeightManager()

    def score_cell(
        self,
        earth_values: Dict[str, Any],
        target_profile: Dict[str, Any],
        preset_name: str = "balanced_default",
        custom_weights: Optional[Dict[str, float]] = None,
    ) -> SimilarityScoreResult:
        """Compute comprehensive similarity score for a single Earth cell."""
        target_id = target_profile.get("target_id", "unknown")
        target_features = target_profile.get("features", {})

        # 1. Obtain weights
        if custom_weights:
            weights = custom_weights
        else:
            weights = self.weight_manager.get_preset_weights(preset_name)

        # 2. Compute percentile ranks and feature-level distances
        distances: Dict[str, float] = {}
        subscores: Dict[str, float] = {}
        earth_p_map: Dict[str, float] = {}
        target_p_map: Dict[str, float] = {}
        missing_feats: List[str] = []

        for feat, w in weights.items():
            if w <= 0.0:
                continue

            e_val = earth_values.get(feat)
            t_obj = target_features.get(feat, {})
            t_val = t_obj.get("value") if isinstance(t_obj, dict) else t_obj

            is_dryness = "precip" in feat

            e_p = self.normalizer.transform(feat, e_val)
            t_p = self.normalizer.transform(feat, t_val)

            if e_p is not None:
                earth_p_map[feat] = e_p
            if t_p is not None:
                target_p_map[feat] = t_p

            dist = calculate_feature_distance(e_p, t_p, is_one_sided_lower_better=is_dryness)
            if dist is not None:
                distances[feat] = dist
                subscores[feat] = (1.0 - dist) * 100.0
            else:
                missing_feats.append(feat)

        # 3. Compute weighted composite distance and data quality
        comp_dist, quality = calculate_weighted_distance(distances, weights)
        overall_score = max(0.0, min(100.0, (1.0 - comp_dist) * 100.0))

        # 4. Sort top matches vs deviations
        sorted_subs = sorted(subscores.items(), key=lambda x: x[1], reverse=True)
        top_matches = sorted_subs[:3]
        top_deviations = sorted_subs[-2:] if len(sorted_subs) >= 2 else sorted_subs

        # 5. Determine exploration suitability
        suitability = self._synthesize_suitability(preset_name, overall_score, subscores)

        return SimilarityScoreResult(
            target_id=target_id,
            preset_name=preset_name,
            overall_score=overall_score,
            data_quality=quality,
            feature_subscores=subscores,
            feature_percentiles_earth=earth_p_map,
            feature_percentiles_target=target_p_map,
            top_matching_features=top_matches,
            top_deviating_features=top_deviations,
            missing_features=missing_feats,
            exploration_suitability=suitability,
        )

    def _synthesize_suitability(self, preset: str, overall: float, subscores: Dict[str, float]) -> str:
        if overall >= 75.0:
            return "High-fidelity analog: Recommended for primary end-to-end mission and rover trials."
        if preset == "rover_mobility":
            slope_s = subscores.get("slope_20km_deg", 0)
            rough_s = subscores.get("roughness_10km_m", 0)
            if slope_s > 80 and rough_s > 80:
                return "Strong terrain/mobility analog: Recommended for suspension, grousers, and obstacle negotiation."
            return "Moderate terrain analog: Useful for baseline locomotion and grade climbing."
        elif preset == "cold_trap_ice":
            temp_s = subscores.get("temp_min_coldest_c", 0)
            if temp_s > 80:
                return "Cryogenic/cold-trap analog: Recommended for volatile stability and thermal insulation tests."
            return "Partial cold analog: Sub-zero conditions suitable for cold-start mechanisms."
        elif preset == "thermal_cycling":
            diurn_s = subscores.get("temp_diurnal_range_c", 0)
            if diurn_s > 80:
                return "Thermal stress analog: Recommended for battery duty-cycle and thermal fatigue verification."
            return "Moderate thermal swing: Suitable for day-night payload monitoring."
        return "General environmental analog: Useful for subsystem-level procedures."
