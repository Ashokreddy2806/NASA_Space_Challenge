"""Percentile normalization module.

Transforms raw feature values into standardized percentile ranks [0, 1]
using verified global Earth reference distributions (docs/earth_grid_report.md).
Handles outliers, missing data, and directional constraints.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

# Earth reference distributions from docs/earth_grid_report.md (8,712,831 valid land cells)
# Format: (min, p25, median, p75, max, mean, std)
EARTH_REFERENCE_DISTRIBUTIONS: Dict[str, Tuple[float, float, float, float, float, float, float]] = {
    # Terrain features
    "relief_20km_m": (0.0, 32.0, 78.7, 245.0, 4170.0, 185.0, 260.0),
    "slope_20km_deg": (0.0, 0.12, 0.33, 1.15, 18.29, 0.85, 1.25),
    "roughness_5km_m": (0.0, 1.85, 4.438, 11.2, 505.1, 8.5, 14.2),
    "roughness_10km_m": (0.0, 3.42, 8.41, 21.0, 853.0, 16.2, 26.5),
    "roughness_20km_m": (0.0, 5.80, 14.38, 36.5, 1067.0, 28.1, 44.0),
    "hurst_2_32km": (0.0, 0.48, 0.6148, 0.74, 1.5, 0.61, 0.18),

    # Climate / Temperature features
    "temp_mean_c": (-54.75, -8.5, -0.7526, 18.2, 31.06, 2.1, 16.5),
    "temp_diurnal_range_c": (1.0, 6.8, 9.462, 12.3, 21.82, 9.8, 3.8),
    "temp_max_warmest_c": (-29.99, 12.0, 21.59, 29.5, 48.41, 19.5, 13.0),
    "temp_min_coldest_c": (-72.5, -36.5, -22.08, 2.5, 26.3, -16.5, 22.0),
    "temp_annual_range_c": (1.0, 19.5, 33.6, 46.2, 72.57, 33.2, 17.5),

    # Dryness features
    "precip_annual_mm": (0.0, 115.0, 333.3, 850.0, 11230.0, 550.0, 620.0),
    "precip_driest_month_mm": (0.0, 0.5, 4.667, 22.0, 495.2, 15.5, 28.0),

    # Ice / PSR proxy
    "psr_coverage_fraction": (0.0, 0.0, 0.0, 0.05, 1.0, 0.02, 0.08),
}


class PercentileNormalizer:
    """Normalizes raw values to percentile ranks [0, 1] relative to Earth baseline."""

    def __init__(self, reference_dists: Optional[Dict[str, Tuple[float, ...]]] = None):
        self.distributions = reference_dists or EARTH_REFERENCE_DISTRIBUTIONS

    def transform(self, feature_name: str, value: Optional[float]) -> Optional[float]:
        """Convert a feature value to its percentile rank in [0, 1].

        Returns None if value is None, NaN, or feature is unknown.
        """
        if value is None or math.isnan(value) or math.isinf(value):
            return None

        if feature_name not in self.distributions:
            return None

        dist = self.distributions[feature_name]
        min_v, p25_v, med_v, p75_v, max_v, mean_v, std_v = dist

        # Clip extreme outliers outside physical range
        if value <= min_v:
            return 0.0
        if value >= max_v:
            return 1.0

        # Piecewise linear interpolation across known quantiles (0, 0.25, 0.5, 0.75, 1.0)
        if value <= p25_v:
            span = p25_v - min_v
            return 0.25 * ((value - min_v) / span) if span > 0 else 0.125
        elif value <= med_v:
            span = med_v - p25_v
            return 0.25 + 0.25 * ((value - p25_v) / span) if span > 0 else 0.375
        elif value <= p75_v:
            span = p75_v - med_v
            return 0.50 + 0.25 * ((value - med_v) / span) if span > 0 else 0.625
        else:
            span = max_v - p75_v
            return 0.75 + 0.25 * ((value - p75_v) / span) if span > 0 else 0.875

    def get_feature_bounds(self, feature_name: str) -> Optional[Tuple[float, float]]:
        """Return (min, max) for feature."""
        if feature_name in self.distributions:
            d = self.distributions[feature_name]
            return d[0], d[4]
        return None
