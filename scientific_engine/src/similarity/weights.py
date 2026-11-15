"""Weight management module.

Manages preset configurations and dynamically re-normalizes weights
when features are missing or flagged unavailable.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Set

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.data.loading import load_yaml_config

CONFIG_PATH = ENGINE_DIR / "config" / "weights.yaml"


class WeightManager:
    """Manages preset weights and dynamic re-weighting."""

    def __init__(self, config_path: Optional[Path] = None):
        cfg_file = config_path or CONFIG_PATH
        self.config = load_yaml_config(cfg_file) if cfg_file.exists() else {}
        self.presets: Dict[str, Dict[str, float]] = {}

        raw_presets = self.config.get("presets", {})
        for name, data in raw_presets.items():
            if isinstance(data, dict) and "weights" in data:
                self.presets[name] = data["weights"]
            elif isinstance(data, dict):
                self.presets[name] = data

    def get_preset_names(self) -> List[str]:
        return list(self.presets.keys())

    def get_preset_weights(self, preset_name: str) -> Dict[str, float]:
        """Get raw weights for a given preset, defaulting to balanced_default."""
        if preset_name in self.presets:
            return dict(self.presets[preset_name])
        if "balanced_default" in self.presets:
            return dict(self.presets["balanced_default"])
        # Fallback default
        return {
            "relief_20km_m": 0.15,
            "slope_20km_deg": 0.15,
            "roughness_10km_m": 0.15,
            "hurst_2_32km": 0.10,
            "temp_mean_c": 0.15,
            "temp_diurnal_range_c": 0.15,
            "temp_min_coldest_c": 0.15,
        }

    def normalize_weights(
        self,
        weights: Dict[str, float],
        available_features: Optional[Set[str]] = None,
    ) -> Dict[str, float]:
        """Normalize weights to sum to 1.0 over available features.

        Features with weight 0.0 or not in available_features are excluded.
        """
        filtered: Dict[str, float] = {}
        for feat, w in weights.items():
            if w <= 0.0:
                continue
            if available_features is not None and feat not in available_features:
                continue
            filtered[feat] = float(w)

        total = sum(filtered.values())
        if total <= 0.0:
            return {}

        return {feat: w / total for feat, w in filtered.items()}
