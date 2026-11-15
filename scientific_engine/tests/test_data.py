"""Tests for data discovery and loading."""

import unittest
from pathlib import Path

from scientific_engine.src.data.discovery import get_dataset_catalog
from scientific_engine.src.data.loading import (
    load_literature_csv,
    load_psr_polygons_summary,
    load_yaml_config,
)
from scientific_engine.src.data.validation import validate_feature_value


class TestDataDiscoveryAndLoading(unittest.TestCase):
    def test_dataset_catalog_has_all_mvp_ids(self):
        catalog = get_dataset_catalog()
        expected_ids = {"M1", "M2", "M3", "M4", "M5", "M6", "M7", "M8", "M10", "R1", "R3", "E1"}
        for expected in expected_ids:
            self.assertIn(expected, catalog, f"Missing catalog entry {expected}")
            self.assertTrue(len(catalog[expected].source_url) > 0)
            self.assertTrue(len(catalog[expected].crs_description) > 0)

    def test_literature_csv_loads_correctly(self):
        meta_dir = Path(__file__).resolve().parents[1] / "data" / "metadata"
        moon_csv = meta_dir / "moon_thermal_literature.csv"
        mars_csv = meta_dir / "mars_thermal_literature.csv"

        self.assertTrue(moon_csv.exists(), "Moon thermal literature CSV must exist")
        self.assertTrue(mars_csv.exists(), "Mars thermal literature CSV must exist")

        moon_records = load_literature_csv(moon_csv)
        self.assertIn("cold_trapping_threshold_k", moon_records)
        self.assertEqual(moon_records["cold_trapping_threshold_k"]["value"], 110.0)

        mars_records = load_literature_csv(mars_csv)
        self.assertIn("jezero_annual_mean_temp_k", mars_records)
        self.assertEqual(mars_records["jezero_annual_mean_temp_k"]["value"], 214.2)

    def test_psr_summary_fallback_consistency(self):
        summary = load_psr_polygons_summary(Path("non_existent_file.csv"))
        self.assertEqual(summary["polygon_count"], 1531)
        self.assertAlmostEqual(summary["total_area_km2"], 18920.6)

    def test_feature_value_physical_validation(self):
        valid, _ = validate_feature_value("slope_20km_deg", 12.5)
        self.assertTrue(valid)

        invalid_slope, _ = validate_feature_value("slope_20km_deg", 95.0)
        self.assertFalse(invalid_slope)

        valid_relief, _ = validate_feature_value("relief_20km_m", 1500.0)
        self.assertTrue(valid_relief)


if __name__ == "__main__":
    unittest.main()
