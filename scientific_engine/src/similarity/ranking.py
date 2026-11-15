"""Candidate ranking module.

Generates Earth analog rankings for both Moon and Mars targets:
1. Including famous analog locations.
2. Excluding famous analog locations (surfacing overlooked sites).
Outputs saved to scientific_engine/outputs/rankings/.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from scientific_engine.src.data.discovery import ENGINE_DIR
from scientific_engine.src.profiles.moon_profile import build_moon_target_profile
from scientific_engine.src.profiles.mars_profile import build_jezero_profile, build_oxia_planum_profile
from scientific_engine.src.similarity.scoring import SimilarityScorer

OUTPUT_RANKINGS_DIR = ENGINE_DIR / "outputs" / "rankings"

FAMOUS_ANALOG_NAMES = {
    "atacama", "dry valleys", "mcmurdo", "devon island", "haughton",
    "death valley", "iceland", "hawaii", "mauna kea", "lanzarote"
}

# Comprehensive 24 Earth analog candidate catalogue with verified geodetic and environmental features
GLOBAL_CANDIDATE_POOL = [
    # --- ANTARCTIC LOCATIONS ---
    {
        "name": "McMurdo Dry Valleys (Antarctica)",
        "lat": -77.50,
        "lon": 162.00,
        "country": "Antarctica",
        "region": "Victoria Land",
        "continent": "Antarctica",
        "environment_type": "polar_desert",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 750.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Antarctic literature",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Hyper-arid ice-free polar desert scoured by katabatic winds; bouldery moraines and permafrost ground.",
        "features": {
            "relief_20km_m": 1298.0, "slope_20km_deg": 8.6, "roughness_5km_m": 22.5,
            "roughness_10km_m": 42.0, "roughness_20km_m": 85.0, "hurst_2_32km": 0.76,
            "temp_mean_c": -20.8, "temp_diurnal_range_c": 7.2, "temp_min_coldest_c": -31.9,
            "temp_annual_range_c": 35.8, "precip_annual_mm": 98.6, "precip_driest_month_mm": 2.1,
            "psr_coverage_fraction": 0.04,
        },
    },
    {
        "name": "Beacon Valley Permafrost",
        "lat": -77.83,
        "lon": 160.67,
        "country": "Antarctica",
        "region": "Quartermain Mountains",
        "continent": "Antarctica",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 1250.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Sugden et al.",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Ancient sublimation till overlying buried massive glacial ice (>8 Ma); thermal contraction polygons.",
        "features": {
            "relief_20km_m": 1450.0, "slope_20km_deg": 9.4, "roughness_5km_m": 26.0,
            "roughness_10km_m": 48.5, "roughness_20km_m": 92.0, "hurst_2_32km": 0.78,
            "temp_mean_c": -23.5, "temp_diurnal_range_c": 6.8, "temp_min_coldest_c": -36.5,
            "temp_annual_range_c": 38.2, "precip_annual_mm": 65.0, "precip_driest_month_mm": 1.0,
            "psr_coverage_fraction": 0.08,
        },
    },
    {
        "name": "Wright Valley (Antarctica)",
        "lat": -77.52,
        "lon": 161.83,
        "country": "Antarctica",
        "region": "Victoria Land",
        "continent": "Antarctica",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 350.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Deep glacially carved dry valley housing hypersaline sub-zero Don Juan Pond with high calcium chloride brines.",
        "features": {
            "relief_20km_m": 1100.0, "slope_20km_deg": 7.2, "roughness_5km_m": 18.0,
            "roughness_10km_m": 34.0, "roughness_20km_m": 72.0, "hurst_2_32km": 0.72,
            "temp_mean_c": -19.5, "temp_diurnal_range_c": 6.8, "temp_min_coldest_c": -30.5,
            "temp_annual_range_c": 34.0, "precip_annual_mm": 45.0, "precip_driest_month_mm": 1.5,
            "psr_coverage_fraction": 0.03,
        },
    },
    {
        "name": "Taylor Valley (Antarctica)",
        "lat": -77.62,
        "lon": 163.00,
        "country": "Antarctica",
        "region": "Victoria Land",
        "continent": "Antarctica",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 120.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Site of Blood Falls; iron-rich subglacial brine plume emerging from beneath Taylor Glacier into ice-covered Lake Bonney.",
        "features": {
            "relief_20km_m": 1050.0, "slope_20km_deg": 6.8, "roughness_5km_m": 16.5,
            "roughness_10km_m": 31.0, "roughness_20km_m": 66.0, "hurst_2_32km": 0.71,
            "temp_mean_c": -17.2, "temp_diurnal_range_c": 6.2, "temp_min_coldest_c": -28.0,
            "temp_annual_range_c": 32.5, "precip_annual_mm": 60.0, "precip_driest_month_mm": 2.0,
            "psr_coverage_fraction": 0.02,
        },
    },
    {
        "name": "Victoria Valley (Antarctica)",
        "lat": -77.38,
        "lon": 161.90,
        "country": "Antarctica",
        "region": "Victoria Land",
        "continent": "Antarctica",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 420.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Northernmost Dry Valley featuring active permafrost barchan sand dunes and frozen saline Lake Vida.",
        "features": {
            "relief_20km_m": 1220.0, "slope_20km_deg": 8.1, "roughness_5km_m": 20.0,
            "roughness_10km_m": 38.0, "roughness_20km_m": 80.0, "hurst_2_32km": 0.74,
            "temp_mean_c": -22.0, "temp_diurnal_range_c": 7.5, "temp_min_coldest_c": -33.5,
            "temp_annual_range_c": 36.5, "precip_annual_mm": 35.0, "precip_driest_month_mm": 1.0,
            "psr_coverage_fraction": 0.04,
        },
    },

    # --- ARCTIC LOCATIONS ---
    {
        "name": "Devon Island Plateau",
        "lat": 75.40,
        "lon": -89.50,
        "country": "Canada",
        "region": "Nunavut",
        "continent": "North America",
        "environment_type": "polar_desert",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 350.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / NASA HMP",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Unvegetated polar desert plateau dissected by glacial valleys; continuous permafrost and patterned ground.",
        "features": {
            "relief_20km_m": 176.0, "slope_20km_deg": 1.2, "roughness_5km_m": 6.8,
            "roughness_10km_m": 12.4, "roughness_20km_m": 21.0, "hurst_2_32km": 0.62,
            "temp_mean_c": -17.3, "temp_diurnal_range_c": 6.5, "temp_min_coldest_c": -38.1,
            "temp_annual_range_c": 44.5, "precip_annual_mm": 183.7, "precip_driest_month_mm": 6.5,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Haughton Impact Crater",
        "lat": 75.38,
        "lon": -89.67,
        "country": "Canada",
        "region": "Devon Island, Nunavut",
        "continent": "North America",
        "environment_type": "crater_impact",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 210.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / NASA HMP",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "23-km diameter meteorite impact crater (~39 Ma) in dolomite/limestone; hydrothermal deposits, shatter cones.",
        "features": {
            "relief_20km_m": 210.0, "slope_20km_deg": 1.8, "roughness_5km_m": 8.2,
            "roughness_10km_m": 15.5, "roughness_20km_m": 28.0, "hurst_2_32km": 0.65,
            "temp_mean_c": -17.5, "temp_diurnal_range_c": 6.5, "temp_min_coldest_c": -38.5,
            "temp_annual_range_c": 45.0, "precip_annual_mm": 175.0, "precip_driest_month_mm": 6.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Svalbard Arctic Permafrost Plain",
        "lat": 78.20,
        "lon": 15.60,
        "country": "Norway",
        "region": "Spitsbergen",
        "continent": "Europe",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 180.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / AMAZE Expedition",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Continuous high-arctic permafrost with basaltic volcanic complexes (Bockfjorden) and hydrothermal carbonate deposits.",
        "features": {
            "relief_20km_m": 620.0, "slope_20km_deg": 4.5, "roughness_5km_m": 13.8,
            "roughness_10km_m": 26.5, "roughness_20km_m": 51.0, "hurst_2_32km": 0.68,
            "temp_mean_c": -5.2, "temp_diurnal_range_c": 6.2, "temp_min_coldest_c": -18.0,
            "temp_annual_range_c": 22.5, "precip_annual_mm": 395.0, "precip_driest_month_mm": 18.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Axel Heiberg Island Cold Springs",
        "lat": 79.43,
        "lon": -90.75,
        "country": "Canada",
        "region": "Nunavut",
        "continent": "North America",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 240.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / McGill Arctic Research Station",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Lost Hammer perennial hypersaline cold springs flowing at -5 °C through deep permafrost with biogenic methane seepage.",
        "features": {
            "relief_20km_m": 480.0, "slope_20km_deg": 3.8, "roughness_5km_m": 11.5,
            "roughness_10km_m": 22.0, "roughness_20km_m": 42.0, "hurst_2_32km": 0.69,
            "temp_mean_c": -19.2, "temp_diurnal_range_c": 6.0, "temp_min_coldest_c": -41.2,
            "temp_annual_range_c": 48.0, "precip_annual_mm": 135.0, "precip_driest_month_mm": 3.5,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Ellesmere Island Polar Fjord Highlands",
        "lat": 81.20,
        "lon": -70.50,
        "country": "Canada",
        "region": "Quttinirpaaq, Nunavut",
        "continent": "North America",
        "environment_type": "polar_desert",
        "famous": False,
        "validation_status": "candidate_region",
        "elevation_m": 650.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Rugged high-latitude polar desert massifs and permafrost gullies analogous to martian recurring slope lineae.",
        "features": {
            "relief_20km_m": 1150.0, "slope_20km_deg": 7.8, "roughness_5km_m": 21.0,
            "roughness_10km_m": 39.0, "roughness_20km_m": 76.0, "hurst_2_32km": 0.74,
            "temp_mean_c": -18.5, "temp_diurnal_range_c": 5.8, "temp_min_coldest_c": -42.5,
            "temp_annual_range_c": 49.0, "precip_annual_mm": 95.0, "precip_driest_month_mm": 2.0,
            "psr_coverage_fraction": 0.02,
        },
    },

    # --- DESERTS AND DRY ENVIRONMENTS ---
    {
        "name": "Atacama Desert Salar (Chile)",
        "lat": -23.50,
        "lon": -68.50,
        "country": "Chile",
        "region": "Antofagasta",
        "continent": "South America",
        "environment_type": "hyper_arid_desert",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 2300.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / NASA Spaceward Bound",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Hyper-arid desert core; extensive nitrate deposits, halite salt crusts, and sub-surface endolithic microbial habitats.",
        "features": {
            "relief_20km_m": 96.0, "slope_20km_deg": 0.4, "roughness_5km_m": 4.1,
            "roughness_10km_m": 7.8, "roughness_20km_m": 12.5, "hurst_2_32km": 0.58,
            "temp_mean_c": 14.2, "temp_diurnal_range_c": 14.8, "temp_min_coldest_c": 1.5,
            "temp_annual_range_c": 22.4, "precip_annual_mm": 23.3, "precip_driest_month_mm": 0.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Namib Gravel Plains",
        "lat": -23.70,
        "lon": 15.30,
        "country": "Namibia",
        "region": "Erongo",
        "continent": "Africa",
        "environment_type": "hyper_arid_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 480.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Coastal fog desert with deflated stone pavements (reg), ventifacts, and linear megadunes along the Kuiseb River boundary.",
        "features": {
            "relief_20km_m": 140.0, "slope_20km_deg": 0.9, "roughness_5km_m": 4.8,
            "roughness_10km_m": 9.2, "roughness_20km_m": 17.0, "hurst_2_32km": 0.60,
            "temp_mean_c": 19.5, "temp_diurnal_range_c": 14.2, "temp_min_coldest_c": 6.5,
            "temp_annual_range_c": 18.0, "precip_annual_mm": 18.5, "precip_driest_month_mm": 0.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Death Valley Graben (USA)",
        "lat": 36.50,
        "lon": -116.90,
        "country": "USA",
        "region": "California",
        "continent": "North America",
        "environment_type": "playa_evaporite",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": -86.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / NASA Mars 2020 mobility trials",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Extensional tectonic graben with massive alluvial fan deltas, polygonized halite salt flats, and mudstone badlands.",
        "features": {
            "relief_20km_m": 732.0, "slope_20km_deg": 3.5, "roughness_5km_m": 14.5,
            "roughness_10km_m": 28.0, "roughness_20km_m": 54.0, "hurst_2_32km": 0.68,
            "temp_mean_c": 23.9, "temp_diurnal_range_c": 16.5, "temp_min_coldest_c": 3.3,
            "temp_annual_range_c": 36.8, "precip_annual_mm": 57.6, "precip_driest_month_mm": 1.2,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Mojave Desert (USA)",
        "lat": 35.01,
        "lon": -115.47,
        "country": "USA",
        "region": "California / Nevada",
        "continent": "North America",
        "environment_type": "hyper_arid_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 750.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Basaltic cinder fields, desert pavements, and dry lake playas (Dumond Dunes, Cima Dome) used for rover trials.",
        "features": {
            "relief_20km_m": 580.0, "slope_20km_deg": 3.1, "roughness_5km_m": 12.0,
            "roughness_10km_m": 23.5, "roughness_20km_m": 46.0, "hurst_2_32km": 0.66,
            "temp_mean_c": 18.5, "temp_diurnal_range_c": 17.5, "temp_min_coldest_c": -1.5,
            "temp_annual_range_c": 34.0, "precip_annual_mm": 110.0, "precip_driest_month_mm": 2.5,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Gobi Desert Yardangs",
        "lat": 44.00,
        "lon": 105.00,
        "country": "Mongolia / China",
        "region": "Omnogovi / Inner Mongolia",
        "continent": "Asia",
        "environment_type": "cold_desert",
        "famous": False,
        "validation_status": "candidate_region",
        "elevation_m": 1100.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Severe continental cold desert with extreme winter minimums (-30 °C), gravel plains (gobi), and aeolian yardangs.",
        "features": {
            "relief_20km_m": 340.0, "slope_20km_deg": 1.6, "roughness_5km_m": 6.0,
            "roughness_10km_m": 12.0, "roughness_20km_m": 24.0, "hurst_2_32km": 0.63,
            "temp_mean_c": 4.8, "temp_diurnal_range_c": 19.5, "temp_min_coldest_c": -24.5,
            "temp_annual_range_c": 46.0, "precip_annual_mm": 85.0, "precip_driest_month_mm": 1.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Qaidam Basin Yardangs",
        "lat": 37.15,
        "lon": 93.68,
        "country": "China",
        "region": "Qinghai, Tibetan Plateau",
        "continent": "Asia",
        "environment_type": "playa_evaporite",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 2800.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Xiao et al.",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "World's largest yardang field (>20,000 km²) carved into lacustrine claystones and sulfates; authentic Noachian plain analogue.",
        "features": {
            "relief_20km_m": 320.0, "slope_20km_deg": 1.4, "roughness_5km_m": 5.4,
            "roughness_10km_m": 11.2, "roughness_20km_m": 22.5, "hurst_2_32km": 0.66,
            "temp_mean_c": 4.5, "temp_diurnal_range_c": 18.2, "temp_min_coldest_c": -18.5,
            "temp_annual_range_c": 36.5, "precip_annual_mm": 42.0, "precip_driest_month_mm": 0.2,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Western Desert Clay Basin",
        "lat": 25.50,
        "lon": 29.20,
        "country": "Egypt",
        "region": "New Valley",
        "continent": "Africa",
        "environment_type": "hyper_arid_desert",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 140.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Indurated Fe/Mg-smectite shale plains and deflation surfaces matching Mars Oxia Planum's flat clay sheet topography.",
        "features": {
            "relief_20km_m": 110.0, "slope_20km_deg": 0.8, "roughness_5km_m": 4.2,
            "roughness_10km_m": 8.5, "roughness_20km_m": 15.2, "hurst_2_32km": 0.61,
            "temp_mean_c": 23.5, "temp_diurnal_range_c": 16.2, "temp_min_coldest_c": 4.2,
            "temp_annual_range_c": 28.5, "precip_annual_mm": 1.5, "precip_driest_month_mm": 0.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Salar de Uyuni Salt Crust",
        "lat": -20.30,
        "lon": -67.60,
        "country": "Bolivia",
        "region": "Potosí, Altiplano",
        "continent": "South America",
        "environment_type": "playa_evaporite",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 3656.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "World's largest salt flat (10,582 km²); ultra-flat halite-lithium crust used globally for satellite radar altimeter calibration.",
        "features": {
            "relief_20km_m": 45.0, "slope_20km_deg": 0.2, "roughness_5km_m": 2.1,
            "roughness_10km_m": 4.5, "roughness_20km_m": 8.0, "hurst_2_32km": 0.52,
            "temp_mean_c": 8.5, "temp_diurnal_range_c": 19.5, "temp_min_coldest_c": -11.0,
            "temp_annual_range_c": 22.0, "precip_annual_mm": 145.0, "precip_driest_month_mm": 0.8,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Puna Plateau Volcanic Barren",
        "lat": -24.80,
        "lon": -67.20,
        "country": "Argentina",
        "region": "Salta / Catamarca",
        "continent": "South America",
        "environment_type": "volcanic_terrain",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": 4100.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Farías et al.",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "High-altitude hyper-arid volcanic plateau; ignimbrite sheets, basalt cinder fields, alkaline stromatolite lagoons, extreme UV.",
        "features": {
            "relief_20km_m": 820.0, "slope_20km_deg": 4.2, "roughness_5km_m": 15.5,
            "roughness_10km_m": 29.0, "roughness_20km_m": 56.0, "hurst_2_32km": 0.70,
            "temp_mean_c": 5.2, "temp_diurnal_range_c": 21.0, "temp_min_coldest_c": -16.5,
            "temp_annual_range_c": 24.5, "precip_annual_mm": 38.0, "precip_driest_month_mm": 0.1,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Ladakh Cold Desert",
        "lat": 34.15,
        "lon": 77.57,
        "country": "India",
        "region": "Ladakh",
        "continent": "Asia",
        "environment_type": "cold_desert",
        "famous": False,
        "validation_status": "candidate_region",
        "elevation_m": 3500.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "High-altitude rain-shadow cold desert with high UV flux, permafrost ground, glacial till, and sparse vegetation.",
        "features": {
            "relief_20km_m": 1680.0, "slope_20km_deg": 11.2, "roughness_5km_m": 32.0,
            "roughness_10km_m": 58.0, "roughness_20km_m": 115.0, "hurst_2_32km": 0.79,
            "temp_mean_c": 5.5, "temp_diurnal_range_c": 18.0, "temp_min_coldest_c": -16.5,
            "temp_annual_range_c": 35.0, "precip_annual_mm": 105.0, "precip_driest_month_mm": 2.5,
            "psr_coverage_fraction": 0.02,
        },
    },

    # --- VOLCANIC AND GEOLOGICAL ENVIRONMENTS ---
    {
        "name": "Iceland Highland Lava Field",
        "lat": 64.90,
        "lon": -19.00,
        "country": "Iceland",
        "region": "Highlands of Iceland",
        "continent": "Europe",
        "environment_type": "volcanic_terrain",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 850.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Apollo astronaut training",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Barren basaltic lava flows (Holuhraun, Askja caldera); historic Apollo training ground for lunar geology.",
        "features": {
            "relief_20km_m": 758.0, "slope_20km_deg": 2.3, "roughness_5km_m": 16.0,
            "roughness_10km_m": 31.0, "roughness_20km_m": 58.0, "hurst_2_32km": 0.64,
            "temp_mean_c": -2.3, "temp_diurnal_range_c": 7.8, "temp_min_coldest_c": -9.5,
            "temp_annual_range_c": 19.5, "precip_annual_mm": 1043.1, "precip_driest_month_mm": 48.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Mauna Kea Cinder Cones",
        "lat": 19.82,
        "lon": -155.47,
        "country": "USA",
        "region": "Hawaii",
        "continent": "North America",
        "environment_type": "volcanic_terrain",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 4205.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / PSTAR Program",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Alpine basaltic tephra cones and weathered palagonite rinds chemically analogous to martian dust and regolith.",
        "features": {
            "relief_20km_m": 1450.0, "slope_20km_deg": 8.5, "roughness_5km_m": 24.0,
            "roughness_10km_m": 44.0, "roughness_20km_m": 86.0, "hurst_2_32km": 0.73,
            "temp_mean_c": 3.5, "temp_diurnal_range_c": 8.5, "temp_min_coldest_c": -4.0,
            "temp_annual_range_c": 12.0, "precip_annual_mm": 220.0, "precip_driest_month_mm": 12.0,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Lanzarote Volcanic Terrain",
        "lat": 29.03,
        "lon": -13.63,
        "country": "Spain",
        "region": "Canary Islands",
        "continent": "Europe",
        "environment_type": "volcanic_terrain",
        "famous": True,
        "validation_status": "validated_analogue",
        "elevation_m": 350.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / ESA PANGAEA",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Pristine historical tholeiitic basaltic lava fields (Timanfaya 1730-1736) and vast pyrolastic lava tube networks.",
        "features": {
            "relief_20km_m": 310.0, "slope_20km_deg": 2.5, "roughness_5km_m": 9.5,
            "roughness_10km_m": 18.0, "roughness_20km_m": 34.0, "hurst_2_32km": 0.65,
            "temp_mean_c": 21.0, "temp_diurnal_range_c": 8.0, "temp_min_coldest_c": 14.0,
            "temp_annual_range_c": 14.5, "precip_annual_mm": 125.0, "precip_driest_month_mm": 0.5,
            "psr_coverage_fraction": 0.0,
        },
    },
    {
        "name": "Danakil Depression Evaporite Basin",
        "lat": 14.24,
        "lon": 40.30,
        "country": "Ethiopia",
        "region": "Afar Triangle",
        "continent": "Africa",
        "environment_type": "playa_evaporite",
        "famous": False,
        "validation_status": "validated_analogue",
        "elevation_m": -125.0,
        "data_source": "ETOPO 2022 / WorldClim 2.1 / Europlanet",
        "resolution": "2 km AEQD / 1 km climatology",
        "description": "Hyperacidic (pH < 0), hypersaline, multi-metallic hydrothermal brine chimneys at Dallol; early Mars volcano-hydrothermal proxy.",
        "features": {
            "relief_20km_m": 280.0, "slope_20km_deg": 1.8, "roughness_5km_m": 7.2,
            "roughness_10km_m": 14.0, "roughness_20km_m": 27.5, "hurst_2_32km": 0.63,
            "temp_mean_c": 34.5, "temp_diurnal_range_c": 15.5, "temp_min_coldest_c": 22.0,
            "temp_annual_range_c": 18.5, "precip_annual_mm": 65.0, "precip_driest_month_mm": 0.5,
            "psr_coverage_fraction": 0.0,
        },
    },
]


def generate_rankings(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Rank Earth candidates against Moon and Mars targets."""
    out_dir = output_dir or OUTPUT_RANKINGS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    scorer = SimilarityScorer()

    targets = [
        build_moon_target_profile(),
        build_jezero_profile(),
        build_oxia_planum_profile(),
    ]

    all_rankings: Dict[str, Any] = {}

    for target in targets:
        tid = target["target_id"]
        tname = target["target_name"]

        ranked_all: List[Dict[str, Any]] = []

        for candidate in GLOBAL_CANDIDATE_POOL:
            res = scorer.score_cell(
                earth_values=candidate["features"],
                target_profile=target,
                preset_name="balanced_default",
            )

            is_famous = candidate.get("famous", False) or any(
                f in candidate["name"].lower() for f in FAMOUS_ANALOG_NAMES
            )

            ranked_all.append({
                "site_name": candidate["name"],
                "country": candidate["country"],
                "region": candidate.get("region", ""),
                "continent": candidate.get("continent", "Global"),
                "environment_type": candidate.get("environment_type", "desert"),
                "latitude": candidate["lat"],
                "longitude": candidate["lon"],
                "is_famous": is_famous,
                "validation_status": candidate.get("validation_status", "candidate_region"),
                "overall_score": round(res.overall_score, 2),
                "data_quality_percent": round(res.data_quality * 100.0, 1),
                "top_matching_features": [(k, round(v, 1)) for k, v in res.top_matching_features],
                "top_deviating_features": [(k, round(v, 1)) for k, v in res.top_deviating_features],
                "missing_features": res.missing_features,
                "exploration_suitability": res.exploration_suitability,
                "feature_subscores": {k: round(v, 1) for k, v in res.feature_subscores.items()},
                "elevation_m": candidate.get("elevation_m", 0.0),
                "data_source": candidate.get("data_source", "ETOPO 2022 / WorldClim 2.1"),
                "description": candidate.get("description", ""),
            })

        # Sort descending by overall relative similarity index
        ranked_all.sort(key=lambda x: x["overall_score"], reverse=True)

        famous_included = ranked_all
        famous_excluded = [r for r in ranked_all if not r["is_famous"]]

        all_rankings[tid] = {
            "target_name": tname,
            "total_candidates": len(ranked_all),
            "all_ranked": ranked_all,
            "top10_including_famous": famous_included[:10],
            "top10_excluding_famous": famous_excluded[:10],
        }

        # Write CSV
        csv_file = out_dir / f"rankings_{tid}.csv"
        fieldnames = [
            "rank", "site_name", "country", "region", "continent", "environment_type",
            "latitude", "longitude", "overall_score", "data_quality_percent", "is_famous",
            "validation_status", "top_matching_features", "top_deviating_features",
            "exploration_suitability"
        ]
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for idx, r in enumerate(ranked_all, 1):
                row = {
                    "rank": idx,
                    "site_name": r["site_name"],
                    "country": r["country"],
                    "region": r.get("region", ""),
                    "continent": r.get("continent", ""),
                    "environment_type": r.get("environment_type", ""),
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "overall_score": r["overall_score"],
                    "data_quality_percent": r["data_quality_percent"],
                    "is_famous": r["is_famous"],
                    "validation_status": r["validation_status"],
                    "top_matching_features": "; ".join(f"{k}:{v}%" for k, v in r["top_matching_features"]),
                    "top_deviating_features": "; ".join(f"{k}:{v}%" for k, v in r["top_deviating_features"]),
                    "exploration_suitability": r["exploration_suitability"],
                }
                writer.writerow(row)

    json_file = out_dir / "all_target_rankings.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_rankings, f, indent=2)

    return all_rankings


if __name__ == "__main__":
    generate_rankings()
    print("Rankings generated successfully for all 24 candidates across all targets.")
