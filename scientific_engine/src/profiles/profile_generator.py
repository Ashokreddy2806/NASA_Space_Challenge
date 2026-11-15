"""Target profile generator module.

Generates and saves the master target profile dictionary:
scientific_engine/outputs/profiles/target_profiles.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.data.validation import validate_profile_dict
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile

OUTPUT_PROFILES_DIR = ENGINE_DIR / "outputs" / "profiles"


def generate_all_target_profiles(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Generate and write target_profiles.json."""
    out_dir = output_dir or OUTPUT_PROFILES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    moon_profile = build_moon_target_profile()
    jezero_profile = build_jezero_profile()
    oxia_profile = build_oxia_planum_profile()

    # Validate profiles
    for prof in (moon_profile, jezero_profile, oxia_profile):
        errs = validate_profile_dict(prof)
        if errs:
            raise ValueError(f"Profile {prof.get('target_id')} failed validation: {errs}")

    all_profiles = {
        "metadata": {
            "version": "2.0.0",
            "description": "Verified Moon and Mars target profiles for NASA Space Apps planetary analog matching",
            "pipeline_phases": "Phase 2 (W3, W4)",
            "standards_compliance": "docs/FEATURES.md and docs/DATASETS.md",
        },
        "targets": {
            "moon_south_pole": moon_profile,
            "mars_jezero_crater": jezero_profile,
            "mars_oxia_planum": oxia_profile,
        },
    }

    target_file = out_dir / "target_profiles.json"
    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, indent=2)

    return all_profiles


if __name__ == "__main__":
    profiles = generate_all_target_profiles()
    print(f"Generated target profiles with {len(profiles['targets'])} targets in {OUTPUT_PROFILES_DIR}")
