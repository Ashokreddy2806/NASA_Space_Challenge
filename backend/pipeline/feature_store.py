"""Chunked NetCDF feature store for the Phase 1 Earth grid.

Zarr could not be imported on this machine because the ``numcodecs`` Jenkins
extension is blocked by Windows Application Control. NetCDF4/HDF5 works and
provides the same chunked, compressed storage, so the pipeline uses one NetCDF
file per dataset and a final merged NetCDF file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from netCDF4 import Dataset

from backend.pipeline.earth_grid import NX, NY, lat_centers, lon_centers

CHUNK_ROWS = 360  # 10° at 0.05°
CHUNK_COLS = 720


class GridStore:
    """Thin wrapper around a NetCDF4 dataset with the common lat/lon grid."""

    def __init__(self, path: Path, mode: str = "w") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.dataset = Dataset(str(self.path), mode, format="NETCDF4")
        if mode == "w":
            self.dataset.createDimension("lat", NY)
            self.dataset.createDimension("lon", NX)
            lat = self.dataset.createVariable("lat", "f8", ("lat",))
            lat[:] = lat_centers()
            lat.units = "degrees_north"
            lat.standard_name = "latitude"
            lon = self.dataset.createVariable("lon", "f8", ("lon",))
            lon[:] = lon_centers()
            lon.units = "degrees_east"
            lon.standard_name = "longitude"
        elif mode == "a":
            if "lat" not in self.dataset.dimensions:
                raise ValueError(f"{self.path} is not a gridded feature store")

    def create_feature(
        self,
        name: str,
        attrs: dict[str, Any],
        fill_value: float | bool = np.nan,
        dtype: str = "f4",
    ):
        """Create one compressed (lat, lon) variable."""
        variable = self.dataset.createVariable(
            name,
            dtype,
            ("lat", "lon"),
            zlib=True,
            complevel=4,
            shuffle=True,
            chunksizes=(CHUNK_ROWS, CHUNK_COLS),
            fill_value=fill_value,
        )
        for key, value in attrs.items():
            setattr(variable, key, value)
        return variable

    def set_attrs(self, attrs: dict[str, Any]) -> None:
        """Set global attributes."""
        for key, value in attrs.items():
            setattr(self.dataset, key, value)

    def close(self) -> None:
        """Flush and close the file."""
        self.dataset.close()

    def __enter__(self) -> "GridStore":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
