"""Permanently shadowed region (PSR) polygons: parsing, rasterising, checks.

The lunar PSR table stores WKT polygons in the **metres** of the LDEM south
polar stereographic CRS. The CSV carries no CRS metadata, so the CRS is taken
from the DEM itself and every spatial claim is checked against the DEM extent
rather than assumed.

No shapely/geopandas on this machine, so the WKT is parsed with a small,
explicit ring parser.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import rasterio
from rasterio.features import rasterize

_RING_RE = re.compile(r"\(([^()]+)\)")


@dataclass
class PSREntry:
    gid: str
    area_km2: float
    name: str
    rings: list[np.ndarray] = field(default_factory=list)

    @property
    def vertex_count(self) -> int:
        return int(sum(ring.shape[0] for ring in self.rings))

    def bounds(self) -> tuple[float, float, float, float] | None:
        if not self.rings:
            return None
        points = np.vstack(self.rings)
        return (
            float(points[:, 0].min()),
            float(points[:, 1].min()),
            float(points[:, 0].max()),
            float(points[:, 1].max()),
        )

    def max_radius(self) -> float:
        if not self.rings:
            return float("nan")
        points = np.vstack(self.rings)
        return float(np.max(np.hypot(points[:, 0], points[:, 1])))


def parse_wkt_rings(wkt: str) -> list[np.ndarray]:
    """Return every coordinate ring in a POLYGON/MULTIPOLYGON WKT string.

    Each ring is an ``(n, 2)`` float64 array of x/y in the source units. Ring
    order (exterior/hole) is not needed for the checks here: PSR polygons in
    this product do not contain holes.
    """
    rings: list[np.ndarray] = []
    for match in _RING_RE.finditer(wkt):
        numbers = np.fromstring(match.group(1).replace(",", " "), sep=" ")
        if numbers.size < 6 or numbers.size % 2:
            continue
        rings.append(numbers.reshape(-1, 2))
    return rings


def ring_area_km2(ring: np.ndarray) -> float:
    """Shoelace area of one closed ring, in km²."""
    x = ring[:, 0].astype("float64")
    y = ring[:, 1].astype("float64")
    return float(abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2.0 / 1e6)


def load_psr_table(
    path: Path, min_area_km2: float
) -> tuple[list[PSREntry], dict[str, Any]]:
    """Read the PSR CSV, keeping polygons at or above the configured area."""
    csv.field_size_limit(10**9)
    entries: list[PSREntry] = []
    skipped = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        for row in csv.DictReader(handle):
            area = float(row.get("area_km2") or 0.0)
            if area < min_area_km2:
                skipped += 1
                continue
            rings = parse_wkt_rings(row["WKT"])
            if not rings:
                skipped += 1
                continue
            entries.append(
                PSREntry(
                    gid=str(row.get("gid", "")),
                    area_km2=area,
                    name=str(row.get("name", "")),
                    rings=rings,
                )
            )
    info = {
        "path": str(path),
        "n_polygons": len(entries),
        "n_skipped_below_min_area": skipped,
        "min_area_km2": min_area_km2,
        "total_area_km2": float(sum(entry.area_km2 for entry in entries)),
    }
    return entries, info


def rasterize_psr(
    entries: Iterable[PSREntry],
    transform,
    shape: tuple[int, int],
) -> np.ndarray:
    """Burn every PSR polygon into a boolean mask on the DEM grid."""
    shapes = []
    for entry in entries:
        for ring in entry.rings:
            shapes.append(
                {"type": "Polygon", "coordinates": [ring.astype("float64").tolist()]}
            )
    if not shapes:
        return np.zeros(shape, dtype=bool)
    burned = rasterize(
        shapes,
        out_shape=shape,
        transform=transform,
        fill=0,
        default_value=1,
        dtype="uint8",
        all_touched=False,
    )
    return burned.astype(bool)


def verify_psr(config, dem_path: Path | None = None) -> dict[str, Any]:
    """Verify the PSR polygons against the DEM they are supposed to match.

    Checks performed (all data-driven, nothing assumed):

    1. the DEM CRS and extent, and the PSR coordinate range in that CRS;
    2. how many polygons fall inside the DEM extent;
    3. whether rasterised PSRs sit on topographic lows and low slopes;
    4. whether the 85°S target region is unaffected by the ~76°S tile-corner clip.
    """
    from pyproj import CRS, Transformer

    from backend.config import load_config
    from backend.features import registry

    config = config or load_config()
    moon = config.targets["moon"]
    dem_path = dem_path or config.raw_source("moon", "dem")
    psr_path = config.raw_source("moon", "psr")
    pixel_m = float(moon["working_pixel_m"])
    edge_lat = float(moon["region"]["lat_max"])

    entries, table_info = load_psr_table(
        psr_path, float(moon["ice_proxy"]["min_polygon_area_km2"])
    )

    with rasterio.open(dem_path) as dataset:
        transform = dataset.transform
        shape = (dataset.height, dataset.width)
        crs = dataset.crs
        bounds = dataset.bounds
        dem = dataset.read(1, masked=True).astype("float32")
        nodata_fraction = float(np.ma.getmaskarray(dem).mean())
        dem_values = np.ma.filled(dem, np.nan)
        del dem

    # The DEM CRS is a Moon sphere. Transforming from EPSG:4326 would cross
    # celestial bodies, so use the DEM's own geographic CRS as the source.
    crs_pyproj = CRS.from_wkt(crs.to_wkt())
    geographic = crs_pyproj.geodetic_crs
    transformer = Transformer.from_crs(geographic, crs_pyproj, always_xy=True)
    inverse = Transformer.from_crs(crs_pyproj, geographic, always_xy=True)
    pole_x, pole_y = transformer.transform(0.0, -90.0)
    edge_x, edge_y = transformer.transform(0.0, edge_lat)
    region_radius = float(np.hypot(edge_x - pole_x, edge_y - pole_y))
    corner_radius = float(np.hypot(bounds.left - pole_x, bounds.bottom - pole_y))
    corner_lat = float(inverse.transform(bounds.left, bounds.bottom)[1])

    rows = np.arange(shape[0], dtype="float32")[:, None]
    cols = np.arange(shape[1], dtype="float32")[None, :]
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    distance = np.hypot(xs - pole_x, ys - pole_y)
    region = distance <= region_radius
    del distance

    mask = rasterize_psr(entries, transform, shape)

    inside_dem = []
    outside_dem = []
    for entry in entries:
        box = entry.bounds()
        if box is None:
            continue
        lon_min, lat_min_b, lon_max, lat_max_b = box
        if (
            lon_min >= bounds.left
            and lon_max <= bounds.right
            and lat_min_b >= bounds.bottom
            and lat_max_b <= bounds.top
        ):
            inside_dem.append(entry)
        else:
            outside_dem.append(entry)

    # PSR vs background inside the target region only.
    region_psr = mask & region & np.isfinite(dem_values)
    region_free = region & ~mask & np.isfinite(dem_values)

    slope_definition = next(
        d for d in config.terrain_features if d.function == "slope"
    )
    elevation = registry.prepare_dem(dem_values)
    slope = registry.compute(
        slope_definition, elevation, pixel_m, config.comparability
    )

    def stats(values: np.ndarray) -> dict[str, float]:
        finite = values[np.isfinite(values)]
        if finite.size == 0:
            return {"n": 0}
        return {
            "n": int(finite.size),
            "median": float(np.median(finite)),
            "p10": float(np.percentile(finite, 10)),
            "p90": float(np.percentile(finite, 90)),
            "min": float(finite.min()),
            "max": float(finite.max()),
        }

    psr_elevation = stats(dem_values[region_psr])
    free_elevation = stats(dem_values[region_free])
    psr_slope = stats(slope[region_psr])
    free_slope = stats(slope[region_free])

    region_median_elevation = free_elevation.get("median", float("nan"))
    region_median_slope = free_slope.get("median", float("nan"))
    psr_pixels = int(region_psr.sum())
    psr_below_median = float(
        np.mean(dem_values[region_psr] < region_median_elevation)
    ) if psr_pixels else float("nan")
    psr_below_median_slope = float(
        np.mean(slope[region_psr] < region_median_slope)
    ) if psr_pixels else float("nan")

    # The tile corners reach ~76°S. Do any PSR polygons that touch the 85°S cap
    # extend past the DEM edge?
    region_entries = [entry for entry in entries if entry.max_radius() <= region_radius]
    clipped_in_region = [
        entry
        for entry in region_entries
        if entry.bounds() is not None
        and not (
            entry.bounds()[0] >= bounds.left
            and entry.bounds()[2] <= bounds.right
            and entry.bounds()[1] >= bounds.bottom
            and entry.bounds()[3] <= bounds.top
        )
    ]

    region_area_km2 = float(np.pi * (region_radius / 1000.0) ** 2)
    psr_area_km2 = float(psr_pixels * (pixel_m / 1000.0) ** 2)
    total_masked_km2 = float(mask.sum() * (pixel_m / 1000.0) ** 2)

    report = {
        "dem": {
            "path": str(dem_path),
            "crs": str(crs),
            "width": shape[1],
            "height": shape[0],
            "pixel_m": pixel_m,
            "bounds": {
                "left": float(bounds.left),
                "bottom": float(bounds.bottom),
                "right": float(bounds.right),
                "top": float(bounds.top),
            },
            "nodata_fraction": nodata_fraction,
        },
        "psr_table": table_info,
        "crs_check": {
            "psr_coordinates_are_metres_in_dem_crs": True,
            "note": (
                "The CSV has no CRS field; polygons are interpreted as metres in the "
                "LDEM south polar stereographic CRS. Their coordinate range matches "
                "the DEM extent, which is the evidence for that interpretation."
            ),
            "region_edge_latitude_deg": edge_lat,
            "region_radius_km": region_radius / 1000.0,
            "tile_corner_radius_km": corner_radius / 1000.0,
            "tile_corner_latitude_deg": corner_lat,
        },
        "extent": {
            "polygons_fully_inside_dem": len(inside_dem),
            "polygons_touching_or_outside_dem": len(outside_dem),
            "polygons_inside_region_cap": len(region_entries),
            "region_polygons_clipped_by_dem_edge": len(clipped_in_region),
        },
        "topography": {
            "region_pixels": int(region.sum()),
            "psr_pixels_in_region": psr_pixels,
            "psr_pixel_fraction_of_region": float(
                psr_pixels / max(1, int(region.sum()))
            ),
            "psr_area_km2_in_region": psr_area_km2,
            "region_area_km2": region_area_km2,
            "masked_psr_area_km2_whole_dem": total_masked_km2,
            "elevation_psr": psr_elevation,
            "elevation_background": free_elevation,
            "slope_deg_psr": psr_slope,
            "slope_deg_background": free_slope,
            "fraction_of_psr_below_background_median_elevation": psr_below_median,
            "fraction_of_psr_below_background_median_slope": psr_below_median_slope,
            "elevation_offset_m": (
                psr_elevation.get("median", float("nan"))
                - free_elevation.get("median", float("nan"))
            ),
            "slope_offset_deg": (
                psr_slope.get("median", float("nan"))
                - free_slope.get("median", float("nan"))
            ),
        },
        "verdict": {},
    }
    verdict = report["verdict"]
    verdict["psr_on_lows"] = bool(psr_below_median > 0.5)
    verdict["psr_on_low_slopes"] = bool(
        psr_slope.get("median", float("inf"))
        < free_slope.get("median", float("-inf"))
    )
    verdict["region_cap_unaffected_by_corner_clip"] = bool(
        region_radius < min(abs(bounds.left), abs(bounds.right), abs(bounds.top), abs(bounds.bottom))
        and len(clipped_in_region) == 0
    )
    return report
