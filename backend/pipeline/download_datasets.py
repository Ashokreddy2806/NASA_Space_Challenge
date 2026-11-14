"""Download everything listed in docs/DATASETS.md into the shared Datasets/{Moon,Mars,Earth} folder (backend/paths.py).

Usage (repo root): python -m backend.pipeline.download_datasets
Reuses fetch() from download.py. Skips files that already exist.
"""
import sys
import zipfile
from array import array

from backend.paths import RAW
from backend.pipeline.download import PDS, fetch

PGDA = "https://pgda.gsfc.nasa.gov/data/LOLA_20mpp"
MOON = [
    f"{PGDA}/LDEM_80S_80MPP_ADJ.TIF",
    *[f"{PGDA}/LDRM_80S_1000MPP_ADJ_{n}.TIF" for n in ("ROUGH_800M", "ROUGH_1600M", "SLP_800M", "SLP_1600M", "H", "SPSLP")],
    f"{PGDA}/LPSR_80S_20MPP_ADJ_1km2.CSV",
    "https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_16.tif",  # optional, global context only
]
MOLA_IMG = f"{PDS}/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg016/megt90n000eb.img"
WORLDCLIM = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base/wc2.1_2.5m_bio.zip"
BIO_KEEP = (1, 2, 5, 6, 7, 12, 14)
ETOPO = "https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/60s/60s_surface_elev_gtif/ETOPO_2022_v1_60s_N90W180_surface.tif"


def mars() -> None:
    """MOLA 16 ppd: int16 big-endian, 2880 x 5760 -> mars_elev.npy (little-endian int16, metres)."""
    out = RAW["mars"] / "mars_elev.npy"
    if out.exists():
        return
    img = RAW["mars"] / "megt90n000eb.img"
    fetch(MOLA_IMG, img)
    a = array("h")
    a.frombytes(img.read_bytes())
    if sys.byteorder == "little":
        a.byteswap()  # file is big-endian
    header = "{'descr': '<i2', 'fortran_order': False, 'shape': (2880, 5760), }"
    header += " " * (63 - (10 + len(header)) % 64) + "\n"  # pad so data starts on a 64-byte boundary
    with open(out, "wb") as f:  # minimal .npy v1.0 writer (no numpy needed)
        f.write(b"\x93NUMPY\x01\x00" + len(header).to_bytes(2, "little") + header.encode())
        f.write(a.tobytes())


def earth() -> None:
    """WorldClim 2.5 min: keep only the bio layers we use; delete the zip afterwards."""
    d = RAW["earth"]
    zpath = d / "wc2.1_2.5m_bio.zip"
    if not all((d / f"wc2.1_2.5m_bio_{n}.tif").exists() for n in BIO_KEEP):
        fetch(WORLDCLIM, zpath)
        with zipfile.ZipFile(zpath) as z:
            for n in BIO_KEEP:
                z.extract(f"wc2.1_2.5m_bio_{n}.tif", d)
        zpath.unlink()
    fetch(ETOPO, d / ETOPO.rsplit("/", 1)[1])


def main() -> None:
    for url in MOON:
        name = url.rsplit("/", 1)[1]
        name = name[:-4] + ".tiff" if name.endswith(".TIF") else name  # team naming (docs/data_inventory.md)
        name = name[:-4] + ".csv" if name.endswith(".CSV") else name
        fetch(url, RAW["moon"] / name)
    mars()
    earth()
    print("done")


if __name__ == "__main__":
    main()
