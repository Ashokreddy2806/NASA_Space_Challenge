"""Tests for percentile normalization module."""

import unittest

from scientific_engine.src.similarity.normalization import PercentileNormalizer


class TestNormalization(unittest.TestCase):
    def setUp(self):
        self.normalizer = PercentileNormalizer()

    def test_median_maps_to_50th_percentile(self):
        # Earth median slope from docs/earth_grid_report.md is 0.33
        p = self.normalizer.transform("slope_20km_deg", 0.33)
        self.assertIsNotNone(p)
        self.assertAlmostEqual(p, 0.50, delta=0.05)

    def test_outlier_clipping(self):
        # Negative slope should clip to 0.0
        p_low = self.normalizer.transform("slope_20km_deg", -5.0)
        self.assertEqual(p_low, 0.0)

        # Huge slope should clip to 1.0
        p_high = self.normalizer.transform("slope_20km_deg", 50.0)
        self.assertEqual(p_high, 1.0)

    def test_missing_data_returns_none(self):
        self.assertIsNone(self.normalizer.transform("slope_20km_deg", None))
        self.assertIsNone(self.normalizer.transform("slope_20km_deg", float("nan")))
        self.assertIsNone(self.normalizer.transform("unknown_feature", 10.0))

    def test_monotonic_ordering(self):
        vals = [0.0, 50.0, 78.7, 500.0, 3000.0]
        percentiles = [self.normalizer.transform("relief_20km_m", v) for v in vals]
        for i in range(len(percentiles) - 1):
            self.assertLessEqual(percentiles[i], percentiles[i + 1])


if __name__ == "__main__":
    unittest.main()
