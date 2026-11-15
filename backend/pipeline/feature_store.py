"""Chunked NetCDF feature store for the search grid.

Zarr could not be imported on this machine because the ``numcodecs`` Jenkins
extension is blocked by Windows Application Control. NetCDF4/HDF5 works and
provides the same chunked, compressed storage, so the pipeline uses one NetCDF
file per dataset and a final merged NetCDF file.

Chunk shapes and the grid geometry come from ``config/config.yaml``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from netCDF4 import Dataset

from backend.config import GridSpec
from backend.pipeline.earth_grid import lat_centers, lon_centers


class GridStore:
    """Thin wrapper around a NetCDF4 dataset with the common search grid."""

    def __init__(
        self,
        path: Path,
        spec: GridSpec,
        mode: str = "w",
        compression_level: int = 4,
    ) -> None:
        self.path = Path(path)
        self.spec = spec
        self.compression_level = compression_level
        self.dataset = Dataset(str(self.path), mode, format="NETCDF4")
        if mode == "w":
            self.dataset.createDimension("lat", spec.ny)
            self.dataset.createDimension("lon", spec.nx)
            lat = self.dataset.createVariable("lat", "f8", ("lat",))
            lat[:] = lat_centers(spec)
            lat.units = "degrees_north"
            lat.standard_name = "latitude"
            lon = self.dataset.createVariable("lon", "f8", ("lon",))
            lon[:] = lon_centers(spec)
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
            complevel=self.compression_level,
            shuffle=True,
            chunksizes=(self.spec.chunk_rows, self.spec.chunk_cols),
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
