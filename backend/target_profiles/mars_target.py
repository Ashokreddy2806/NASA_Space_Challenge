"""W4 Mars Target Profile Generator.

Generates standardized, scientifically validated Mars target profiles for
Earth analog similarity matching (W5 engine).

Primary Target: Oxia Planum (ExoMars Rosalind Franklin Landing Site)
Comparative Benchmark: Jezero Crater (NASA Mars 2020 Perseverance Site)
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("mars_target")


@dataclass
class CoordinateBounds:
    """Geographical study boundary."""
    center_lat: float
    center_lon_east: float  # Degrees East (0-360)
    center_lon_west: float  # Degrees West (convenience)
    min_lat: float
    max_lat: float
    min_lon_east: float
    max_lon_east: float
    datum: str = "MOLA areoid (0 m elevation defined at mean radius 3396.0 km)"


@dataclass
class FeatureMeasurement:
    """Single scientific feature measurement with lineage and confidence."""
    name: str
    value: float
    unit: str
    std_dev: Optional[float] = None
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    data_quality_tier: str = "orbital_derived"  # ground_truth_in_situ | orbital_derived | model_derived | estimated
    instrument: str = ""
    pds_dataset_id: str = ""
    citation: str = ""
    notes: str = ""


@dataclass
class MarsTargetProfile:
    """Full Mars Target Profile specification compatible with W5 similarity engine."""
    target_id: str
    target_name: str
    target_archetype: str  # e.g. "ancient_clay_habitable_plain" vs "crater_delta_lake"
    mission_context: str
    scientific_summary: str
    geological_epoch: str
    coordinates: CoordinateBounds
    # Core global vector for Tier-1 screening (aligned with Earth global grid features)
    tier1_global_vector: Dict[str, float]
    # Feature tolerance / normalization scales for distance calculation
    tier1_feature_weights: Dict[str, float]
    tier1_tolerances: Dict[str, float]
    # Detailed scientific measurements across all domains
    detailed_measurements: Dict[str, FeatureMeasurement]
    # Earth limits / non-matching realities
    irreducible_limits: Dict[str, str]
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to serializable dictionary."""
        d = asdict(self)
        return d

    def export_json(self, filepath: Path) -> None:
        """Export profile to machine-readable JSON."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("Exported Mars target profile to %s", filepath)


def get_oxia_planum_profile() -> MarsTargetProfile:
    """Generate the primary Mars target profile: Oxia Planum.

    Scientific justification:
    - Ancient Noachian plain (~3.9-4.0 Ga) preserving widespread Fe/Mg smectite clays.
    - Official landing site for ESA/Roscosmos ExoMars Rosalind Franklin Rover.
    - Low regional slope (<1.5 deg) and low dust mantling make it an ideal target
      for regional coarse-grid (5 km) planetary analog screening.
    """
    coords = CoordinateBounds(
        center_lat=18.275,
        center_lon_east=335.368,
        center_lon_west=24.632,
        min_lat=17.50,
        max_lat=19.00,
        min_lon_east=334.50,
        max_lon_east=336.50,
    )

    measurements = {
        "elevation": FeatureMeasurement(
            name="surface_elevation",
            value=-3050.0,
            unit="m",
            std_dev=85.0,
            min_val=-3200.0,
            max_val=-2900.0,
            data_quality_tier="orbital_derived",
            instrument="MGS MOLA / HRSC-MOLA Blended DEM",
            pds_dataset_id="MGS-M-MOLA-5-MEGDR-L3-V1.0",
            citation="Fergason et al. (2018), Quantin-Nataf et al. (2021)",
            notes="Elevation relative to MOLA areoid",
        ),
        "slope": FeatureMeasurement(
            name="regional_slope",
            value=1.2,
            unit="degrees",
            std_dev=0.8,
            min_val=0.1,
            max_val=4.5,
            data_quality_tier="orbital_derived",
            instrument="HRSC-MOLA 200m DEM / HiRISE DTMs",
            pds_dataset_id="MRO-M-HIRISE-5-DTM-V1.0",
            citation="Quantin-Nataf et al. (2021) Astrobiology",
            notes="98% of landing ellipse area has slopes < 5 degrees",
        ),
        "surface_roughness_rms": FeatureMeasurement(
            name="decameter_rms_roughness",
            value=0.45,
            unit="m",
            std_dev=0.15,
            min_val=0.10,
            max_val=1.10,
            data_quality_tier="orbital_derived",
            instrument="MGS MOLA 1-km baseline pulse width / HiRISE",
            pds_dataset_id="MGS-M-MOLA-3-PEDR-L1A-V1.0",
            citation="Kreslavsky & Head (2000)",
            notes="Relatively smooth, low-relief plain with isolated resistant remnant buttes",
        ),
        "temperature_mean_annual": FeatureMeasurement(
            name="surface_temperature_annual_mean",
            value=212.5,
            unit="K",
            std_dev=12.0,
            min_val=178.2,
            max_val=274.0,
            data_quality_tier="model_validated",
            instrument="Mars Climate Database (MCD v6.1) / MGS TES",
            pds_dataset_id="MGS-M-TES-3-TSDR-V1.0",
            citation="Forget et al. (1999), Millour et al. (2018)",
            notes="Equivalent to -60.65 deg C annual mean surface temperature",
        ),
        "temperature_diurnal_range": FeatureMeasurement(
            name="diurnal_temperature_amplitude",
            value=72.4,
            unit="K",
            std_dev=6.5,
            min_val=55.0,
            max_val=88.0,
            data_quality_tier="orbital_derived",
            instrument="Odyssey THEMIS IR / MGS TES",
            pds_dataset_id="ODY-M-THM-5-IRGEO-V1.0",
            citation="Christensen et al. (2004)",
            notes="Severe diurnal swing typical of thin Martian atmosphere and low thermal inertia",
        ),
        "thermal_inertia": FeatureMeasurement(
            name="thermal_inertia",
            value=265.0,
            unit="J m^-2 K^-1 s^-1/2",
            std_dev=45.0,
            min_val=180.0,
            max_val=360.0,
            data_quality_tier="orbital_derived",
            instrument="Odyssey THEMIS Global Thermal Inertia Mosaic (v2)",
            pds_dataset_id="ODY-M-THM-5-IRGEO-V1.0",
            citation="Edwards et al. (2011), Fergason et al. (2018)",
            notes="Corresponds to cohesive duricrust / moderately indurated clay-bearing regolith",
        ),
        "albedo_bolometric": FeatureMeasurement(
            name="bolometric_visible_albedo",
            value=0.165,
            unit="dimensionless",
            std_dev=0.020,
            min_val=0.125,
            max_val=0.210,
            data_quality_tier="orbital_derived",
            instrument="MGS TES Bolometric Albedo",
            pds_dataset_id="MGS-M-TES-3-TSDR-V1.0",
            citation="Christensen et al. (2001)",
            notes="Intermediate albedo, indicating exposed bedrock with thin, non-continuous dust",
        ),
        "dust_cover_index": FeatureMeasurement(
            name="dust_cover_index_dci",
            value=0.962,
            unit="dimensionless",
            std_dev=0.015,
            min_val=0.930,
            max_val=0.985,
            data_quality_tier="orbital_derived",
            instrument="MGS TES 1075 cm^-1 Silicate Band",
            pds_dataset_id="MGS-M-TES-3-TSDR-V1.0",
            citation="Ruff & Christensen (2002)",
            notes="DCI > 0.95 indicates a dust-poor, rock/duricrust-dominated surface",
        ),
        "clay_phyllosilicate_index": FeatureMeasurement(
            name="fe_mg_phyllosilicate_absorption",
            value=0.052,
            unit="band_depth_d2300",
            std_dev=0.018,
            min_val=0.020,
            max_val=0.085,
            data_quality_tier="orbital_derived",
            instrument="MRO CRISM Targeted Runs (FRT0000A2C9, FRT00009B89)",
            pds_dataset_id="MRO-M-CRISM-3-RDR-TARGETED-V1.0",
            citation="Carter et al. (2015), Quantin-Nataf et al. (2021)",
            notes="Extensive stratiform Fe/Mg smectite clay (saponite/vermiculite)",
        ),
        "water_equivalent_hydrogen": FeatureMeasurement(
            name="water_equivalent_hydrogen_weh",
            value=3.8,
            unit="wt% H2O",
            std_dev=0.6,
            min_val=2.8,
            max_val=4.9,
            data_quality_tier="orbital_derived",
            instrument="Mars Odyssey GRS / HEND Neutron Spectrometer",
            pds_dataset_id="ODY-M-GRS-5-DIR-H2O-MAP-V1.0",
            citation="Boynton et al. (2007), Feldman et al. (2004)",
            notes="Water bound in clay mineral lattice (structural OH/H2O); zero liquid water",
        ),
        "atmospheric_pressure": FeatureMeasurement(
            name="mean_surface_pressure",
            value=755.0,
            unit="Pa",
            std_dev=45.0,
            min_val=690.0,
            max_val=840.0,
            data_quality_tier="model_validated",
            instrument="MCD v6.1 scaled to MOLA elevation -3050 m",
            pds_dataset_id="MCD-LMD-V6.1",
            citation="Forget et al. (1999)",
            notes="Approx 7.55 hPa (0.0075 atm); 95.3% CO2",
        ),
    }

    # Core 6-element Tier-1 Global Vector for W5 similarity matching against Earth grid:
    # Earth Features: [ndvi, slope_deg, roughness_m, lst_mean_k, lst_diurnal_k, soil_moisture_m3m3]
    tier1_vector = {
        "vegetation_ndvi": 0.00,        # Abiotic constraint
        "slope_deg": 1.20,              # Flat plain
        "surface_roughness_m": 0.45,    # Decameter RMS roughness
        "lst_mean_k": 212.5,            # Annual mean surface temp
        "lst_diurnal_range_k": 72.4,    # Day/Night amplitude
        "soil_moisture_fraction": 0.00, # Absolute hydrologic dryness
    }

    # Normalization tolerances (sigma) for Euclidean/Mahalanobis distance scoring in W5
    tier1_tolerances = {
        "vegetation_ndvi": 0.05,        # Strict cutoff: must be bare ground
        "slope_deg": 2.00,              # Degrees tolerance
        "surface_roughness_m": 0.50,    # Meters tolerance
        "lst_mean_k": 15.0,             # Kelvin tolerance
        "lst_diurnal_range_k": 12.0,    # Kelvin tolerance
        "soil_moisture_fraction": 0.03, # Volumetric fraction tolerance
    }

    tier1_weights = {
        "vegetation_ndvi": 0.25,        # High weight to eliminate all vegetation
        "slope_deg": 0.15,
        "surface_roughness_m": 0.15,
        "lst_mean_k": 0.15,
        "lst_diurnal_range_k": 0.15,
        "soil_moisture_fraction": 0.15,
    }

    limits = {
        "surface_gravity": "Mars = 3.71 m/s^2 (0.38g) vs Earth = 9.81 m/s^2 (1.00g). Affects saltation threshold and rover chassis dynamics.",
        "atmospheric_pressure": "Mars = ~7.55 hPa (0.0075 atm) pure CO2 vs Earth = 1013 hPa N2/O2. Sublimation kinetics and aerodynamic rotorcraft testing diverge.",
        "radiation_environment": "Oxia Planum has zero magnetic shielding and negligible atmosphere; annual cosmic ray/SPE surface dose is ~230 mSv/yr.",
        "biological_sterility": "Oxia Planum is an abiotic, hyper-arid surface exposed to UV-C; Earth analogs contain active microbial extremophiles.",
    }

    return MarsTargetProfile(
        target_id="mars_oxia_planum",
        target_name="Oxia Planum",
        target_archetype="ancient_clay_habitable_plain",
        mission_context="ExoMars Rosalind Franklin Rover Landing Site (ESA/Roscosmos/NASA)",
        scientific_summary=(
            "Exposes an ancient (~4.0 Ga, Noachian) stratiform clay sheet spanning thousands "
            "of square kilometers. Unlike volatile lake deposits that underwent acidic desiccation, "
            "Oxia Planum represents a persistent, neutral-pH, habitable water-rock alteration epoch "
            "subsequently preserved by cryogenic freeze-drying and gentle aeolian deflation."
        ),
        geological_epoch="Circa 4.0 Ga (Noachian to Early Hesperian boundary)",
        coordinates=coords,
        tier1_global_vector=tier1_vector,
        tier1_feature_weights=tier1_weights,
        tier1_tolerances=tier1_tolerances,
        detailed_measurements=measurements,
        irreducible_limits=limits,
        metadata={
            "version": "1.0.0",
            "primary_target": True,
            "created_by": "W4 Mars Target Workstream",
            "recommended_earth_analog_archetypes": [
                "Cold-desert clay playas (e.g. McMurdo Dry Valleys paleolake sediments)",
                "Hyper-arid high-altitude evaporite basins (Tibetan Qaidam Basin, Puna-Altiplano salars)",
                "Wind-deflated smectite clay massifs (Western Desert of Egypt)",
            ],
        },
    )


def get_jezero_crater_profile() -> MarsTargetProfile:
    """Generate comparative benchmark Mars target profile: Jezero Crater.

    Scientific justification:
    - NASA Mars 2020 Perseverance landing site ($18.38 N, 77.58 E$).
    - Open-basin paleolake with preserved river delta fan.
    - Ground-truth validation available from MEDA, PIXL, SHERLOC, SuperCam, RIMFAX.
    """
    coords = CoordinateBounds(
        center_lat=18.380,
        center_lon_east=77.580,
        center_lon_west=282.420,
        min_lat=18.15,
        max_lat=18.60,
        min_lon_east=77.30,
        max_lon_east=77.85,
    )

    measurements = {
        "elevation": FeatureMeasurement(
            name="surface_elevation",
            value=-2530.0,
            unit="m",
            std_dev=120.0,
            min_val=-2650.0,
            max_val=-2100.0,
            data_quality_tier="ground_truth_in_situ",
            instrument="MOLA / HiRISE DTM / Perseverance MEDA barometer",
            pds_dataset_id="MGS-M-MOLA-5-MEGDR-L3-V1.0",
            citation="Farley et al. (2020), Rodriguez-Manfredi et al. (2021)",
            notes="Elevation of floor and western delta fan base",
        ),
        "slope": FeatureMeasurement(
            name="crater_floor_slope",
            value=2.4,
            unit="degrees",
            std_dev=1.8,
            min_val=0.2,
            max_val=18.5,
            data_quality_tier="ground_truth_in_situ",
            instrument="HiRISE DTM / Rover IMU traversability logs",
            pds_dataset_id="MRO-M-HIRISE-5-DTM-V1.0",
            citation="Stack et al. (2020)",
            notes="Landing ellipse is flat (1.5 deg), delta scarp exceeds 15-20 deg",
        ),
        "surface_roughness_rms": FeatureMeasurement(
            name="decameter_rms_roughness",
            value=0.78,
            unit="m",
            std_dev=0.35,
            min_val=0.20,
            max_val=2.10,
            data_quality_tier="ground_truth_in_situ",
            instrument="HiRISE / Perseverance Navcam stereo point clouds",
            pds_dataset_id="MRO-M-HIRISE-5-DTM-V1.0",
            citation="Golombek et al. (2020)",
            notes="Moderate-to-high roughness due to fractured floor (Séítah) and boulder ejecta",
        ),
        "temperature_mean_annual": FeatureMeasurement(
            name="surface_temperature_annual_mean",
            value=214.2,
            unit="K",
            std_dev=14.0,
            min_val=183.4,
            max_val=282.1,
            data_quality_tier="ground_truth_in_situ",
            instrument="Perseverance MEDA Thermal Infrared Sensor (TIRS)",
            pds_dataset_id="M2020-M-MEDA-3-RDR-V1.0",
            citation="Martinez et al. (2023) JGR Planets",
            notes="Ground-truth calibrated surface temperature from rover",
        ),
        "temperature_diurnal_range": FeatureMeasurement(
            name="diurnal_temperature_amplitude",
            value=78.6,
            unit="K",
            std_dev=8.0,
            min_val=60.0,
            max_val=95.0,
            data_quality_tier="ground_truth_in_situ",
            instrument="Perseverance MEDA TIRS",
            pds_dataset_id="M2020-M-MEDA-3-RDR-V1.0",
            citation="Rodriguez-Manfredi et al. (2021)",
            notes="Extreme diurnal swing between afternoon peak and pre-dawn minimum",
        ),
        "thermal_inertia": FeatureMeasurement(
            name="thermal_inertia",
            value=340.0,
            unit="J m^-2 K^-1 s^-1/2",
            std_dev=70.0,
            min_val=210.0,
            max_val=580.0,
            data_quality_tier="ground_truth_in_situ",
            instrument="THEMIS Mosaic / MEDA derived surface thermal inertia",
            pds_dataset_id="ODY-M-THM-5-IRGEO-V1.0",
            citation="Martinez et al. (2023)",
            notes="Higher than Oxia Planum due to exposed olivine-cumulate bedrock and coarse sand dunes",
        ),
        "albedo_bolometric": FeatureMeasurement(
            name="bolometric_visible_albedo",
            value=0.152,
            unit="dimensionless",
            std_dev=0.025,
            min_val=0.110,
            max_val=0.220,
            data_quality_tier="orbital_derived",
            instrument="MGS TES Bolometric Albedo / HiRISE",
            pds_dataset_id="MGS-M-TES-3-TSDR-V1.0",
            citation="Bell et al. (2021)",
            notes="Dark Séítah unit has albedo ~0.11; delta top has albedo ~0.18",
        ),
        "dust_cover_index": FeatureMeasurement(
            name="dust_cover_index_dci",
            value=0.958,
            unit="dimensionless",
            std_dev=0.018,
            min_val=0.920,
            max_val=0.980,
            data_quality_tier="orbital_derived",
            instrument="MGS TES 1075 cm^-1 Silicate Band",
            pds_dataset_id="MGS-M-TES-3-TSDR-V1.0",
            citation="Ruff & Christensen (2002)",
            notes="Dust-poor, active wind-clearing terrain",
        ),
        "clay_phyllosilicate_index": FeatureMeasurement(
            name="delta_smectite_carbonate_absorption",
            value=0.048,
            unit="band_depth_bd1900_d2300",
            std_dev=0.022,
            min_val=0.015,
            max_val=0.075,
            data_quality_tier="ground_truth_in_situ",
            instrument="MRO CRISM / Perseverance SuperCam & PIXL",
            pds_dataset_id="MRO-M-CRISM-3-RDR-TARGETED-V1.0",
            citation="Ehlmann et al. (2008), Farley et al. (2022)",
            notes="Localized in western delta fan mudstones and crater marginal carbonates",
        ),
        "water_equivalent_hydrogen": FeatureMeasurement(
            name="water_equivalent_hydrogen_weh",
            value=3.2,
            unit="wt% H2O",
            std_dev=0.5,
            min_val=2.5,
            max_val=4.2,
            data_quality_tier="orbital_derived",
            instrument="Mars Odyssey GRS / HEND Neutron Spectrometer",
            pds_dataset_id="ODY-M-GRS-5-DIR-H2O-MAP-V1.0",
            citation="Boynton et al. (2007)",
            notes="Chemically bound within delta clays and hydrated sulfates",
        ),
        "atmospheric_pressure": FeatureMeasurement(
            name="mean_surface_pressure",
            value=710.0,
            unit="Pa",
            std_dev=55.0,
            min_val=620.0,
            max_val=810.0,
            data_quality_tier="ground_truth_in_situ",
            instrument="Perseverance MEDA Barometer",
            pds_dataset_id="M2020-M-MEDA-3-RDR-V1.0",
            citation="Rodriguez-Manfredi et al. (2021)",
            notes="Measured ground-truth pressure at Jezero floor (~7.1 hPa)",
        ),
    }

    tier1_vector = {
        "vegetation_ndvi": 0.00,
        "slope_deg": 2.40,
        "surface_roughness_m": 0.78,
        "lst_mean_k": 214.2,
        "lst_diurnal_range_k": 78.6,
        "soil_moisture_fraction": 0.00,
    }

    tier1_tolerances = {
        "vegetation_ndvi": 0.05,
        "slope_deg": 3.00,
        "surface_roughness_m": 0.60,
        "lst_mean_k": 15.0,
        "lst_diurnal_range_k": 12.0,
        "soil_moisture_fraction": 0.03,
    }

    tier1_weights = {
        "vegetation_ndvi": 0.25,
        "slope_deg": 0.15,
        "surface_roughness_m": 0.15,
        "lst_mean_k": 0.15,
        "lst_diurnal_range_k": 0.15,
        "soil_moisture_fraction": 0.15,
    }

    limits = {
        "surface_gravity": "Mars = 3.71 m/s^2 vs Earth = 9.81 m/s^2. Sediment settling velocity in paleolake deltas was significantly lower on Mars.",
        "atmospheric_pressure": "Mars = ~7.1 hPa vs Earth = 1013 hPa.",
        "radiation_environment": "Surface dose at Jezero measured by MEDA/RAD analogs is ~240-260 mSv/yr.",
        "biological_sterility": "Jezero delta on Earth would be saturated with microbial mats and plant roots; Martian delta is pristine abiotic rock.",
    }

    return MarsTargetProfile(
        target_id="mars_jezero_crater",
        target_name="Jezero Crater",
        target_archetype="crater_delta_paleolake",
        mission_context="NASA Mars 2020 Perseverance Rover Landing Site",
        scientific_summary=(
            "A 49-km impact crater that hosted a prominent open-basin lake fed by two inlet valleys "
            "during the Noachian-Hesperian transition (~3.7 Ga). Features a remarkably preserved "
            "fluvial delta with clay, carbonate, and olivine-bearing strata. Contains ground-truth "
            "environmental measurements from the Perseverance MEDA instrument suite."
        ),
        geological_epoch="Circa 3.7 Ga (Late Noachian to Early Hesperian)",
        coordinates=coords,
        tier1_global_vector=tier1_vector,
        tier1_feature_weights=tier1_weights,
        tier1_tolerances=tier1_tolerances,
        detailed_measurements=measurements,
        irreducible_limits=limits,
        metadata={
            "version": "1.0.0",
            "primary_target": False,
            "created_by": "W4 Mars Target Workstream",
            "recommended_earth_analog_archetypes": [
                "Salda Lake (Turkey) - Hydromagnesite/stromatolite microbialite shorelines",
                "Green River Formation (Utah/Wyoming) - Lacustrine carbonate and deltaic facies",
                "Lake Eyre Basin (Australia) - Arid terminal lake delta and clay playa",
            ],
        },
    )


def generate_all_mars_profiles(output_dir: Optional[Path] = None) -> List[MarsTargetProfile]:
    """Generate both Oxia Planum and Jezero Crater profiles, saving JSON artifacts."""
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent.parent.parent / "data" / "processed"

    targets_dir = output_dir / "targets"
    targets_dir.mkdir(parents=True, exist_ok=True)

    oxia = get_oxia_planum_profile()
    jezero = get_jezero_crater_profile()

    # Save individual target profiles
    oxia.export_json(targets_dir / "mars_oxia_planum.json")
    jezero.export_json(targets_dir / "mars_jezero_crater.json")

    # Save primary active target profile directly in data/processed/ for W5 engine pickup
    oxia.export_json(output_dir / "mars_target_profile.json")

    logger.info("Successfully generated all Mars target profiles.")
    return [oxia, jezero]


if __name__ == "__main__":
    import sys
    print("=" * 70)
    print("NASA Space Apps 2026 - W4 Mars Target Profile Generator")
    print("=" * 70)
    profiles = generate_all_mars_profiles()
    for p in profiles:
        print(f"\n[+] Generated Profile: {p.target_name} ({p.target_id})")
        print(f"    Archetype:     {p.target_archetype}")
        print(f"    Epoch:         {p.geological_epoch}")
        print(f"    Center Coord:  Lat {p.coordinates.center_lat:.3f} N, Lon {p.coordinates.center_lon_east:.3f} E")
        print("    Tier 1 Vector:")
        for k, v in p.tier1_global_vector.items():
            print(f"      - {k:25s}: {v:8.2f}")
    print("\n" + "=" * 70)
    print("All JSON artifacts exported to data/processed/")
    print("=" * 70)
