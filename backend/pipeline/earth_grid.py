"""Common Earth grid and tiling helpers for the Phase 1 pipeline.

The published search grid is a regular 0.05° lon/lat grid. Terrain features,
however, must be computed in windows measured in kilometres. Each 10°×10° tile
is therefore reprojected to a local azimuthal-equidistant grid at 2 km, features
are computed there, and the results are sampled back onto the 0.05° grid.

Only the standard library, numpy, rasterio and pyproj are used.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
from pyproj import CRS, Transformer
from rasterio.transform import Affine, from_origin

# Search grid definition. Cell centres run from -179.975 to 179.975 and
# 89.975 to -89.975; the upper-left corner is (-180, 90).
RES_DEG = 0.05
LON_MIN = -180.0
LON_MAX = 180.0
LAT_MIN = -90.0
LAT_MAX = 90.0
NX = int(round((LON_MAX - LON_MIN) / RES_DEG))  # 7200
NY = int(round((LAT_MAX - LAT_MIN) / RES_DEG))  # 3600

TILE_DEG = 10.0
TILE_OVERLAP_DEG = 1.0
LOCAL_PIXEL_M = 2_000.0

ETOPO_PATH = "ETOPO_2022_v1_60s_N90W180_surface.tif"


@dataclass(frozen=True)
class Tile:
    """One 10°×10° analysis tile with a 1° halo for edge-safe filtering."""

    lat0: float
    lon0: float

    @property
    def core_bounds(self) -> tuple[float, float, float, float]:
        """Core bounds as (lon_min, lat_min, lon_max, lat_max)."""
        return (self.lon0, self.lat0, self.lon0 + TILE_DEG, self.lat0 + TILE_DEG)

    @property
    def padded_bounds(self) -> tuple[float, float, float, float]:
        """Core bounds expanded by the halo, clipped to the legal lon/lat range."""
        lon_min = max(LON_MIN, self.lon0 - TILE_OVERLAP_DEG)
        lon_max = min(LON_MAX, self.lon0 + TILE_DEG + TILE_OVERLAP_DEG)
        lat_min = max(LAT_MIN, self.lat0 - TILE_OVERLAP_DEG)
        lat_max = min(LAT_MAX, self.lat0 + TILE_DEG + TILE_OVERLAP_DEG)
        return (lon_min, lat_min, lon_max, lat_max)

    @property
    def center(self) -> tuple[float, float]:
        """Tile centre as (lon, lat)."""
        return (self.lon0 + TILE_DEG / 2.0, self.lat0 + TILE_DEG / 2.0)

    @property
    def name(self) -> str:
        """Stable identifier used in logs."""
        return f"lat{self.lat0:+06.1f}_lon{self.lon0:+07.1f}"


def iter_tiles() -> Iterator[Tile]:
    """Yield all 10°×10° tiles covering the globe, south to north."""
    lat = LAT_MIN
    while lat < LAT_MAX - 1e-9:
        lon = LON_MIN
        while lon < LON_MAX - 1e-9:
            yield Tile(lat0=lat, lon0=lon)
            lon += TILE_DEG
        lat += TILE_DEG


def lat_centers() -> np.ndarray:
    """Latitude cell centres, north to south (matches raster row order)."""
    return LAT_MAX - RES_DEG / 2.0 - np.arange(NY) * RES_DEG


def lon_centers() -> np.ndarray:
    """Longitude cell centres, west to east."""
    return LON_MIN + RES_DEG / 2.0 + np.arange(NX) * RES_DEG


def global_transform() -> Affine:
    """Affine transform of the 0.05° output grid (upper-left corner)."""
    return from_origin(LON_MIN, LAT_MAX, RES_DEG, RES_DEG)


def global_slices(tile: Tile) -> tuple[slice, slice]:
    """Return (row_slice, col_slice) of the core tile in the global grid."""
    lon_min, lat_min, lon_max, lat_max = tile.core_bounds
    col0 = int(round((lon_min - LON_MIN) / RES_DEG))
    col1 = int(round((lon_max - LON_MIN) / RES_DEG))
    row0 = int(round((LAT_MAX - lat_max) / RES_DEG))
    row1 = int(round((LAT_MAX - lat_min) / RES_DEG))
    return slice(row0, row1), slice(col0, col1)


def local_crs(tile: Tile) -> CRS:
    """Local azimuthal-equidistant CRS centred on the tile."""
    lon, lat = tile.center
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +datum=WGS84 +units=m +no_defs"
    )


def _edge_points(bounds: tuple[float, float, float, float], samples: int = 25) -> tuple[np.ndarray, np.ndarray]:
    """Sample points along all four edges of a lon/lat bounding box."""
    lon_min, lat_min, lon_max, lat_max = bounds
    lons = np.linspace(lon_min, lon_max, samples)
    lats = np.linspace(lat_min, lat_max, samples)
    lon_edge = np.concatenate([lons, lons, np.full(samples, lon_min), np.full(samples, lon_max)])
    lat_edge = np.concatenate([np.full(samples, lat_min), np.full(samples, lat_max), lats, lats])
    return lon_edge, lat_edge


def local_grid(tile: Tile, pixel_m: float = LOCAL_PIXEL_M) -> tuple[Affine, int, int, CRS]:
    """Destination transform, width, height and CRS for a tile's local grid."""
    crs = local_crs(tile)
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    lons, lats = _edge_points(tile.padded_bounds)
    xs, ys = transformer.transform(lons, lats)
    x_min, x_max = float(np.min(xs)), float(np.max(xs))
    y_min, y_max = float(np.min(ys)), float(np.max(ys))
    width = max(1, int(np.ceil((x_max - x_min) / pixel_m)))
    height = max(1, int(np.ceil((y_max - y_min) / pixel_m)))
    return from_origin(x_min, y_max, pixel_m, pixel_m), width, height, crs
