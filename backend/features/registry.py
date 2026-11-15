"""Feature registry: the one module that defines every feature.

Earth, the Moon and Mars all call these functions. A feature is described in
``config/features.yaml`` (id, function name, parameters, units) and executed
here. Grid resolution, window sizes, lags, percentiles and the comparability
thresholds are configuration, never literals in this file.

Two rules make cross-body comparison honest:

* features are computed over the same **physical** windows (kilometres), and
* a feature is only computed where the source data actually resolve its window
  (:func:`availability`), otherwise it is reported as unavailable with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

import numpy as np
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    percentile_filter,
    uniform_filter,
    zoom,
)

from backend.config import ComparabilityConfig, FeatureDefinition


@dataclass(frozen=True)
class Availability:
    """Whether a feature can be computed on a body, and how well resolved it is."""

    available: bool
    reason: str = ""
    marginal: bool = False
    detail: Mapping[str, Any] = field(default_factory=dict)

    @property
    def resolution(self) -> str:
        if not self.available:
            return "unavailable"
        return "marginal" if self.marginal else "resolved"

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "resolution": self.resolution,
            "marginal": self.marginal,
            "reason": self.reason,
            **dict(self.detail),
        }


# --- geometry helpers --------------------------------------------------------


def window_pixels(window_km: float, pixel_m: float) -> int:
    """Window size in whole pixels (at least one)."""
    return max(1, int(np.ceil(window_km * 1000.0 / pixel_m)))


def window_span_px(window_km: float, pixel_m: float) -> float:
    """How many native pixels a physical window spans, before rounding."""
    return window_km * 1000.0 / pixel_m


def lag_pixels(lag_km: float, pixel_m: float) -> int:
    """Lag in whole pixels (at least one)."""
    return max(1, int(round(lag_km * 1000.0 / pixel_m)))


def _nearest_fill(array: np.ndarray) -> np.ndarray:
    """Fill non-finite cells with the nearest finite value (no invention)."""
    array = np.asarray(array, dtype="float32")
    if np.isfinite(array).all():
        return array
    if not np.isfinite(array).any():
        return array
    missing = ~np.isfinite(array)
    indices = distance_transform_edt(missing, return_distances=False, return_indices=True)
    return array[tuple(indices)]


def prepare_dem(dem: np.ndarray, land: np.ndarray | None = None) -> np.ndarray:
    """Fill voids and (optionally) replace ocean cells before any filtering.

    Voids are filled from the nearest valid cell. When a ``land`` mask is given,
    cells outside it are replaced by the nearest *land* elevation, so shelf
    bathymetry cannot inflate coastal relief, slope or roughness. The ocean is
    masked out of the published product later.
    """
    elevation = _nearest_fill(dem)
    if land is None:
        return elevation
    land = np.asarray(land, dtype=bool)
    if not land.any() or land.all():
        return elevation
    ocean = ~land
    indices = distance_transform_edt(ocean, return_distances=False, return_indices=True)
    elevation = elevation.copy()
    elevation[ocean] = elevation[tuple(indices)][ocean]
    return elevation


# --- local statistics --------------------------------------------------------


def local_std(array: np.ndarray, size: int) -> np.ndarray:
    """Standard deviation in a square moving window."""
    mean = uniform_filter(array, size=size, mode="nearest")
    mean_sq = uniform_filter(array * array, size=size, mode="nearest")
    return np.sqrt(np.maximum(mean_sq - mean * mean, 0.0)).astype("float32")


def local_percentile(
    array: np.ndarray,
    size: int,
    quantile: float,
    options: ComparabilityConfig,
) -> np.ndarray:
    """Local percentile in a square window.

    Exact up to ``exact_percentile_max_px``. Above that the DEM is subsampled to
    ``approx_percentile_window_px`` and the filtered result is resampled back,
    which keeps the 80 m lunar DEM tractable. The approximation is recorded in
    the feature attributes and in the Phase 2 report.
    """
    if size <= options.exact_percentile_max_px:
        return percentile_filter(array, quantile, size=size, mode="nearest").astype("float32")

    target = max(2, int(options.approx_percentile_window_px))
    stride = max(1, int(np.ceil(size / target)))
    sub = np.ascontiguousarray(array[::stride, ::stride])
    sub_size = max(1, int(round(size / stride)))
    sub_out = percentile_filter(sub, quantile, size=sub_size, mode="nearest").astype("float32")
    if stride == 1:
        return sub_out

    zoomed = zoom(
        sub_out,
        (array.shape[0] / sub_out.shape[0], array.shape[1] / sub_out.shape[1]),
        order=1,
        mode="nearest",
    )
    out = np.full(array.shape, np.nan, dtype="float32")
    height = min(out.shape[0], zoomed.shape[0])
    width = min(out.shape[1], zoomed.shape[1])
    out[:height, :width] = zoomed[:height, :width]
    return out


# --- feature functions -------------------------------------------------------
# Every function has the signature (dem, pixel_m, params, options) -> array.


def relief(
    dem: np.ndarray,
    pixel_m: float,
    params: Mapping[str, Any],
    options: ComparabilityConfig,
) -> np.ndarray:
    """Local relief: difference between two percentiles of the DEM."""
    size = window_pixels(float(params["window_km"]), pixel_m)
    low = local_percentile(
        dem, size, float(params["low_percentile"]), options
    )
    high = local_percentile(
        dem, size, float(params["high_percentile"]), options
    )
    return (high - low).astype("float32")


def slope(
    dem: np.ndarray,
    pixel_m: float,
    params: Mapping[str, Any],
    options: ComparabilityConfig,
) -> np.ndarray:
    """Mean slope over the window, from gradients at the native pixel size."""
    gradient_y, gradient_x = np.gradient(dem, pixel_m, pixel_m)
    local = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y))).astype("float32")
    size = window_pixels(float(params["window_km"]), pixel_m)
    return uniform_filter(local, size=size, mode="nearest").astype("float32")


def roughness(
    dem: np.ndarray,
    pixel_m: float,
    params: Mapping[str, Any],
    options: ComparabilityConfig,
) -> np.ndarray:
    """Standard deviation of a Gaussian high-pass residual in the window."""
    window_km = float(params["window_km"])
    sigma_fraction = float(params.get("sigma_fraction", 0.5))
    sigma_px = max(0.75, sigma_fraction * window_km * 1000.0 / pixel_m)
    residual = dem - gaussian_filter(dem, sigma=sigma_px, mode="nearest")
    return local_std(residual.astype("float32"), window_pixels(window_km, pixel_m))


def hurst(
    dem: np.ndarray,
    pixel_m: float,
    params: Mapping[str, Any],
    options: ComparabilityConfig,
) -> np.ndarray:
    """Scale-robust roughness from the elevation structure function.

    For fractional Brownian topography ``E[(z(x+L)-z(x))^2] ∝ L^(2H)``, so the
    local log-log slope of the structure function gives ``2H``. A flat surface
    has no scaling and yields NaN.
    """
    configured = [float(lag) for lag in params["lags_km"]]
    usable = [lag for lag in configured if window_span_px(lag, pixel_m) >= 1.0]
    if len(usable) < 2:
        shape = np.asarray(dem).shape
        return np.full(shape, np.nan, dtype="float32")

    size = window_pixels(float(params["window_km"]), pixel_m)
    structure: list[np.ndarray] = []
    for lag_km in usable:
        lag = lag_pixels(lag_km, pixel_m)
        diff_x = np.zeros_like(dem, dtype="float32")
        diff_y = np.zeros_like(dem, dtype="float32")
        valid = np.zeros_like(dem, dtype="float32")
        diff_x[:, lag:] = (dem[:, lag:] - dem[:, :-lag]) ** 2
        diff_y[lag:, :] = (dem[lag:, :] - dem[:-lag, :]) ** 2
        valid[:, lag:] = 1.0
        valid[lag:, :] += 1.0
        numerator = uniform_filter(diff_x + diff_y, size=size, mode="nearest")
        denominator = uniform_filter(valid, size=size, mode="nearest")
        structure.append(
            np.maximum(numerator / np.maximum(denominator, 1e-6), 1e-12)
        )

    log_structure = np.log(np.stack(structure, axis=0))
    log_lags = np.log(np.asarray(usable, dtype="float32"))
    centered = log_lags - log_lags.mean()
    denominator = float(np.sum(centered**2))
    local_slope = np.sum(
        centered[:, None, None] * (log_structure - log_structure.mean(axis=0)), axis=0
    ) / denominator
    return np.clip(0.5 * local_slope, 0.0, 1.5).astype("float32")


def worldclim_average(
    values: np.ndarray,
    pixel_m: float,
    params: Mapping[str, Any],
    options: ComparabilityConfig,
) -> np.ndarray:
    """Pass-through for pre-resampled raster features (WorldClim).

    These features are not window statistics: the climate pipeline resamples the
    source raster to the search grid. The registry still owns their definition
    so Earth, Moon and Mars read the same metadata.
    """
    return np.asarray(values, dtype="float32")


FUNCTIONS: dict[
    str, Callable[[np.ndarray, float, Mapping[str, Any], ComparabilityConfig], np.ndarray]
] = {
    "relief": relief,
    "slope": slope,
    "roughness": roughness,
    "hurst": hurst,
    "worldclim_average": worldclim_average,
}


# --- availability ------------------------------------------------------------


def availability(
    definition: FeatureDefinition,
    pixel_m: float,
    options: ComparabilityConfig,
    native_pixel_m: float | None = None,
) -> Availability:
    """Decide whether this body's native data resolve the feature's window.

    ``pixel_m`` is the grid the feature is computed on; ``native_pixel_m`` is the
    source ground sampling. Resolution is a property of the source data, so the
    checks use ``native_pixel_m`` when it is supplied.
    """
    native = float(native_pixel_m or pixel_m)
    if definition.function == "worldclim_average":
        return Availability(True, "resampled from the configured source raster")

    if definition.function == "hurst":
        lags = definition.lags_km
        resolved = [
            lag for lag in lags if window_span_px(lag, native) >= options.min_lag_pixels
        ]
        if len(resolved) < options.min_hurst_lags:
            listed = ", ".join(f"{lag:g}" for lag in lags)
            return Availability(
                False,
                (
                    f"Hurst needs at least {options.min_hurst_lags} lags spanning "
                    f"{options.min_lag_pixels:g} native pixels or more; at "
                    f"{native / 1000:.2f} km per pixel only {len(resolved)} of "
                    f"{len(lags)} configured lags ({listed} km) qualify."
                ),
                detail={"resolved_lags_km": resolved, "configured_lags_km": list(lags)},
            )
        return Availability(True, detail={"resolved_lags_km": resolved})

    window_km = definition.window_km
    if window_km is not None:
        span = window_span_px(window_km, native)
        if span < options.min_window_pixels:
            return Availability(
                False,
                (
                    f"{window_km:g} km window spans {span:.2f} native pixels at "
                    f"{native / 1000:.2f} km per pixel; at least "
                    f"{options.min_window_pixels:g} are required."
                ),
                detail={"window_span_px": round(span, 3)},
            )
        marginal = span < options.marginal_window_pixels
        return Availability(
            True,
            (
                f"{window_km:g} km window spans only {span:.2f} native pixels at "
                f"{native / 1000:.2f} km per pixel; computed but flagged marginal."
                if marginal
                else ""
            ),
            marginal=marginal,
            detail={"window_span_px": round(span, 3)},
        )

    return Availability(True)


def compute(
    definition: FeatureDefinition,
    dem: np.ndarray,
    pixel_m: float,
    options: ComparabilityConfig,
) -> np.ndarray:
    """Run one registered feature on a prepared DEM."""
    try:
        function = FUNCTIONS[definition.function]
    except KeyError as exc:
        raise KeyError(
            f"feature {definition.id!r} uses unknown registry function "
            f"{definition.function!r}; known: {sorted(FUNCTIONS)}"
        ) from exc
    return function(dem, pixel_m, definition.params, options)


def compute_all(
    definitions: tuple[FeatureDefinition, ...],
    dem: np.ndarray,
    pixel_m: float,
    options: ComparabilityConfig,
    land: np.ndarray | None = None,
    native_pixel_m: float | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, Availability]]:
    """Compute every resolvable feature and report the rest as unavailable."""
    prepared = prepare_dem(dem, land=land)
    arrays: dict[str, np.ndarray] = {}
    status: dict[str, Availability] = {}
    for definition in definitions:
        verdict = availability(definition, pixel_m, options, native_pixel_m)
        status[definition.id] = verdict
        if verdict.available:
            arrays[definition.id] = compute(definition, prepared, pixel_m, options)
    return arrays, status


def attributes(definition: FeatureDefinition) -> dict[str, Any]:
    """NetCDF attributes for one feature, derived from its config entry."""
    attrs: dict[str, Any] = {
        "long_name": definition.long_name,
        "units": definition.units,
        "definition": definition.definition,
        "feature_group": definition.group,
        "registry_function": definition.function,
    }
    if definition.role:
        attrs["role"] = definition.role
    return attrs
