# DATASETS.md — Pool of datasets used in this project

Challenge: NASA Space Apps 2026, "Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars".
Place this file at `docs/DATASETS.md`. Raw files live in `data/raw/<body>/` (git-ignored).
Status legend: DOWNLOADED = file is on disk. HAND-MADE = small CSV we write ourselves from papers. OPTIONAL = use only if present.

---

## 1. MOON — `data/raw/moon/`

Source family: NASA LRO / LOLA, processed by NASA GSFC PGDA (south polar stereographic, cloud-optimized GeoTIFFs, MOON_ME frame).
Landing page: https://pgda.gsfc.nasa.gov/products/90
Cite: Barker et al., 2023, Planetary Science Journal 4, 183, https://doi.org/10.3847/PSJ/acf3e1 — Data DOI: https://doi.org/10.60903/gsfcpgda-lola-spole

| ID | File (local name) | Link | Size | Format | What it gives us | Status |
|----|-------------------|------|------|--------|------------------|--------|
| M1 | `LDEM_80S_80MPP_ADJ.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDEM_80S_80MPP_ADJ.TIF | ~181 MB | COG GeoTIFF, metres, 80 m/pixel, 80°S–pole | Elevation → relief, slope, roughness for the south pole target | DOWNLOADED |
| M2 | `LDRM_80S_1000MPP_ADJ_ROUGH_800M.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_ROUGH_800M.TIF | ~1.5 MB | GeoTIFF, metres, 1 km/pixel | Roughness at 800 m baseline | DOWNLOADED |
| M3 | `LDRM_80S_1000MPP_ADJ_ROUGH_1600M.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_ROUGH_1600M.TIF | ~1.5 MB | GeoTIFF, metres | Roughness at 1600 m baseline | DOWNLOADED |
| M4 | `LDRM_80S_1000MPP_ADJ_SLP_800M.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_SLP_800M.TIF | ~1.5 MB | GeoTIFF, degrees | Slope at 800 m baseline | DOWNLOADED |
| M5 | `LDRM_80S_1000MPP_ADJ_SLP_1600M.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_SLP_1600M.TIF | ~1.5 MB | GeoTIFF, degrees | Slope at 1600 m baseline | DOWNLOADED |
| M6 | `LDRM_80S_1000MPP_ADJ_H.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_H.TIF | ~1.4 MB | GeoTIFF, unitless | Hurst exponent: how roughness changes with scale (scale-robust feature) | DOWNLOADED |
| M7 | `LDRM_80S_1000MPP_ADJ_SPSLP.TIF` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LDRM_80S_1000MPP_ADJ_SPSLP.TIF | ~1.7 MB | GeoTIFF, sigma/km | Roughness spectral slope (scale-robust feature) | DOWNLOADED |
| M8 | `LPSR_80S_20MPP_ADJ_1km2.CSV` | https://pgda.gsfc.nasa.gov/data/LOLA_20mpp/LPSR_80S_20MPP_ADJ_1km2.CSV | ~28 MB | CSV (columns to be inspected) | Permanently shadowed regions > 1 km² → cold-trap / ice proxy | DOWNLOADED |
| M9 | `ldem_16.tif` | https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_16.tif | ~63 MB | Plain TIFF, km, 5760×2880 global | Global lunar elevation for context only. Distorted near the pole: do NOT use for polar slope. | OPTIONAL |
| M10 | `moon_thermal_literature.csv` | (hand-made; source: Williams et al. 2019, JGR, https://doi.org/10.1029/2019JE006028) | tiny | CSV: feature, value, units, source | Lunar temperature numbers (e.g. cold-trapping threshold ~110 K, day/night extremes) | HAND-MADE |

Notes: the files above cover latitudes poleward of 80°S only. Moon temperature is NOT a raster in our data.

---

## 2. MARS — `data/raw/mars/`

| ID | File (local name) | Link | Size | Format | What it gives us | Status |
|----|-------------------|------|------|--------|------------------|--------|
| R1 | `mars_elev.npy` (converted from `megt90n000eb.img`) | https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg016/megt90n000eb.img (parent page: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) | ~33 MB | Raw int16 big-endian, 2880 rows × 5760 cols, metres, 16 pixels/degree (~3.7 km) | MOLA global topography → relief, slope, roughness for the Mars target (default site: Jezero Crater) | DOWNLOADED |
| R2 | TES thermal inertia (Putzig et al.) | https://www.mars.asu.edu/data/tes_putzigti/nighttime2005/ ("Download global map: TIF") | small | Colorized TIF (not raw numbers) | Surface material proxy (dust vs rock). Colorized, so use qualitatively only. | OPTIONAL |
| R3 | `mars_thermal_literature.csv` | (hand-made; cite papers, e.g. Putzig et al. 2005, Icarus 173; Putzig & Mellon 2007, https://doi.org/10.1016/j.icarus.2007.05.013) | tiny | CSV: feature, value, units, source | Mars temperature and thermal-inertia numbers for the chosen site | HAND-MADE |

Cite MOLA data: MGS MOLA MEGDR, DOI 10.17189/1519460 (PDS Geosciences Node).

---

## 3. EARTH — `data/raw/earth/`

| ID | File (local name) | Link | Size | Format | What it gives us | Status |
|----|-------------------|------|------|--------|------------------|--------|
| E1 | WorldClim 2.1 bioclimatic variables (`wc2.1_<res>_bio_<n>.tif`) | 2.5 min: https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip — 10 min (fallback): https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_10m_bio.zip — page: https://worldclim.org/data/worldclim21.html | zip | 19 GeoTIFFs, °C and mm, 1970–2000 averages | Air temperature, day/night range, annual range, rainfall (dryness). Ocean = nodata → use as LAND MASK. | DOWNLOADED |
| E2 | `ETOPO_2022_v1_60s_N90W180_surface.tif` | https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif (page: https://www.ncei.noaa.gov/products/etopo-global-relief-model) | several hundred MB (not verified) | GeoTIFF, metres, 60 arc-second (~1.85 km), global incl. poles | Earth elevation for relief, slope, roughness and scale-robust roughness (Hurst-like) features, including Antarctica and the Arctic | DOWNLOADED |

WorldClim variables we use: bio_1 (annual mean temp), bio_2 (mean diurnal range = day/night swing proxy), bio_5 (max temp warmest month), bio_6 (min temp coldest month), bio_7 (annual temp range), bio_12 (annual precipitation), bio_14 (precipitation of driest month).
Cite: Fick & Hijmans 2017, Int. J. Climatology 37(12), 4302–4315. ETOPO: NOAA NCEI 2022, https://doi.org/10.25921/fd45-gt74.

If E2 is too large for disk: use Grid Extract (https://www.ncei.noaa.gov/maps/grid-extract/), "Ice surface" version, and download polar subsets only.

---

## 4. Feature map (what comes from where)

| Feature | Moon (south pole) | Mars (site TBD, default Jezero) | Earth |
|---------|-------------------|---------------------------------|-------|
| Relief / elevation range | M1 | R1 | E2 |
| Slope | M4, M5 (and M1) | R1 | E2 |
| Roughness (multi-scale) | M2, M3 | R1 | E2 |
| Scale-robust roughness (Hurst / spectral slope) | M6, M7 | derive from R1 where resolution allows | derive from E2 over several window sizes |
| Temperature stats and day/night swing | M10 (literature) | R3 (literature) | E1 bio_1, 2, 5, 6, 7 |
| Dryness | n/a (airless) | n/a | E1 bio_12, bio_14 |
| Ice / cold-trap proxy | M8 (PSR table) | n/a in MVP | E1 cold extremes (bio_6) |

---

## 5. Known limitations (state these in the submission)
- WorldClim gives AIR temperature, not surface temperature, and may not cover Antarctica; ETOPO gives elevation only.
- Moon files cover only poleward of 80°S. Mars MOLA at 16 ppd is ~3.7 km per pixel; Earth ETOPO is ~1.85 km. Compare features at matched physical window sizes.
- Earth cannot reproduce reduced gravity, lunar vacuum, the thin Martian atmosphere, or the radiation environments.
- Moon and Mars temperatures come from published values, not from rasters.

## 6. Dropped or not used (and why)
- Diviner temperature rasters: host site blocks automated access, large polar files.
- MODIS land surface temperature: needs NASA Earthdata login, heavy. WorldClim bio_2 and bio_7 replace it.
- Large LOLA products (hundreds of MB to several GB): not needed for a coarse screening tool.
- WorldClim elevation: replaced by ETOPO (poles covered).
- Minerals, dust, soil moisture, vegetation index, permafrost: stretch goals only.
