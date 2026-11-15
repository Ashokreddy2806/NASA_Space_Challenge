"""Tests for Moon and Mars target profiles and schema generation."""

import unittest
from pathlib import Path

from scientific_engine.src.data.validation import validate_profile_dict
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile
from scientific_engine.src.profiles.profile_generator import generate_all_target_profiles


class TestProfiles(unittest.TestCase):
    def test_moon_profile_completeness_and_schema(self):
        profile = build_moon_target_profile()
        errors = validate_profile_dict(profile)
        self.assertEqual(len(errors), 0, f"Moon profile validation failed: {errors}")

        features = profile["features"]
        self.assertIn("relief_20km_m", features)
        self.assertIn("slope_20km_deg", features)
        self.assertIn("roughness_10km_m", features)
        self.assertIn("hurst_2_32km", features)
        self.assertIn("temp_mean_c", features)
        self.assertIn("psr_coverage_fraction", features)

        # Check defensible values
        self.assertGreater(features["relief_20km_m"]["value"], 2000.0)
        self.assertGreater(features["slope_20km_deg"]["value"], 5.0)
        self.assertLess(features["temp_mean_c"]["value"], -100.0)

    def test_mars_jezero_profile_completeness(self):
        profile = build_jezero_profile()
        errors = validate_profile_dict(profile)
        self.assertEqual(len(errors), 0, f"Jezero profile validation failed: {errors}")

        features = profile["features"]
        self.assertIn("relief_20km_m", features)
        self.assertIn("temp_diurnal_range_c", features)
        self.assertAlmostEqual(features["temp_mean_c"]["value"], -58.95, places=1)
        self.assertEqual(features["precip_annual_mm"]["value"], 0.0)

    def test_profile_generator_outputs_valid_json(self):
        profiles = generate_all_target_profiles()
        self.assertIn("targets", profiles)
        targets = profiles["targets"]
        self.assertIn("moon_south_pole", targets)
        self.assertIn("mars_jezero_crater", targets)
        self.assertIn("mars_oxia_planum", targets)


if __name__ == "__main__":
    unittest.main()
