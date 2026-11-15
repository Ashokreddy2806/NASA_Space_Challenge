"""Common search-grid and tiling helpers, driven entirely by configuration.

The published search grid is a regular lon/lat grid whose limits, resolution and
tile size come from ``config/config.yaml``. Terrain features must be computed in
windows measured in kilometres, so each tile is reprojected to a local
azimuthal-equidistant grid at the configured working pixel size, features are
computed there, and the results are sampled back onto the search grid.

``GLOBE_*`` below are the limits of the lon/lat coordinate system itself, not
tunable project settings: a padded tile may reach past the configured bounding
box (that is how a regional proof run still gets real halo data) but never past
these limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
from pyproj import CRS, Transformer
from rasterio.transform import Affine, from_origin

from backend.config import GridSpec

GLOBE_LON_MIN = -180.0
GLOBE_LON_MAX = 180.0
GLOBE_LAT_MIN = -90.0
GLOBE_LAT_MAX = 90.0

_EPS = 1e-9


@dataclass(frozen=True)
class Tile:
    """One analysis tile, with its bounds and the grid it belongs to."""

    lat0: float
    lon0: float
    lat1: float
    lon1: float
    spec: GridSpec

    @property
    def core_bounds(self) -> tuple[float, float, float, float]:
        """Core bounds as (lon_min, lat_min, lon_max, lat_max)."""
        return (self.lon0, self.lat0, self.lon1, self.lat1)

    @property
    def padded_bounds(self) -> tuple[float, float, float, float]:
        """Core bounds expanded by the halo, clipped to the legal lon/lat range."""
        halo = self.spec.halo_deg
        return (
            max(GLOBE_LON_MIN, self.lon0 - halo),
            max(GLOBE_LAT_MIN, self.lat0 - halo),
            min(GLOBE_LON_MAX, self.lon1 + halo),
            min(GLOBE_LAT_MAX, self.lat1 + halo),
        )

    @property
    def center(self) -> tuple[float, float]:
        """Tile centre as (lon, lat)."""
        return ((self.lon0 + self.lon1) / 2.0, (self.lat0 + self.lat1) / 2.0)

    @property
    def name(self) -> str:
        """Stable identifier used in logs."""
        return f"lat{self.lat0:+06.1f}_lon{self.lon0:+07.1f}"


def iter_tiles(spec: GridSpec) -> Iterator[Tile]:
    """Yield every tile covering the configured bounds, south to north.

    Edge tiles are clipped to the bounds, so a regional bounding box that is not
    a whole number of tiles still works.
    """
    lat = spec.lat_min
    while lat < spec.lat_max - _EPS:
        lat1 = min(spec.lat_max, lat + spec.tile_deg)
        lon = spec.lon_min
        while lon < spec.lon_max - _EPS:
            lon1 = min(spec.lon_max, lon + spec.tile_deg)
            yield Tile(lat0=lat, lon0=lon, lat1=lat1, lon1=lon1, spec=spec)
            lon = lon1
        lat = lat1


def lat_centers(spec: GridSpec) -> np.ndarray:
    """Latitude cell centres, north to south (matches raster row order)."""
    return spec.lat_max - spec.resolution_deg / 2.0 - np.arange(spec.ny) * spec.resolution_deg


def lon_centers(spec: GridSpec) -> np.ndarray:
    """Longitude cell centres, west to east."""
    return spec.lon_min + spec.resolution_deg / 2.0 + np.arange(spec.nx) * spec.resolution_deg


def global_transform(spec: GridSpec) -> Affine:
    """Affine transform of the search grid (upper-left corner)."""
    return from_origin(spec.lon_min, spec.lat_max, spec.resolution_deg, spec.resolution_deg)


def tile_transform(tile: Tile) -> Affine:
    """Affine transform of a tile's core window on the search grid."""
    return from_origin(tile.lon0, tile.lat1, tile.spec.resolution_deg, tile.spec.resolution_deg)


def global_slices(tile: Tile) -> tuple[slice, slice]:
    """Return (row_slice, col_slice) of the core tile in the search grid."""
    spec = tile.spec
    lon_min, lat_min, lon_max, lat_max = tile.core_bounds
    col0 = int(round((lon_min - spec.lon_min) / spec.resolution_deg))
    col1 = int(round((lon_max - spec.lon_min) / spec.resolution_deg))
    row0 = int(round((spec.lat_max - lat_max) / spec.resolution_deg))
    row1 = int(round((spec.lat_max - lat_min) / spec.resolution_deg))
    return (
        slice(max(0, row0), min(spec.ny, row1)),
        slice(max(0, col0), min(spec.nx, col1)),
    )


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


def local_grid(
    tile: Tile, pixel_m: float | None = None
) -> tuple[Affine, int, int, CRS]:
    """Destination transform, width, height and CRS for a tile's local grid."""
    pixel_m = float(tile.spec.working_pixel_m if pixel_m is None else pixel_m)
    crs = local_crs(tile)
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    lons, lats = _edge_points(tile.padded_bounds)
    xs, ys = transformer.transform(lons, lats)
    x_min, x_max = float(np.min(xs)), float(np.max(xs))
    y_min, y_max = float(np.min(ys)), float(np.max(ys))
    width = max(1, int(np.ceil((x_max - x_min) / pixel_m)))
    height = max(1, int(np.ceil((y_max - y_min) / pixel_m)))
    return from_origin(x_min, y_max, pixel_m, pixel_m), width, height, crs


def sample_point_rowcol(spec: GridSpec, lat: float, lon: float) -> tuple[int, int]:
    """Nearest search-grid (row, col) for a lon/lat point, clipped to the grid."""
    row = int(round((spec.lat_max - lat) / spec.resolution_deg - 0.5))
    col = int(round((lon - spec.lon_min) / spec.resolution_deg - 0.5))
    return min(max(row, 0), spec.ny - 1), min(max(col, 0), spec.nx - 1)
