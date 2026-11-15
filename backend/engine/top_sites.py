"""Top-site selection: non-maximum suppression, area-weighted site means.

Neighbouring cells must not be presented as separate sites, so peaks are
accepted greedily in descending score order only when they are at least the
configured separation distance from every already-accepted peak. A site's score
is the area-weighted mean of all cells within a fraction of that distance, so a
single noisy cell cannot define a site.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from backend.config import AppConfig

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray
) -> np.ndarray:
    """Great-circle distance in km from one point to an array of points."""
    phi1 = math.radians(lat1)
    phi2 = np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2 - lon1)
    a = (
        np.sin(dphi / 2.0) ** 2
        + math.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def select_sites(
    score: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    separation_km: float,
    max_sites: int,
) -> list[dict[str, Any]]:
    """Greedy non-maximum suppression over every finite land cell."""
    valid = np.isfinite(score)
    rows, cols = np.nonzero(valid)
    if rows.size == 0:
        return []
    values = score[rows, cols]
    order = np.argsort(-values, kind="stable")
    accepted: list[dict[str, Any]] = []
    accepted_lat: list[float] = []
    accepted_lon: list[float] = []
    for index in order:
        row = int(rows[index])
        col = int(cols[index])
        site_lat = float(lat[row])
        site_lon = float(lon[col])
        if accepted_lat:
            distances = haversine_km(
                site_lat,
                site_lon,
                np.asarray(accepted_lat, dtype=np.float64),
                np.asarray(accepted_lon, dtype=np.float64),
            )
            if float(distances.min()) < separation_km:
                continue
        accepted.append(
            {
                "row": row,
                "col": col,
                "lat": site_lat,
                "lon": site_lon,
                "peak_score": float(values[index]),
            }
        )
        accepted_lat.append(site_lat)
        accepted_lon.append(site_lon)
        if len(accepted) >= max_sites:
            break
    return accepted


def nearest_cell(
    lat: np.ndarray, lon: np.ndarray, lat_deg: float, lon_deg: float
) -> tuple[int, int]:
    """Nearest grid cell to a coordinate (grid is regular, so index search)."""
    row = int(np.argmin(np.abs(lat - lat_deg)))
    col = int(np.argmin(np.abs(lon - lon_deg)))
    return row, col


def _axis_slice(axis: np.ndarray, low: float, high: float) -> slice:
    """Slice covering ``[low, high]`` on a monotone axis, either direction."""
    if axis[0] <= axis[-1]:
        left = int(np.searchsorted(axis, low, side="left")) - 1
        right = int(np.searchsorted(axis, high, side="right")) + 1
    else:
        left = int(np.searchsorted(-axis, -high, side="left")) - 1
        right = int(np.searchsorted(-axis, -low, side="right")) + 1
    return slice(max(0, left), min(axis.size, right))


def window_slice(
    lat: np.ndarray, lon: np.ndarray, lat_deg: float, lon_deg: float, radius_km: float
) -> tuple[slice, slice]:
    """Bounding slice for a radius, widened so high latitudes are not clipped."""
    dlat = radius_km / 110.574
    coslat = max(math.cos(math.radians(lat_deg)), 1.0 / 3600.0)
    dlon = radius_km / (111.320 * coslat)
    rows = _axis_slice(lat, lat_deg - dlat, lat_deg + dlat)
    cols = _axis_slice(lon, lon_deg - dlon, lon_deg + dlon)
    return rows, cols


def site_aggregate(
    config: AppConfig,
    score: np.ndarray,
    groups: dict[str, np.ndarray],
    lat: np.ndarray,
    lon: np.ndarray,
    site: dict[str, Any],
    land: np.ndarray,
    separation_km: float,
) -> dict[str, Any]:
    """Area-weighted mean score and group scores around an accepted peak."""
    radius_km = separation_km * config.scoring.site_aggregation_fraction_of_separation
    rows, cols = window_slice(lat, lon, site["lat"], site["lon"], radius_km)
    block = score[rows, cols]
    sub_land = land[rows, cols]
    local_lat = lat[rows]
    finite = np.isfinite(block)
    weights = np.cos(np.radians(local_lat))[:, None] * sub_land * finite
    weight_sum = float(weights.sum())
    safe_block = np.where(finite, block, 0.0)
    if weight_sum <= 0.0:
        mean_score = float(site["peak_score"])
        group_means: dict[str, float] = {}
    else:
        mean_score = float((safe_block * weights).sum() / weight_sum)
        group_means = {}
        for name, grid in groups.items():
            local = grid[rows, cols]
            mask = np.isfinite(local)
            group_means[name] = (
                float((local[mask] * weights[mask]).sum() / weights[mask].sum())
                if mask.any()
                else float("nan")
            )
    step = float(abs(lat[1] - lat[0]))
    half = step / 2.0
    return {
        **site,
        "site_score": mean_score,
        "aggregation_radius_km": radius_km,
        "bbox": [
            site["lon"] - half,
            max(-90.0, site["lat"] - half),
            site["lon"] + half,
            min(90.0, site["lat"] + half),
        ],
        "polygon": [
            [site["lon"] - half, site["lat"] - half],
            [site["lon"] + half, site["lat"] - half],
            [site["lon"] + half, site["lat"] + half],
            [site["lon"] - half, site["lat"] + half],
            [site["lon"] - half, site["lat"] - half],
        ],
        "group_scores": group_means,
    }


def caveats_for(
    config: AppConfig, lat_deg: float, lon_deg: float
) -> list[dict[str, Any]]:
    """Heuristic caveats for a site, from the configured geographic boxes.

    These are flags, not masks: each box is coarse and labelled heuristic, and
    the caveat only tells the reader that this feature set cannot separate ice
    cover from bare ground there.
    """
    caveats: list[dict[str, Any]] = []
    for region in config.caveats.regions:
        if (
            region.lat_min <= lat_deg <= region.lat_max
            and region.lon_min <= lon_deg <= region.lon_max
        ):
            caveats.append(
                {
                    "id": region.id,
                    "label": region.label,
                    "text": config.caveats.text,
                    "heuristic": config.caveats.heuristic,
                    "region_note": region.note,
                }
            )
    return caveats


def is_famous(
    config: AppConfig, lat_deg: float, lon_deg: float
) -> tuple[bool, str | None]:
    """Whether a site is within the configured radius of a famous analog."""
    if not config.famous_sites:
        return False, None
    lats = np.asarray([site.lat for site in config.famous_sites], dtype=np.float64)
    lons = np.asarray([site.lon for site in config.famous_sites], dtype=np.float64)
    distances = haversine_km(lat_deg, lon_deg, lats, lons)
    index = int(np.argmin(distances))
    if float(distances[index]) <= config.famous_radius_km:
        return True, config.famous_sites[index].name
    return False, None
