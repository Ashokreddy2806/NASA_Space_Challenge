import numpy as np
import pandas as pd

COLUMNS = [
    "tri1_x", "tri1_y", "tri1_z", "tri2_x", "tri2_y", "tri2_z", "tri3_x", "tri3_y", "tri3_z",
    "tri_clon", "tri_clat", "tri_calt", "temp_avg", "temp_max", "ice_depth",
]
COLD_TRAP_K = 110.0
KELVIN_OFFSET = 273.15


def weighted_summary(values, weights) -> dict:
    order = np.argsort(values)
    v = values[order]
    cw = np.cumsum(weights[order]) / weights.sum()
    return {name: float(v[np.searchsorted(cw, p)])
            for name, p in (("p10", 0.1), ("median", 0.5), ("p90", 0.9))}


def diviner_south_profile(path, lat_limit=-85.0) -> dict:
    df = pd.read_csv(path, header=None, names=COLUMNS, skiprows=1)
    df = df[df["tri_clat"] <= lat_limit]
    v1, v2, v3 = (df[[f"tri{i}_{axis}" for axis in "xyz"]].to_numpy() for i in (1, 2, 3))
    area = 0.5 * np.linalg.norm(np.cross(v2 - v1, v3 - v1), axis=1)
    total = area.sum()
    return {
        "n_triangles": int(len(df)),
        "area_km2": float(total),
        "temp_avg_c": weighted_summary(df["temp_avg"].to_numpy() - KELVIN_OFFSET, area),
        "temp_max_c": weighted_summary(df["temp_max"].to_numpy() - KELVIN_OFFSET, area),
        "cold_trap_area_fraction": float(area[df["temp_max"].to_numpy() < COLD_TRAP_K].sum() / total),
    }
