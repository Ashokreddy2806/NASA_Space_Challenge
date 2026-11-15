"""Download raw data from the open PDS portals into the shared Datasets folder (see backend/paths.py).

Usage (from the repo root):
    python -m backend.pipeline.download --list          # show products, sizes
    python -m backend.pipeline.download T1              # download a tier (no login)
    python -m backend.pipeline.download T1 T2 --yes     # skip the confirm prompt

Only open (no-login) products are handled here. Earthdata products need a
login in ~/.netrc and are fetched separately (see docs/DATA_CATALOG.md).
"""
import argparse
import shutil
import sys
import urllib.request

from backend.paths import RAW

PDS = "https://pds-geosciences.wustl.edu"
LOLA = f"{PDS}/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr"
DIV_DERIVED = f"{PDS}/lro/urn-nasa-pds-lro_diviner_derived1"
DIV_PRP = f"{PDS}/lro/lro-l-dlre-4-rdr-v1/lrodlr_1001/data/prp"
MOLA = f"{PDS}/mgs/mgs-m-mola-5-megdr-l3-v1/mgsl_300x/meg016"

# (tier, subfolder, url); a .lbl label sits next to each .img/.tab and is fetched too
PRODUCTS = [
    ("T1", "moon/pds/lola", f"{LOLA}/cylindrical/float_img/ldem_16_float.img"),
    ("T1", "moon/pds/lola", f"{LOLA}/polar/float_img/ldem_80s_80m_float.img"),
    ("T1", "moon/pds/diviner", f"{DIV_DERIVED}/data_derived_gdr_l3/cylindrical/img/dgdr_ra_avg_cyl_032_img.img"),
    ("T1", "moon/pds/diviner", f"{DIV_DERIVED}/data_derived_gdr_l3/cylindrical/img/dgdr_nen_cf_clc_cyl_032_img.img"),
    ("T1", "mars", f"{MOLA}/megt90n000eb.img"),
    ("T2", "moon/pds/diviner", f"{DIV_PRP}/dlre_prp_south.tab"),
    ("T2", "moon/pds/lola", f"{LOLA}/polar/float_img/ldem_85s_40m_float.img"),
]


def label_url(url):
    return url.rsplit(".", 1)[0] + ".lbl"


def remote_size(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as r:
        return int(r.headers["Content-Length"])


def fetch(url, dest):
    if dest.exists():
        print(f"  skip (exists) {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"  get {dest.name}")
    with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as f:
        shutil.copyfileobj(r, f, 1 << 20)
    tmp.rename(dest)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("tiers", nargs="*", help="T1 T2 ...")
    p.add_argument("--list", action="store_true")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args()

    chosen = [x for x in PRODUCTS if a.list or x[0] in a.tiers]
    if not chosen:
        sys.exit("Nothing selected. Use --list or pass a tier like T1.")

    total = 0
    for tier, sub, url in chosen:
        size = remote_size(url)
        total += size
        print(f"{tier}  {size / 1e6:8.1f} MB  {sub}/{url.rsplit('/', 1)[1]}")
    print(f"Total: {total / 1e6:.0f} MB -> {RAW['moon'].parent}")
    if a.list:
        return
    if not a.yes and input("Download? [y/N] ").lower() != "y":
        sys.exit("Cancelled.")

    for _, sub, url in chosen:
        name = url.rsplit("/", 1)[1]
        fetch(url, RAW[sub.split('/')[0]] / '/'.join(sub.split('/')[1:]) / name)
        fetch(label_url(url), RAW[sub.split('/')[0]] / '/'.join(sub.split('/')[1:]) / (name.rsplit(".", 1)[0] + ".lbl"))


if __name__ == "__main__":
    main()
