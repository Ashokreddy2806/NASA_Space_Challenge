"""Label the downloaded data and upload it to a Hugging Face dataset repo.

Usage:
    python -m backend.pipeline.publish_hf --repo ORG/NAME            # writes labels, dry run
    python -m backend.pipeline.publish_hf --repo ORG/NAME --upload   # uploads (needs `hf auth login`)
    add --public to create a public repo (default: private)
"""
import argparse
import subprocess

from backend.paths import RAW

ROOT = RAW["moon"].parent  # shared Datasets folder (Moon/ Mars/ Earth/)

# file -> (title, body, instrument, what it is, units / scaling, source folder)
LABELS = {
    "Moon/pds/lola/ldem_16_float.img": ("LOLA global DEM, 16 ppd (PDS)", "Moon", "LRO LOLA", "Global elevation, cylindrical, ~1.9 km/px", "float32 LE, metres vs 1737.4 km sphere"),
    "Moon/pds/lola/ldem_80s_80m_float.img": ("LOLA south-polar DEM, 80 m/px", "Moon", "LRO LOLA", "Elevation 80S-90S, polar stereographic", "float32 LE, metres vs 1737.4 km sphere"),
    "Moon/pds/lola/ldem_85s_40m_float.img": ("LOLA south-polar DEM, 40 m/px", "Moon", "LRO LOLA", "Elevation 85S-90S, polar stereographic", "float32 LE, metres vs 1737.4 km sphere"),
    "Moon/pds/diviner/dgdr_ra_avg_cyl_032_img.img": ("Diviner rock abundance, 32 ppd", "Moon", "LRO Diviner", "Fraction of surface covered by rocks (roughness proxy)", "int16 LE, value = DN*0.001, missing -32768"),
    "Moon/pds/diviner/dgdr_nen_cf_clc_cyl_032_img.img": ("Diviner Christiansen feature, 32 ppd", "Moon", "LRO Diviner", "Mid-IR emissivity peak position (silicate mineralogy)", "see .lbl for scaling"),
    "Moon/pds/diviner/dlre_prp_south.tab": ("Diviner south-polar resource product", "Moon", "LRO Diviner", "ASCII table, 2.88 M rows x 15 cols: polar temperatures and ice-stability data", "see .lbl and DLRE_PRP.FMT"),
    "Mars/megt90n000eb.img": ("MOLA global topography, 16 ppd", "Mars", "MGS MOLA", "Global elevation, cylindrical, ~3.7 km/px", "int16 big-endian, metres vs MOLA areoid"),
    "Moon/LDEM_80S_80MPP_ADJ.tiff": ("LOLA south-polar DEM, 80 m/px (GSFC PGDA)", "Moon", "LRO LOLA", "Cloud-optimized GeoTIFF, 80S-90S, polar stereographic", "metres"),
    "Moon/LDRM_80S_1000MPP_ADJ_ROUGH_800M.tiff": ("LOLA roughness, 800 m baseline", "Moon", "LRO LOLA", "1 km/px roughness map", "metres"),
    "Moon/LDRM_80S_1000MPP_ADJ_ROUGH_1600M.tiff": ("LOLA roughness, 1600 m baseline", "Moon", "LRO LOLA", "1 km/px roughness map", "metres"),
    "Moon/LDRM_80S_1000MPP_ADJ_SLP_800M.tiff": ("LOLA slope, 800 m baseline", "Moon", "LRO LOLA", "1 km/px slope map", "degrees"),
    "Moon/LDRM_80S_1000MPP_ADJ_SLP_1600M.tiff": ("LOLA slope, 1600 m baseline", "Moon", "LRO LOLA", "1 km/px slope map", "degrees"),
    "Moon/LDRM_80S_1000MPP_ADJ_H.tiff": ("LOLA Hurst exponent", "Moon", "LRO LOLA", "How roughness changes with scale", "unitless"),
    "Moon/LDRM_80S_1000MPP_ADJ_SPSLP.tiff": ("LOLA roughness spectral slope", "Moon", "LRO LOLA", "Scale-robust roughness", "sigma/km"),
    "Moon/LPSR_80S_20MPP_ADJ_1km2.csv": ("Permanently shadowed regions > 1 km2", "Moon", "LRO LOLA", "Cold-trap / ice proxy table", "see columns"),
    "Moon/ldem_16.tif": ("LOLA global DEM, 16 ppd (SVS)", "Moon", "LRO LOLA", "Global context only, distorted near poles", "km"),
    "Mars/mars_elev.npy": ("MOLA 16 ppd elevation as NumPy array", "Mars", "MGS MOLA", "2880x5760 int16, converted from megt90n000eb.img", "metres"),
    "Earth/ETOPO_2022_v1_60s_N90W180_surface.tif": ("ETOPO 2022 surface elevation, 60 arcsec", "Earth", "NOAA NCEI", "Global GeoTIFF incl. poles, ~1.85 km", "metres"),
    "Earth/wc2.1_2.5m_bio_1.tif": ("WorldClim 2.1 bio_1, 2.5 arcmin", "Earth", "WorldClim", "annual mean temp (air temperature/precipitation, 1970-2000)", "deg C"),
    "Earth/wc2.1_2.5m_bio_2.tif": ("WorldClim 2.1 bio_2, 2.5 arcmin", "Earth", "WorldClim", "mean diurnal range (air temperature/precipitation, 1970-2000)", "deg C"),
    "Earth/wc2.1_2.5m_bio_5.tif": ("WorldClim 2.1 bio_5, 2.5 arcmin", "Earth", "WorldClim", "max temp warmest month (air temperature/precipitation, 1970-2000)", "deg C"),
    "Earth/wc2.1_2.5m_bio_6.tif": ("WorldClim 2.1 bio_6, 2.5 arcmin", "Earth", "WorldClim", "min temp coldest month (air temperature/precipitation, 1970-2000)", "deg C"),
    "Earth/wc2.1_2.5m_bio_7.tif": ("WorldClim 2.1 bio_7, 2.5 arcmin", "Earth", "WorldClim", "annual temp range (air temperature/precipitation, 1970-2000)", "deg C"),
    "Earth/wc2.1_2.5m_bio_12.tif": ("WorldClim 2.1 bio_12, 2.5 arcmin", "Earth", "WorldClim", "annual precipitation (air temperature/precipitation, 1970-2000)", "mm"),
    "Earth/wc2.1_2.5m_bio_14.tif": ("WorldClim 2.1 bio_14, 2.5 arcmin", "Earth", "WorldClim", "precipitation of driest month (air temperature/precipitation, 1970-2000)", "mm"),
}


