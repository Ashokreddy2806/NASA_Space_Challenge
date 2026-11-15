"""Tests for planetary coordinate conversions and reprojection."""

import unittest

from scientific_engine.src.data.reprojection import (
    lunar_latlon_to_polar_xy,
    lunar_polar_xy_to_latlon,
    mars_latlon_to_mola_pixel,
    mars_lon_to_180,
    mars_lon_to_360,
)


class TestGeospatialReprojection(unittest.TestCase):
    def test_lunar_south_pole_is_at_origin(self):
        x, y = lunar_latlon_to_polar_xy(-90.0, 0.0)
        self.assertAlmostEqual(x, 0.0, places=3)
        self.assertAlmostEqual(y, 0.0, places=3)

        lat, lon = lunar_polar_xy_to_latlon(0.0, 0.0)
        self.assertAlmostEqual(lat, -90.0, places=3)

    def test_lunar_roundtrip_coordinate_fidelity(self):
        test_points = [
            (-89.9, 0.0),    # Shackleton rim
            (-86.0, 2.7),    # Malapert Mountain
            (-85.0, 180.0),  # 85S boundary
            (-80.0, -90.0),  # 80S tile edge midpoint
        ]
        for lat, lon in test_points:
            x, y = lunar_latlon_to_polar_xy(lat, lon)
            lat_back, lon_back = lunar_polar_xy_to_latlon(x, y)
            self.assertAlmostEqual(lat, lat_back, delta=0.01)
            # Longitude can wrap at poles, check angle difference
            diff_lon = (lon - lon_back + 180) % 360 - 180
            self.assertAlmostEqual(diff_lon, 0.0, delta=0.05)

    def test_mars_longitude_conversions(self):
        # -68.5 W should be 360 - 68.5 = 291.5 E
        self.assertAlmostEqual(mars_lon_to_360(-68.5), 291.5)
        self.assertAlmostEqual(mars_lon_to_180(291.5), -68.5)
        # 77.58 E should remain 77.58
        self.assertAlmostEqual(mars_lon_to_360(77.58), 77.58)

    def test_mola_pixel_lookup(self):
        # North pole (90N, 0E) -> row 0, col 0
        r, c = mars_latlon_to_mola_pixel(90.0, 0.0)
        self.assertEqual(r, 0)
        self.assertEqual(c, 0)

        # South pole (-90N, 0E) -> row 2879, col 0
        r, c = mars_latlon_to_mola_pixel(-90.0, 0.0)
        self.assertEqual(r, 2879)

        # Equator (0N, 180E) -> row 1440, col 2880
        r, c = mars_latlon_to_mola_pixel(0.0, 180.0)
        self.assertEqual(r, 1440)
        self.assertEqual(c, 2880)


if __name__ == "__main__":
    unittest.main()
