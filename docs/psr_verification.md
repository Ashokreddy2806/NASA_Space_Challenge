# PSR verification — data-driven, not assumed

The lunar PSR table is a CSV of WKT polygons in projected metres with no CRS
field. This document records what was actually checked against the DEM, so the
ice proxy does not rest on an assumption.

## 1. DEM and table

- DEM: `K:\NASA_Space_Project\Datasets\Moon\LDEM_80S_80MPP_ADJ.tiff`
- CRS: `PROJCS["Moon (2015) - Sphere / Ocentric / South Polar",GEOGCS["Moon (2015) - Sphere / Ocentric",DATUM["Moon (2015) - Sphere",SPHEROID["Moon (2015) - Sphere",1737400,0]],PRIMEM["Reference Meridian",0],UNIT["degree",0.0174532925199433,AUTHORITY["EPSG","9122"]]],PROJECTION["Polar_Stereographic"],PARAMETER["latitude_of_origin",-90],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["metre",1],AXIS["Easting",NORTH],AXIS["Northing",NORTH]]`
- Size: 7600 × 7600 cells at 80 m; bounds -304000 … 304000 m easting, -304000 … 304000 m northing.
- DEM nodata fraction: 0.0000.
- PSR table: `K:\NASA_Space_Project\Datasets\Moon\LPSR_80S_20MPP_ADJ_1km2.csv`
- Polygons ≥ 1 km²: 1531; skipped below threshold: 0; total area 18,920.6 km².

## 2. Coordinate interpretation

- The CSV has no CRS metadata. The polygons are interpreted as metres in the
  **LDEM south polar stereographic CRS**, taken from the DEM itself.
- Evidence: the polygon coordinate range fits the DEM extent, and the
  rasterised PSRs land on topographic lows (section 4).
- Radius of the configured 85°S cap in this projection: **151.713 km**.
- DEM tile-corner radius: 429.9 km (≈ 75.9°S).

## 3. Extent checks

- Polygons fully inside the DEM: **1531** of 1531.
- Polygons touching or crossing the DEM edge: 0.
- Polygons inside the target cap: 366; clipped by the DEM edge: 0.

## 4. Are the rasterised PSRs on cold, low, flat terrain?

| Quantity | PSR pixels | Background (non-PSR) in cap |
|---|---|---|
| Elevation median (m) | -2389 | -1175 |
| Elevation p10–p90 (m) | -3881 – -398.7 | -2868 – 1032 |
| Slope median (deg) | 10.3 | 9.175 |
| Slope p10–p90 (deg) | 6.981 – 13.62 | 5.396 – 13.22 |

- PSR pixels in the cap: 1,110,902 of 11,298,156 (9.83%).
- PSR area inside the cap: 7,110 km² of 72,310 km².
- Fraction of PSR pixels below the background median elevation: **0.771**.
- Fraction of PSR pixels below the background median slope: **0.339**.
- Elevation offset (PSR − background): -1213.4 m.
- Slope offset (PSR − background): +1.12°.

## 5. Verdict

- PSRs sit on topographic lows: **True**
- PSRs sit on lower slopes than their surroundings: **False**
- The 85°S target cap is unaffected by the ~75.9°S tile-corner clip: **True**

The ~75.9°S figure is the radius of the **square tile corner**, not a latitude
cut. The region of interest is a 151.7 km cap around the pole, which sits well
inside the tile, so the corner clip cannot truncate it.
