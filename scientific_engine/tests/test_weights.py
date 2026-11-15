"""Tests for weight configurations and dynamic re-weighting."""

import unittest

from scientific_engine.src.similarity.weights import WeightManager


class TestWeights(unittest.TestCase):
    def setUp(self):
        self.wm = WeightManager()

    def test_presets_exist(self):
        names = self.wm.get_preset_names()
        self.assertIn("rover_mobility", names)
        self.assertIn("cold_trap_ice", names)
        self.assertIn("thermal_cycling", names)
        self.assertIn("balanced_default", names)

    def test_rover_mobility_prioritizes_terrain(self):
        w = self.wm.get_preset_weights("rover_mobility")
        norm_w = self.wm.normalize_weights(w)
        self.assertGreater(norm_w.get("slope_20km_deg", 0), 0.20)
        self.assertGreater(norm_w.get("roughness_5km_m", 0), 0.10)
        self.assertEqual(norm_w.get("temp_mean_c", 0), 0.0)

    def test_cold_trap_ice_prioritizes_temperature(self):
        w = self.wm.get_preset_weights("cold_trap_ice")
        norm_w = self.wm.normalize_weights(w)
        self.assertGreater(norm_w.get("temp_min_coldest_c", 0), 0.25)
        self.assertGreater(norm_w.get("psr_coverage_fraction", 0), 0.15)

    def test_dynamic_renormalization_on_missing_features(self):
        raw = {"slope_20km_deg": 0.5, "roughness_10km_m": 0.5, "missing_feat": 0.5}
        available = {"slope_20km_deg", "roughness_10km_m"}
        norm = self.wm.normalize_weights(raw, available_features=available)
        self.assertAlmostEqual(sum(norm.values()), 1.0)
        self.assertEqual(norm["slope_20km_deg"], 0.5)
        self.assertEqual(norm["roughness_10km_m"], 0.5)


if __name__ == "__main__":
    unittest.main()
