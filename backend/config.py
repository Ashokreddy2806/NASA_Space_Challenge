"""Configuration loading for the whole backend.

Every grid size, window, lag, percentile, file name, target coordinate and
validation site is defined in ``config/*.yaml``. Code asks this module for the
values instead of repeating literals. A proof or alternate run can deep-merge an
override file with ``load_config(override=...)`` or ``NASA_CONFIG_OVERRIDE``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Mapping

import yaml

from backend.paths import PROJECT_ROOT, RAW


def _deep_merge(base: dict[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (lists replace, dicts merge)."""
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), Mapping):
            base[key] = _deep_merge(dict(base[key]), value)
        else:
            base[key] = value
    return base


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a mapping at the top level")
    return data


def _abs(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class GridSpec:
    """Regular lon/lat search grid and its tiling / working-grid settings."""

    resolution_deg: float
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float
    tile_deg: float
    halo_deg: float
    working_pixel_m: float
    chunk_rows: int
    chunk_cols: int

    @property
    def nx(self) -> int:
        return int(round((self.lon_max - self.lon_min) / self.resolution_deg))

    @property
    def ny(self) -> int:
        return int(round((self.lat_max - self.lat_min) / self.resolution_deg))

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        return (self.lon_min, self.lat_min, self.lon_max, self.lat_max)

    def validate(self) -> None:
        if not (-180.0 <= self.lon_min < self.lon_max <= 180.0):
            raise ValueError(f"invalid longitude bounds: {self.lon_min}..{self.lon_max}")
        if not (-90.0 <= self.lat_min < self.lat_max <= 90.0):
            raise ValueError(f"invalid latitude bounds: {self.lat_min}..{self.lat_max}")
        for name in ("resolution_deg", "tile_deg", "halo_deg", "working_pixel_m"):
            if getattr(self, name) <= 0:
                raise ValueError(f"grid.{name} must be positive")
        lon_span = self.lon_max - self.lon_min
        lat_span = self.lat_max - self.lat_min
        if abs(lon_span / self.resolution_deg - self.nx) > 1e-6:
            raise ValueError("longitude span must be a whole number of grid cells")
        if abs(lat_span / self.resolution_deg - self.ny) > 1e-6:
            raise ValueError("latitude span must be a whole number of grid cells")


@dataclass(frozen=True)
class ComparabilityConfig:
    """Rules that decide whether a feature is resolvable on a body."""

    min_window_pixels: float
    marginal_window_pixels: float
    min_hurst_lags: int
    min_lag_pixels: float
    exact_percentile_max_px: int
    approx_percentile_window_px: int


@dataclass(frozen=True)
class EarthConfig:
    """Earth-specific choices that are still data-driven."""

    land_mask_source: str
    land_mask_threshold: float
    native_pixel_m: float


@dataclass(frozen=True)
class FigureConfig:
    stride_cells: int
    dpi_single: int
    dpi_overview: int
    percentile_stretch: tuple[float, float]
    overview_columns: int


@dataclass(frozen=True)
class StorageConfig:
    compression_level: int


@dataclass(frozen=True)
class ReportConfig:
    polar_circle_deg: float
    plot_xticks: tuple[float, ...]
    plot_yticks: tuple[float, ...]


@dataclass(frozen=True)
class DistributionConfig:
    sample_stride_px: int
    percentiles: tuple[float, float]


@dataclass(frozen=True)
class HurstSensitivityConfig:
    sample_count: int
    random_seed: int
    patch_km: float
    drop_lag_km: float
    robust_max_median_difference: float
    robust_min_correlation: float


@dataclass(frozen=True)
class FeatureDefinition:
    """One registered feature: a function plus its configured parameters."""

    id: str
    group: str
    function: str
    params: Mapping[str, Any]
    units: str
    long_name: str
    label: str
    definition: str
    cmap: str
    role: str | None = None

    @property
    def window_km(self) -> float | None:
        value = self.params.get("window_km")
        return float(value) if value is not None else None

    @property
    def lags_km(self) -> tuple[float, ...]:
        return tuple(float(lag) for lag in self.params.get("lags_km", ()))


@dataclass(frozen=True)
class GroupDefinition:
    name: str
    weight: float
    members: tuple[str, ...]


@dataclass(frozen=True)
class OutputPaths:
    """Resolved output locations and figure settings."""

    processed_dir: Path
    docs_dir: Path
    figures_dir: Path
    proofs_dir: Path
    names: Mapping[str, str]
    figure_prefix: str
    overview_figure: str

    def path(self, key: str) -> Path:
        try:
            name = self.names[key]
        except KeyError as exc:
            raise KeyError(f"unknown output key {key!r}") from exc
        if key.endswith("_report") or key in {
            "phase2_report",
            "psr_report",
            "hurst_sensitivity",
            "hardcode_audit",
            "data_inventory",
        }:
            return self.docs_dir / name
        return self.processed_dir / name


@dataclass(frozen=True)
class ValidationSite:
    name: str
    lat: float
    lon: float
    notes: str = ""
    expect: Mapping[str, Mapping[str, float]] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    grid: GridSpec
    earth: EarthConfig
    comparability: ComparabilityConfig
    distribution: DistributionConfig
    hurst_sensitivity: HurstSensitivityConfig
    figures: FigureConfig
    report: ReportConfig
    storage: StorageConfig
    terrain_features: tuple[FeatureDefinition, ...]
    climate_features: tuple[FeatureDefinition, ...]
    groups: tuple[GroupDefinition, ...]
    sources: Mapping[str, Mapping[str, Any]]
    outputs: OutputPaths
    targets: Mapping[str, Any]
    validation_sites: tuple[ValidationSite, ...]

    @property
    def all_features(self) -> tuple[FeatureDefinition, ...]:
        return self.terrain_features + self.climate_features

    def raw_source(self, body: str, key: str) -> Path:
        """Resolve a configured source file for a body (Earth/Moon/Mars)."""
        return RAW[body] / self.source_name(body, key)

    def source_name(self, body: str, key: str) -> str:
        """Configured file name for a body source (Earth/Moon/Mars)."""
        try:
            name = self.sources[body][key]
        except KeyError as exc:
            raise KeyError(f"unknown source {body}.{key}") from exc
        if isinstance(name, Mapping):
            raise TypeError(f"source {body}.{key} is a group; specify a child key")
        return str(name)

    def output(self, key: str) -> Path:
        return self.outputs.path(key)


_DEFAULT_CONFIG_FILES = (
    "config.yaml",
    "features.yaml",
    "paths.yaml",
    "targets.yaml",
    "validation_sites.yaml",
)


def _build_feature(raw: Mapping[str, Any]) -> FeatureDefinition:
    return FeatureDefinition(
        id=str(raw["id"]),
        group=str(raw.get("group", "")),
        function=str(raw["function"]),
        params=dict(raw.get("params") or {}),
        units=str(raw.get("units", "")),
        long_name=str(raw.get("long_name", raw["id"])),
        label=str(raw.get("label", raw.get("long_name", raw["id"]))),
        definition=str(raw.get("definition", "")),
        cmap=str(raw.get("cmap", "viridis")),
        role=raw.get("role"),
    )


def _patch_feature(
    feature: FeatureDefinition, patch: Mapping[str, Any] | None
) -> FeatureDefinition:
    """Apply an ``overrides:`` entry from a proof config to one feature."""
    if not patch:
        return feature
    params = dict(feature.params)
    params.update(patch.get("params") or {})
    return replace(
        feature,
        params=params,
        units=str(patch.get("units", feature.units)),
        long_name=str(patch.get("long_name", feature.long_name)),
        label=str(patch.get("label", feature.label)),
        definition=str(patch.get("definition", feature.definition)),
        cmap=str(patch.get("cmap", feature.cmap)),
    )


def load_config(
    override: str | Path | None = None,
    config_dir: str | Path | None = None,
) -> AppConfig:
    """Load and validate the YAML configuration.

    ``override`` is a YAML file deep-merged over the five base files. It can also
    be supplied through ``NASA_CONFIG_OVERRIDE``; ``config_dir`` defaults to
    ``NASA_CONFIG_DIR`` or ``<project>/config``.
    """
    base_dir = Path(config_dir or os.environ.get("NASA_CONFIG_DIR", PROJECT_ROOT / "config"))
    merged: dict[str, Any] = {}
    for name in _DEFAULT_CONFIG_FILES:
        path = base_dir / name
        if not path.exists():
            raise FileNotFoundError(f"missing configuration file: {path}")
        merged[name] = _read_yaml(path)

    override_value = override or os.environ.get("NASA_CONFIG_OVERRIDE")
    if override_value:
        override_path = Path(override_value)
        if not override_path.is_absolute():
            override_path = PROJECT_ROOT / override_path
        if not override_path.exists():
            raise FileNotFoundError(f"configuration override not found: {override_path}")
        merged = _deep_merge(merged, _read_yaml(override_path))

    grid = GridSpec(**merged["config.yaml"]["grid"])
    grid.validate()
    config_raw = merged["config.yaml"]
    comparability = ComparabilityConfig(**config_raw["comparability"])
    earth = EarthConfig(**config_raw["earth"])
    distribution_raw = config_raw["distribution"]
    distribution = DistributionConfig(
        sample_stride_px=int(distribution_raw["sample_stride_px"]),
        percentiles=tuple(float(v) for v in distribution_raw["percentiles"]),
    )
    hurst = HurstSensitivityConfig(**config_raw["hurst_sensitivity"])
    figures_raw = config_raw["figures"]
    figures = FigureConfig(
        stride_cells=int(figures_raw["stride_cells"]),
        dpi_single=int(figures_raw["dpi_single"]),
        dpi_overview=int(figures_raw["dpi_overview"]),
        percentile_stretch=tuple(float(v) for v in figures_raw["percentile_stretch"]),
        overview_columns=int(figures_raw["overview_columns"]),
    )
    storage = StorageConfig(compression_level=int(config_raw["storage"]["compression_level"]))
    report_raw = config_raw["report"]
    report = ReportConfig(
        polar_circle_deg=float(report_raw["polar_circle_deg"]),
        plot_xticks=tuple(float(v) for v in report_raw["plot_xticks"]),
        plot_yticks=tuple(float(v) for v in report_raw["plot_yticks"]),
    )

    features_raw = merged["features.yaml"]
    patches = features_raw.get("overrides", {}) or {}
    unknown_patch = set(patches) - {str(raw["id"]) for raw in features_raw.get("terrain", []) + features_raw.get("climate", [])}
    if unknown_patch:
        raise ValueError(f"feature overrides reference unknown ids: {sorted(unknown_patch)}")
    terrain = tuple(
        _patch_feature(_build_feature(raw), patches.get(str(raw["id"])))
        for raw in features_raw.get("terrain", [])
    )
    climate = tuple(
        _patch_feature(_build_feature(raw), patches.get(str(raw["id"])))
        for raw in features_raw.get("climate", [])
    )
    groups = tuple(
        GroupDefinition(
            name=name,
            weight=float(raw.get("weight", 1.0)),
            members=tuple(raw.get("members", ())),
        )
        for name, raw in features_raw.get("groups", {}).items()
    )
    known = {feature.id for feature in terrain + climate}
    for group in groups:
        for member in group.members:
            if member not in known:
                raise ValueError(f"group {group.name} references unknown feature {member}")

    paths_raw = merged["paths.yaml"]
    outputs_raw = paths_raw["outputs"]
    processed_dir = _abs(outputs_raw["processed_dir"])
    docs_dir = _abs(outputs_raw["docs_dir"])
    outputs = OutputPaths(
        processed_dir=processed_dir,
        docs_dir=docs_dir,
        figures_dir=docs_dir / outputs_raw["figures_subdir"],
        proofs_dir=processed_dir / outputs_raw["proofs_subdir"],
        names={
            key: str(value)
            for key, value in outputs_raw.items()
            if key
            not in {
                "processed_dir",
                "docs_dir",
                "figures_subdir",
                "proofs_subdir",
                "earth_figure_prefix",
                "overview_figure",
            }
        },
        figure_prefix=str(outputs_raw["earth_figure_prefix"]),
        overview_figure=str(outputs_raw["overview_figure"]),
    )

    targets = merged["targets.yaml"]
    for body, target in targets.items():
        if "body" in target and target["body"] != body:
            raise ValueError(f"target {body} declares body {target['body']}")

    sites_raw = merged["validation_sites.yaml"].get("sites", [])
    sites = tuple(
        ValidationSite(
            name=str(raw["name"]),
            lat=float(raw["lat"]),
            lon=float(raw["lon"]),
            notes=str(raw.get("notes", "")),
            expect=raw.get("expect", {}) or {},
        )
        for raw in sites_raw
    )

    return AppConfig(
        grid=grid,
        earth=earth,
        comparability=comparability,
        distribution=distribution,
        hurst_sensitivity=hurst,
        figures=figures,
        report=report,
        storage=storage,
        terrain_features=terrain,
        climate_features=climate,
        groups=groups,
        sources=paths_raw["sources"],
        outputs=outputs,
        targets=targets,
        validation_sites=sites,
    )
