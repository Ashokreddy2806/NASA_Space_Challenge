"""Master orchestration script for scientific_engine (Phase 2 & Phase 3).

Executes the complete workflow end-to-end:
1. Discovers and catalogs datasets.
2. Builds and validates Moon and Mars target profiles.
3. Generates target_profiles.json.
4. Generates distribution plots.
5. Runs Earth analog validation on the 6 confirmed sites (analog_validation.csv).
6. Generates top-10 candidate rankings (including and excluding famous sites).
7. Generates cartographic similarity maps.
8. Writes comprehensive run_metadata.json for full reproducibility.
"""

from __future__ import annotations

import datetime
import json
import platform
import sys
import time
from pathlib import Path

# Add project root to sys.path so package imports resolve seamlessly
ENGINE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ENGINE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scientific_engine.src.data.discovery import get_dataset_catalog
from scientific_engine.src.profiles.profile_generator import generate_all_target_profiles
from scientific_engine.src.similarity.ranking import generate_rankings
from scientific_engine.src.similarity.validation import run_analog_validation
from scientific_engine.src.visualization.comparisons import generate_comparison_charts
from scientific_engine.src.visualization.distributions import generate_distribution_plots
from scientific_engine.src.visualization.similarity_maps import generate_similarity_maps


def run_pipeline() -> None:
    """Run the complete scientific engine pipeline."""
    print("=" * 80)
    print("NASA SPACE APPS CHALLENGE — CLEAN SCIENTIFIC ENGINE (PHASE 2 + PHASE 3)")
    print("=" * 80)
    start_time = time.perf_counter()
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Step 1: Catalog audit
    print("\n[Step 1/7] Discovering and cataloging datasets...")
    catalog = get_dataset_catalog()
    avail_count = sum(1 for d in catalog.values() if d.is_available_locally)
    print(f"  Cataloged {len(catalog)} official datasets ({avail_count} available locally).")

    # Step 2: Target Profiles (Phase 2)
    print("\n[Step 2/7] Generating verified Moon and Mars target profiles...")
    profiles = generate_all_target_profiles()
    print(f"  Saved target_profiles.json ({len(profiles['targets'])} target profiles validated).")

    # Step 3: Distribution Plots
    print("\n[Step 3/7] Generating planetary distribution comparison plots...")
    plot_files = generate_distribution_plots()
    print(f"  Rendered {len(plot_files)} distribution plots in outputs/plots/.")

    # Step 4: Earth Analog Validation (Phase 3)
    print("\n[Step 4/7] Validating 6 confirmed Earth analog sites against all targets...")
    validation_records = run_analog_validation()
    print(f"  Completed {len(validation_records)} validation evaluations. Saved analog_validation.csv.")

    # Step 5: Candidate Rankings
    print("\n[Step 5/7] Generating top-10 candidate rankings (including & excluding famous sites)...")
    rankings = generate_rankings()
    print("  Ranked all candidate sites across targets. Saved rankings CSVs and all_target_rankings.json.")

    # Step 6: Similarity Maps
    print("\n[Step 6/7] Rendering cartographic similarity maps...")
    map_files = generate_similarity_maps()
    print(f"  Rendered {len(map_files)} similarity maps in outputs/maps/.")

    # Step 7: Multi-Feature Radar Charts
    print("\n[Step 7/7] Generating multi-feature radar comparison charts...")
    radar_files = generate_comparison_charts()
    print(f"  Rendered {len(radar_files)} radar comparison charts in outputs/plots/.")

    # Run Metadata for Reproducibility
    duration = time.perf_counter() - start_time
    metadata = {
        "execution_timestamp_utc": timestamp,
        "runtime_seconds": round(duration, 3),
        "system_info": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "executable": sys.executable,
        },
        "standards": {
            "earth_reference_grid": "0.05 deg WGS 84 (7200 x 3600), WorldClim 2.1 + ETOPO 2022",
            "moon_reference_crs": "Moon 2015 South Polar Stereographic (R=1737.4 km, True at 90S, central 0)",
            "mars_reference_crs": "Mars Simple Cylindrical (MOLA areoid datum, 0-360 deg East)",
            "estimator_spec": "docs/FEATURES.md locked contract",
        },
        "target_summaries": {
            "moon_south_pole": {
                "relief_20km_m": profiles["targets"]["moon_south_pole"]["features"]["relief_20km_m"]["value"],
                "slope_20km_deg": profiles["targets"]["moon_south_pole"]["features"]["slope_20km_deg"]["value"],
                "temp_mean_c": profiles["targets"]["moon_south_pole"]["features"]["temp_mean_c"]["value"],
                "psr_coverage_fraction": profiles["targets"]["moon_south_pole"]["features"]["psr_coverage_fraction"]["value"],
            },
            "mars_jezero_crater": {
                "relief_20km_m": profiles["targets"]["mars_jezero_crater"]["features"]["relief_20km_m"]["value"],
                "slope_20km_deg": profiles["targets"]["mars_jezero_crater"]["features"]["slope_20km_deg"]["value"],
                "temp_mean_c": profiles["targets"]["mars_jezero_crater"]["features"]["temp_mean_c"]["value"],
            },
            "mars_oxia_planum": {
                "relief_20km_m": profiles["targets"]["mars_oxia_planum"]["features"]["relief_20km_m"]["value"],
                "slope_20km_deg": profiles["targets"]["mars_oxia_planum"]["features"]["slope_20km_deg"]["value"],
                "temp_mean_c": profiles["targets"]["mars_oxia_planum"]["features"]["temp_mean_c"]["value"],
            },
        },
        "output_inventory": {
            "profiles": ["outputs/profiles/target_profiles.json"],
            "validation": ["outputs/validation/analog_validation.csv"],
            "rankings": [
                "outputs/rankings/all_target_rankings.json",
                "outputs/rankings/rankings_moon_south_pole.csv",
                "outputs/rankings/rankings_mars_jezero_crater.csv",
                "outputs/rankings/rankings_mars_oxia_planum.csv",
            ],
            "maps": [p.name for p in map_files],
            "plots": [p.name for p in plot_files + radar_files],
        },
    }

    meta_path = ENGINE_DIR / "outputs" / "run_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 80)
    print(f"PIPELINE RUN COMPLETE in {duration:.2f} seconds!")
    print(f"Reproducibility run metadata saved to: {meta_path}")
    print("=" * 80)


if __name__ == "__main__":
    run_pipeline()
