"""Unit tests for Mars Target Profile generator."""

import json
import unittest
from pathlib import Path

from backend.target_profiles.mars_target import (
    get_oxia_planum_profile,
    get_jezero_crater_profile,
    generate_all_mars_profiles,
)


class TestMarsTargetProfile(unittest.TestCase):
    def test_oxia_planum_profile_structure(self):
        profile = get_oxia_planum_profile()
        self.assertEqual(profile.target_id, "mars_oxia_planum")
        self.assertEqual(profile.coordinates.center_lat, 18.275)
        self.assertEqual(profile.tier1_global_vector["vegetation_ndvi"], 0.0)
        self.assertEqual(profile.tier1_global_vector["soil_moisture_fraction"], 0.0)
        self.assertIn("fe/mg", profile.detailed_measurements.get("clay_phyllosilicate_index").notes.lower())

    def test_jezero_crater_profile_structure(self):
        profile = get_jezero_crater_profile()
        self.assertEqual(profile.target_id, "mars_jezero_crater")
        self.assertAlmostEqual(profile.coordinates.center_lat, 18.380)
        self.assertIn("surface_gravity", profile.irreducible_limits)

    def test_json_export_and_load(self):
        test_dir = Path("/tmp/nasa_test_output")
        profiles = generate_all_mars_profiles(output_dir=test_dir)
        self.assertEqual(len(profiles), 2)

        json_file = test_dir / "mars_target_profile.json"
        self.assertTrue(json_file.exists())

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertEqual(data["target_id"], "mars_oxia_planum")
        self.assertIn("tier1_global_vector", data)
        self.assertIn("tier1_tolerances", data)
        self.assertIn("tier1_feature_weights", data)
        self.assertIn("detailed_measurements", data)


if __name__ == "__main__":
    unittest.main()
