"""Small geometry helpers shared by the Moon and Mars target modules."""

from __future__ import annotations

from typing import Any

import numpy as np
from pyproj import CRS, Transformer


def pyproj_crs(raster_crs: Any) -> CRS:
    """Convert a rasterio CRS to a pyproj CRS (needed for celestial bodies)."""
    return CRS.from_wkt(raster_crs.to_wkt())


def transformers(raster_crs: Any) -> tuple[CRS, Transformer, Transformer]:
    """Return (geographic CRS, forward, inverse) for a body's projected CRS.

    The source must be the DEM's own geographic CRS, not EPSG:4326: PROJ refuses
    to transform between celestial bodies, and on the Moon or Mars WGS84 would be
    the wrong planet.
    """
    projected = pyproj_crs(raster_crs)
    geographic = projected.geodetic_crs
    forward = Transformer.from_crs(geographic, projected, always_xy=True)
    inverse = Transformer.from_crs(projected, geographic, always_xy=True)
    return geographic, forward, inverse


def polar_radius_m(raster_crs: Any, lat_deg: float) -> float:
    """Distance from the pole to a parallel, in the projected CRS metres."""
    _, forward, _ = transformers(raster_crs)
    pole_x, pole_y = forward.transform(0.0, -90.0)
    x, y = forward.transform(0.0, lat_deg)
    return float(np.hypot(x - pole_x, y - pole_y))


def polar_coordinates(raster_crs: Any) -> tuple[float, float]:
    """Pole position in the projected CRS."""
    _, forward, _ = transformers(raster_crs)
    x, y = forward.transform(0.0, -90.0)
    return float(x), float(y)


def distance_from_pole(transform, shape: tuple[int, int], pole: tuple[float, float]) -> np.ndarray:
    """Distance of every pixel centre from the pole, in CRS metres."""
    rows = np.arange(shape[0], dtype="float32")[:, None]
    cols = np.arange(shape[1], dtype="float32")[None, :]
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    return np.hypot(xs - pole[0], ys - pole[1])


def sphere_crs(radius_m: float) -> CRS:
    """Geographic CRS for a spherical body of the given radius."""
    return CRS.from_proj4(f"+proj=longlat +R={radius_m:.3f} +no_defs")


def local_aeqd(radius_m: float, lat: float, lon: float) -> CRS:
    """Local azimuthal-equidistant CRS on a sphere of the given radius."""
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +R={radius_m:.3f} +units=m +no_defs"
    )
