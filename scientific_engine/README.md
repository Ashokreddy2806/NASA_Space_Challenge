# Scientific Engine (Phase 2 & Phase 3)
**NASA Space Apps Challenge — Planetary Analogs Project**

This package is the self-contained scientific implementation of **Phase 2 (W3 Moon, W4 Mars Target Profiles)** and **Phase 3 (W5 Similarity Engine)**.

It operates strictly on verified planetary datasets, published literature constraints, and normalized percentile geometries, ensuring that no artificial or guessed values enter the scientific pipeline.

---

## 1. Directory Structure

```
scientific_engine/
│
├── README.md                           <-- Complete documentation & user guide
├── requirements.txt                    <-- Optional dependencies (runs pure-python)
├── config/
│   ├── targets.yaml                    <-- Target AOIs, CRS definitions, and sites
│   ├── features.yaml                   <-- Feature definitions and calculation formulas
│   └── weights.yaml                    <-- Presets (Rover Mobility, Cold Trap, Thermal)
│
├── data/
│   ├── raw/                            <-- Local raw data folder
│   ├── processed/                      <-- Processed intermediate grids
│   └── metadata/                       <-- Verified peer-reviewed literature CSVs
│       ├── moon_thermal_literature.csv
│       └── mars_thermal_literature.csv
│
├── src/
│   ├── data/                           <-- Ingestion, catalog discovery, reprojection
│   │   ├── discovery.py
│   │   ├── loading.py
│   │   ├── validation.py
│   │   └── reprojection.py
│   │
│   ├── profiles/                       <-- Phase 2 target profile generation
│   │   ├── moon_profile.py
│   │   ├── mars_profile.py
│   │   └── profile_generator.py
│   │
│   ├── similarity/                     <-- Phase 3 mathematical similarity engine
│   │   ├── normalization.py
│   │   ├── distance.py
│   │   ├── scoring.py
│   │   ├── weights.py
│   │   ├── ranking.py
│   │   └── validation.py
│   │
│   ├── visualization/                  <-- High-resolution vector plots and maps
│   │   ├── distributions.py
│   │   ├── similarity_maps.py
│   │   └── comparisons.py
│   │
│   └── main.py                         <-- Master pipeline runner
│
├── outputs/                            <-- Generated scientific artifacts
│   ├── profiles/                       <-- target_profiles.json
│   ├── plots/                          <-- Distribution & multi-axis radar charts
│   ├── maps/                           <-- Cartographic world similarity maps
│   ├── rankings/                       <-- Top 10 rankings (all & overlooked)
│   ├── validation/                     <-- analog_validation.csv
│   └── run_metadata.json               <-- Complete reproducibility audit
│
└── tests/                              <-- Comprehensive automated test suite
    ├── test_data.py
    ├── test_profiles.py
    ├── test_normalization.py
    ├── test_scoring.py
    ├── test_weights.py
    └── test_geospatial.py
```

---

## 2. Core Scientific Principles

1. **Physical Estimators in Kilometre Windows (docs/FEATURES.md contract):**
   * Pixel counts vary wildly across planetary sensors (80 m for LOLA polar DEM, ~3.7 km for Mars MOLA, ~1.85 km for ETOPO).
   * All relief, slope, and roughness features are evaluated across matched **5, 10, and 20 km physical metric windows**.
2. **Percentile Space Normalization:**
   * Raw values (e.g. slopes in degrees vs roughness in metres) cannot be averaged linearly.
   * Every feature is normalized to its percentile rank $p \in [0, 1]$ relative to Earth's global land distribution.
3. **One-Sided Dryness Constraints:**
   * Airless (Moon) and hyper-arid (Mars) surfaces have strictly 0.0 mm precipitation.
   * Dryness acts as a one-sided penalty function: any precipitation on Earth increases distance from the target.
4. **Target Region Geometry:**
   * **Moon South Pole:** Evaluated under Moon 2015 South Polar Stereographic coordinates (metres vs $1737.4\text{ km}$ sphere). Never treated as longitude/latitude.
   * **Mars (Jezero Crater & Oxia Planum):** Evaluated under MOLA simple cylindrical coordinates with longitude $0\dots360^\circ\text{E}$.
   * **Thermal Values:** Strictly sourced from peer-reviewed ground truth and published climatology (Williams et al. 2019 for Moon; Putzig et al. and Martinez et al. 2023 for Mars).

---

## 3. Presets & Weight Configurations

Managed in `config/weights.yaml`:
* **Rover Mobility:** Focuses on terrain slope ($30\%$), multi-scale roughness ($45\%$), and relief ($15\%$). Tests chassis clearance, grousers, and slope climbing.
* **Cold-Trap / Ice:** Focuses on coldest-month minimum temperature ($35\%$), mean temperature ($20\%$), and permanently shadowed region presence ($25\%$). Tests cryogenic volatile stability.
* **Thermal Cycling:** Focuses on diurnal temperature range ($35\%$), annual temperature range ($25\%$), and mean temperature ($20\%$). Tests thermal fatigue and battery cycling.
* **Balanced Default:** Equalized distribution across terrain, thermal, and dryness dimensions.

---

## 4. Execution & Testing

### Run the Complete Pipeline:
```bash
python3 scientific_engine/src/main.py
```

### Run the Automated Test Suite:
```bash
python3 -m unittest discover -s scientific_engine/tests -p "test_*.py"
```