def write_card(repo):
    rows = "\n".join(
        f"| `{f}` | {t} | {b} | {i} | {d} | {u} |" for f, (t, b, i, d, u) in LABELS.items() if (ROOT / f).exists()
    )
    card = f"""---
license: other
pretty_name: NASA Space Apps analog-site data (raw PDS products)
tags: [nasa, moon, mars, earth, lro, mola, worldclim, etopo]
---

# Raw Moon, Mars and Earth data for the NASA Space Apps analog-site challenge

Source files for our team, mostly unmodified. Moon/Mars: NASA PDS Geosciences Node and NASA GSFC PGDA (public domain);
`mars_elev.npy` is MOLA converted to NumPy. Earth: NOAA ETOPO 2022 (public domain) and WorldClim 2.1 (Fick & Hijmans 2017,
free for non-commercial use). Layout: `Moon/`, `Mars/`, `Earth/` (same as the team's local `Datasets/` folder; PDS extras under `Moon/pds/`). Each PDS data file has its `.lbl` label next to it: read it for shape, byte order and scaling.
See the project repo `docs/DATASETS.md` for links and citations.

| File | Product | Body | Instrument | What it is | Format / units |
|---|---|---|---|---|---|
{rows}

Sources: https://pds-geosciences.wustl.edu/ , https://pgda.gsfc.nasa.gov/ , https://www.ncei.noaa.gov/products/etopo-global-relief-model , https://worldclim.org/ .
"""
    (ROOT / "README.md").write_text(card)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--upload", action="store_true")
    p.add_argument("--public", action="store_true")
    a = p.parse_args()

    write_card(a.repo)
    files = sorted(x.relative_to(ROOT) for x in ROOT.rglob("*") if x.is_file() and not x.name.endswith(".part"))
    print(f"{len(files)} files in {ROOT}; dataset card at {ROOT / 'README.md'}")
    if not a.upload:
        print("Dry run. Add --upload to publish to", a.repo)
        return
    create = ["hf", "repos", "create", a.repo, "--repo-type", "dataset", "--exist-ok"]
    if not a.public:
        create.append("--private")
    subprocess.run(create, check=True)
    subprocess.run(["hf", "upload-large-folder", a.repo, str(ROOT), "--repo-type", "dataset"], check=True)


if __name__ == "__main__":
    main()
