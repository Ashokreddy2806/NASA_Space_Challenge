"""Similarity scoring engine for planetary analog matching."""

from .similarity import (
    calculate_feature_subscore,
    score_location_against_target,
    EarthCell,
    SimilarityResult,
)

__all__ = [
    "calculate_feature_subscore",
    "score_location_against_target",
    "EarthCell",
    "SimilarityResult",
]
