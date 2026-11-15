"""Distance calculation module.

Computes feature-level and weighted composite distances in normalized percentile space.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple


def calculate_feature_distance(
    earth_p: Optional[float],
    target_p: Optional[float],
    is_one_sided_lower_better: bool = False,
) -> Optional[float]:
    """Calculate distance between Earth and Target in percentile space [0, 1].

    - Two-sided: distance = |earth_p - target_p| in [0, 1]
    - One-sided (e.g. dryness): distance = earth_p (penalizing higher precipitation)
    - If either value is None: returns None (missing feature)
    """
    if earth_p is None or target_p is None:
        return None

    if is_one_sided_lower_better:
        # Lower is better; target is at 0th percentile
        return max(0.0, min(1.0, earth_p))

    return max(0.0, min(1.0, abs(earth_p - target_p)))


def calculate_weighted_distance(
    distances: Dict[str, float],
    weights: Dict[str, float],
) -> Tuple[float, float]:
    """Compute weighted composite distance and data quality score.

    Returns:
    - composite_distance in [0, 1]
    - data_quality in [0, 1] (fraction of active preset weight successfully evaluated)
    """
    total_active_weight = sum(weights.values())
    if total_active_weight <= 0.0:
        return 1.0, 0.0

    eval_weight = 0.0
    accum_dist = 0.0

    for feat, w in weights.items():
        if w <= 0.0:
            continue
        if feat in distances and distances[feat] is not None:
            accum_dist += distances[feat] * w
            eval_weight += w

    if eval_weight <= 0.0:
        return 1.0, 0.0

    composite_dist = accum_dist / eval_weight
    quality = eval_weight / total_active_weight

    return composite_dist, quality
