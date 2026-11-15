# TERRATWIN — Data Flow & Scientific Pipeline Integration
**NASA Space Apps Challenge 2026**

---

## 1. End-to-End Data Flow Diagram

```
[Phase 2: Target Profiles]
   ├── LOLA DEM & Slope (M1, M4, M5) ────────┐
   ├── Diviner Polar Temperature (M3) ───────┼──> target_profiles.json
   └── MOLA MEGDR Topography (Mars) ─────────┘        │
                                                      │
[Phase 3: Scientific Engine]                          │
   ├── ETOPO 2022 & WorldClim 2.1 (Earth) ───┐        │
   ├── Percentile Normalization Matrix ───────┼──> all_target_rankings.json
   └── Multi-Preset Weights (weights.yaml) ───┘   analog_validation.csv
                                                      │
                                                      ▼
                                           [Consolidation Layer]
                                           terratwin_data.json (~68 KB)
                                                      │
                        ┌─────────────────────────────┴─────────────────────────────┐
                        ▼                                                           ▼
               [Mode A: Standalone]                                        [Mode B: REST API]
               Embedded JSON inside                                        server.py (port 8080)
               frontend/index.html                                                  │
                        │                                                           ├── GET /api/targets
                        │                                                           ├── GET /api/similarity/<id>
                        │                                                           └── POST /api/recalculate
                        ▼                                                           │
               Client-Side Canvas &                                                 ▼
               State Dispatcher <───────────────────────────────────────────────────┘
                        │
      ┌─────────────────┼─────────────────┬─────────────────┐
      ▼                 ▼                 ▼                 ▼
[3D Globe / 2D Map] [Ranked Cards]  [Radar Chart]  [Where Analogy Breaks Down]
- Spherical Graticule- Top 10 Scored - 6 Metric Axes- Gravity (0.166g / 0.376g)
- Heat Layer (0-100%)- Famous/Over-  - Earth vs Target - Vacuum / Low Pressure
- Pulsating Pins       looked toggle - Subscore Matrix - Radiation (300-1100 mSv)
- Camera Flight Path - Matching Tags - Units & Bounds  - Regolith Sharpness
```

---

## 2. Dynamic Weight Recalculation Flow

When a user modifies a feature slider (e.g., increases `slope_20km_deg` to 40%):

1. **Event Capture:** Slider `input` event triggers `state.customWeights[key] = value`.
2. **Scoring Dispatch:**
   - In **Offline Mode**, `calculateSimilarity()` iterates through all 15 candidate sites in memory:
     $$d_i = |e_{norm} - t_{norm}|$$
     $$\text{Overall Score} = \left(1 - \frac{\sum w_i d_i}{\sum w_i}\right) \times 100$$
   - In **API Mode**, a JSON POST request is sent to `/api/similarity/recalculate`, which uses `scientific_engine.src.similarity.scoring.SimilarityScorer`.
3. **Reactive Re-sorting:** Candidates are immediately re-sorted by `overall_score` descending.
4. **Synchronized UI Re-render:**
   - Left sidebar cards update ranks, percentage badges, and matching tags.
   - 3D Globe / 2D Map markers update scores, colors (emerald for $\ge 80\%$, cyan for $\ge 70\%$, gold for selected), and heat halo sizes.
   - Comparison Radar Chart smoothly recalculates polygon vertex coordinates.
   - Latency: $< 1\text{ ms}$ client-side, $< 5\text{ ms}$ via local REST API.

---

## 3. Data Integrity & Safety Guardrails

- **Zero Fake Data:** All numbers originate from verified instruments (LRO LOLA, Diviner, MRO CRISM, MGS MOLA, WorldClim 2.1, ETOPO 2022).
- **Coordinate System Segregation:** Earth coordinates (WGS84 lat/lon) are strictly separated from Lunar Polar Stereographic (metres from pole) and Martian Areocentric cylindrical coordinates.
- **Missing Value Handling:** Missing features are flagged with `N/A` and default to neutral distance penalty ($0.5$), never producing artificial $100\%$ scores.
- **Physical Boundary Transparency:** The "Where the Analogy Breaks Down" panel guarantees that high mathematical similarity scores are never misinterpreted as environmental equivalence.
