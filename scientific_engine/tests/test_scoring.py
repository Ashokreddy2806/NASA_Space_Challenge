"""Tests for similarity scoring engine."""

import unittest

from scientific_engine.src.profiles.mars_profile import build_jezero_profile
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.similarity.scoring import SimilarityScorer


class TestScoring(unittest.TestCase):
    def setUp(self):
        self.scorer = SimilarityScorer()
        self.moon = build_moon_target_profile()
        self.jezero = build_jezero_profile()

    def test_identical_profile_scores_high(self):
        # Earth synthetic cell matching Moon target values
        earth_cell = {
            "relief_20km_m": 3650.0,
            "slope_20km_deg": 9.8,
            "roughness_10km_m": 31.5,
            "hurst_2_32km": 0.70,
            "temp_mean_c": -168.15,
            "temp_diurnal_range_c": 120.0,
            "temp_min_coldest_c": -233.15,
            "precip_annual_mm": 0.0,
        }
        res = self.scorer.score_cell(earth_cell, self.moon, preset_name="balanced_default")
        self.assertGreater(res.overall_score, 90.0)
        self.assertEqual(res.data_quality, 1.0)

    def test_atacama_scores_well_for_mars_dryness_and_thermal(self):
        atacama_cell = {
            "relief_20km_m": 96.0,
            "slope_20km_deg": 0.4,
            "roughness_10km_m": 7.8,
            "hurst_2_32km": 0.58,
            "temp_mean_c": 14.2,
            "temp_diurnal_range_c": 14.8,
            "temp_min_coldest_c": 1.5,
            "precip_annual_mm": 23.3,
        }
        res_mars = self.scorer.score_cell(atacama_cell, self.jezero, preset_name="thermal_cycling")
        self.assertGreater(res_mars.overall_score, 50.0)

    def test_dry_valleys_scores_high_for_moon_terrain(self):
        dry_valleys = {
            "relief_20km_m": 1298.0,
            "slope_20km_deg": 8.6,
            "roughness_5km_m": 22.5,
            "roughness_10km_m": 42.0,
            "roughness_20km_m": 85.0,
            "hurst_2_32km": 0.76,
            "temp_mean_c": -20.8,
            "temp_min_coldest_c": -31.9,
            "precip_annual_mm": 98.6,
        }
        res_moon_mobility = self.scorer.score_cell(dry_valleys, self.moon, preset_name="rover_mobility")
        self.assertGreater(res_moon_mobility.overall_score, 70.0)


if __name__ == "__main__":
    unittest.main()
