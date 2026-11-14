"""Demonstration and test harness for the Earth-Mars similarity engine."""

from backend.target_profiles.mars_target import get_oxia_planum_profile
from backend.engine.similarity import EarthCell, score_location_against_target


def run_demo():
    oxia = get_oxia_planum_profile()

    test_sites = [
        EarthCell(
            location_name="Qaidam Basin (Tibetan Plateau)",
            latitude=37.15,
            longitude=93.68,
            vegetation_ndvi=0.02,
            slope_deg=1.4,
            surface_roughness_m=0.48,
            lst_mean_k=278.5,  # Chilly high plateau
            lst_diurnal_range_k=48.2,  # Strong diurnal swing
            soil_moisture_fraction=0.02,
            country="China",
            geological_context="Hyper-arid cold playa with extensive yardangs, evaporite crusts, and clay deposits.",
        ),
        EarthCell(
            location_name="Beacon Valley (McMurdo Dry Valleys)",
            latitude=-77.83,
            longitude=160.67,
            vegetation_ndvi=0.00,
            slope_deg=3.2,
            surface_roughness_m=0.62,
            lst_mean_k=245.0,  # Extremely cold
            lst_diurnal_range_k=32.0,
            soil_moisture_fraction=0.01,
            country="Antarctica",
            geological_context="Permafrost and ancient buried glacial ice under dry sublimation till.",
        ),
        EarthCell(
            location_name="Western Desert Smectite Basin",
            latitude=24.50,
            longitude=27.20,
            vegetation_ndvi=0.01,
            slope_deg=1.1,
            surface_roughness_m=0.38,
            lst_mean_k=298.0,  # Hot desert
            lst_diurnal_range_k=35.0,
            soil_moisture_fraction=0.01,
            country="Egypt",
            geological_context="Hyper-arid wind-deflated smectite clay plains and inverted fluvial channels.",
        ),
        EarthCell(
            location_name="Amazon Rainforest (Negative Control)",
            latitude=-3.46,
            longitude=-62.21,
            vegetation_ndvi=0.82,  # Dense canopy
            slope_deg=1.0,
            surface_roughness_m=0.20,
            lst_mean_k=301.0,
            lst_diurnal_range_k=8.0,
            soil_moisture_fraction=0.45,
            country="Brazil",
            geological_context="Tropical rainforest canopy; non-analog.",
        ),
    ]

    print("=" * 80)
    print("SIMILARITY ENGINE TEST: EARTH SITES vs. OXIA PLANUM (MARS)")
    print("=" * 80)
    for site in test_sites:
        res = score_location_against_target(site, oxia)
        print(f"\n[Site] {site.location_name} ({site.latitude:.2f}, {site.longitude:.2f})")
        if res.is_masked_out:
            print(f"  STATUS: MASKED OUT ({res.mask_reason})")
        else:
            print(f"  Overall Similarity Score: {res.overall_score:.1f} / 100")
            print("  Feature Subscores:")
            for feat, score in res.feature_subscores.items():
                print(f"    - {feat:25s}: {score:5.1f}%")
            print(f"  Top Match:   {res.top_matching_features[0][0]} ({res.top_matching_features[0][1]:.1f}%)")
            print(f"  Top Divergence: {res.top_deviating_features[0][0]} ({res.top_deviating_features[0][1]:.1f}%)")
            print(f"  Recommendation: {res.exploration_recommendation}")
    print("\n" + "=" * 80)


if __name__ == "__main__":
    run_demo()
