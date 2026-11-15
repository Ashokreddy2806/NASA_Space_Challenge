# Data Catalog

What data the challenge portals give us, what each type looks like, and which products we plan to pull. Moon/Mars rows were checked against the live PDS directories on 2026-11-14 (file names and sizes are real). Earth rows are from product documentation and **still need a version/size check** once someone is logged in to Earthdata.

Links: [PROBLEM_STATEMENT.md](../PROBLEM_STATEMENT.md#resources) · Plan: [PLAN.md](../PLAN.md) · Downloader: [backend/pipeline/download.py](../backend/pipeline/download.py)

---

## 1. Kinds of data (what you will actually open)

| Kind | What it is | Typical formats | Python tools | Where it appears |
|---|---|---|---|---|
| **Gridded raster (map)** | A 2D grid of numbers, one per pixel, georeferenced (lat/lon or a polar projection). Elevation, temperature, rock abundance, NDVI. | GeoTIFF, PDS3 `.img` + `.lbl`, PDS4 `.xml`, NetCDF, HDF4/HDF5 | `rasterio`, `xarray`, `numpy.fromfile` | LOLA, MOLA, Diviner GDR, MODIS, SRTM |
| **Multi-band / hyperspectral cube** | A raster with hundreds of bands (one per wavelength). Gives mineral identity. | NetCDF4, ENVI, HDF5 | `xarray`, `spectral` | EMIT, CRISM, ASTER |
| **Point / table data** | One row per measurement (lat, lon, value...). Must be binned onto a grid. | ASCII `.tab`/`.csv`, binary tables | `pandas` | Diviner Polar Resource Products, LEND |
| **Time series / climatology** | The same grid repeated over time (monthly, diurnal, seasonal). Gives temperature range and extremes. | NetCDF, HDF, many files | `xarray` | MODIS LST, SMAP, IMERG, Diviner seasonal |
| **Radar (SAR)** | Backscatter images; see surface roughness and ice, through cloud, day and night. Heavy. | GeoTIFF, SAFE zip, RADARSAT products | `rasterio`, `sarpy` | Sentinel-1, RADARSAT, Mini-RF |
| **Imagery** | Visible/IR pictures for visual checks, not analysis. | JPEG2000, PNG, tiles | `rasterio`, web tiles | LROC, Worldview |

### Formats you will meet
- **PDS3 `.img` + `.lbl`:** a raw binary array plus a text label that gives dimensions, data type, byte order, scaling and the map projection. Read the `.lbl` first; do not guess the shape. Missing-data values are written in the label (e.g. `-32768`).
- **Scaling:** many integer rasters need `value = DN * SCALING_FACTOR + OFFSET` (Diviner rock abundance: factor 0.001).
- **Moon/Mars have no "ground truth" CRS from the web**: radii are in the label (Moon sphere 1737.4 km). Projections are cylindrical (equirectangular) globally and **polar stereographic** near the poles.
- **"ppd" = pixels per degree.** 16 ppd ≈ 1.9 km/px on the Moon, ≈ 3.7 km/px on Mars. 128 ppd ≈ 240 m/px (Moon).

## 2. Moon (lunar south pole) — no login needed

All from the PDS Geosciences Node (`pds-geosciences.wustl.edu`), open HTTP.

### 2.1 LRO LOLA — elevation (laser altimeter)
Base: `.../lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/`

| Product | File | Size | Use |
|---|---|---|---|
| Global DEM, 16 ppd | `cylindrical/float_img/ldem_16_float.img` | 66 MB | Coarse global context; slope/roughness at ~2 km |
| South polar DEM, 80 m/px (80°S–90°S) | `polar/float_img/ldem_80s_80m_float.img` | 231 MB | **Main south-pole terrain**: slope, roughness, elevation range |
| South polar DEM, 40 m/px (85°S–90°S) | `polar/float_img/ldem_85s_40m_float.img` | 230 MB | Zoom on candidate base sites (Shackleton rim etc.) |
| South polar DEM, 20 m/px (87.5°S–90°S) | `polar/float_img/ldem_875s_20m_float.img` | 230 MB | Finest practical for a single site |
| (bigger, skip unless needed) | `ldem_75s_30m`, `ldem_128`, `ldem_256_*` | 0.8–4 GB | Not needed for the hackathon |

Format: 32-bit float, little-endian, **metres relative to the 1737.4 km sphere**, polar stereographic. Derived features: slope, roughness (std of slope in a window), relief, crater/depression density.

### 2.2 LRO Diviner — temperature, rock abundance, ice stability
Base: `.../lro/urn-nasa-pds-lro_diviner_derived1/` (bundle mirrors `lro-l-dlre-4-rdr-v1/lrodlr_1001`)

| Product | File | Size | What it gives |
|---|---|---|---|
| Rock abundance, global 32 ppd | `data_derived_gdr_l3/cylindrical/img/dgdr_ra_avg_cyl_032_img.img` | 88 MB | Fraction of surface covered by rocks (scale 0.001). Roughness/regolith proxy |
| Christiansen feature, global 32 ppd | `.../dgdr_nen_cf_clc_cyl_032_img.img` | 88 MB | Mid-IR emissivity peak position = **silicate mineralogy** (basaltic vs feldspathic) |
| Polar Resource Product, south | `data/prp/dlre_prp_south.tab` + `.lbl` | **605 MB** | Table (2.88 M rows x 15 cols) of polar temperatures: max, mean, min, ice-stability depths. Key for **cold traps / permanently shadowed regions** |
| Polar cumulative products | `data/pcp/seasonal`, `.../diurnal` | varies | Temperature by season / local time at the poles |

Other Diviner GDR bands (bolometric brightness temperature, etc.) are in the same `gdr_l3` folder; list before downloading.

### 2.3 Other lunar products (second priority)
- **LRO LEND** (neutron spectrometer): hydrogen/ice proxy, ~10 km resolution; PDS folder `lro-l-lend-4-cdr-v1` (not located under that name; browse from the LRO page before downloading).
- **LRO Mini-RF**: S-band radar, CPR (circular polarization ratio) as ice/roughness indicator.
- **LROC**: images only, for visuals and boulder counts.
- **Illumination**: LOLA-derived illumination/Earth-visibility maps for the poles (extras / PCP products).

## 3. Mars — no login needed

PDS Geosciences, `mgs-m-mola-5-megdr-l3-v1/mgsl_300x/`

| Product | File | Size | Use |
|---|---|---|---|
| MOLA topography, 16 ppd (global) | `meg016/megt90n000eb.img` | 33 MB | Global elevation ~3.7 km/px |
| MOLA topography, 128 ppd tiles | `meg128/megt{00n,44n,44s,88n}{000,090,180,270}hb.img` | 16 tiles x 65–130 MB | ~460 m/px; only download tiles covering the chosen site |
| Also in `meg016`: `mega` (areoid), `megc`(counts), `megr`(radius) | 33 MB each | Reference surfaces |

Format: 16-bit signed integers, big-endian, metres above the MOLA areoid; label `.lbl` has scale.
**To fetch from PDS Imaging/other nodes (browse manually):** MRO CRISM (minerals), THEMIS (thermal inertia), TES (dust, thermal inertia), Odyssey GRS/NS (hydrogen). Site choice (Jezero?) decides which tiles matter. Mars Climate Database (temperature) is a model, not an archive.

## 4. Earth — Earthdata login required

Create a free account at https://urs.earthdata.nasa.gov/ and put credentials in `~/.netrc` (never in the repo; `.netrc` is git-ignored). Search/download via Earthdata Search or `earthaccess`.

| Feature | Product (short name) | Resolution | Format | Notes |
|---|---|---|---|---|
| Surface temp (mean, min, max, range) | MODIS Terra **MOD11C3** v061 (monthly LST) | 0.05° global | HDF4 | ~2 MB per month; ~12–24 months give a climatology. Already on our target grid |
| Vegetation / dryness | MODIS **MOD13C2** v061 (monthly NDVI) | 0.05° | HDF4 | Mask cells with NDVI above threshold |
| Elevation | **SRTMGL3** or **NASADEM**, or ASTER GDEM | 90 m / 30 m | GeoTIFF/HGT tiles | Large; resample to 0.05° and derive slope/roughness. Alternative with no login: Copernicus DEM GLO-90 on AWS (checked, open) |
| Minerals | **EMIT L2B mineral** (EMITL2BMIN); **ASTER GED** AG100/AG1km | 60 m / 100 m | NetCDF / HDF5 | EMIT covers arid regions only (~±52°) and is granule-based and large: use for top sites only. ASTER GED is global |
| Soil moisture | SMAP **SPL3SMP_E** (9 km, daily) or L4 | 9–36 km | HDF5 | Dryness proxy; average over time |
| Snow / ice | MODIS **MOD10CM** (monthly snow cover) | 0.05° | HDF4 | Cold-trap/ice analog |
| Permafrost | ESA CCI Permafrost | ~1 km | NetCDF | From ESA, no NASA login |
| Dust | MERRA-2 aerosol (**M2TMNXAER**) | 0.5°×0.625° | NetCDF4 | Very coarse; Mars dust analog |
| Precipitation | GPM **IMERG** monthly / JAXA GSMaP | 0.1° | NetCDF/HDF5 | Dryness proxy |
| Radar (one site only) | Sentinel-1 (Copernicus), RADARSAT (CSA) | 10–100 m | GeoTIFF/SAFE | Too heavy for global; pick one candidate |

Partner portals (all free, mostly with their own login): Copernicus Data Space (Sentinel, DEM), ESA Open Science Catalog (permafrost etc.), JAXA G-Portal (GSMaP, snow, vegetation; account needed), CSA (RADARSAT).

## 5. Feature mapping (the common feature space)

| Feature | Earth source | Moon source | Mars source |
|---|---|---|---|
| Elevation range / slope / roughness | SRTM/Copernicus DEM | LOLA | MOLA |
| Surface temp mean / extremes / range | MODIS LST | Diviner PRP | MCD / TES |
| Rock abundance (surface roughness proxy) | ASTER emissivity (indirect) | Diviner RA | TES / THEMIS |
| Silicate mineralogy | ASTER GED, EMIT | Diviner CF | CRISM / TES |
| Water / ice / hydrogen | MODIS snow, permafrost, SMAP | Diviner (ice depth), LEND | Odyssey GRS |
| Vegetation (should be 0) | MODIS NDVI | 0 | 0 |
| Dust | MERRA-2 | — | TES dust index |

## 6. What the data cannot give us (state this in the write-up)
Gravity (Moon 1/6 g, Mars 0.38 g), vacuum / thin atmosphere, ionizing radiation, true regolith (Earth soil is weathered, wet, organic), and Moon/Mars resolutions are far worse than Earth's, so features must be compared at a **common coarse scale (~5 km)**.

## 7. Download tiers (sizes are from the live listings)

| Tier | Contents | Total | Login |
|---|---|---|---|
| **T1 — core, small** | LOLA 16 ppd global, LOLA S-polar 80 m, Diviner rock abundance 32 ppd, Diviner CF 32 ppd, MOLA 16 ppd topo | ~0.5 GB | none |
| **T2 — polar detail** | Diviner PRP south (605 MB), LOLA 85S 40 m (230 MB) | ~0.8 GB | none |
| **T3 — Earth core** | MOD11C3 (24 months), MOD13C2 (12 months), MOD10CM, DEM | ~0.2–1 GB | Earthdata |
| **T4 — site zoom** | Higher-res LOLA/MOLA, EMIT/ASTER for 2–3 top Earth sites, one SAR scene | several GB | varies |
