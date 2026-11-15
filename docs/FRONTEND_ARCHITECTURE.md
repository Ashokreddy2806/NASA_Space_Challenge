# TERRATWIN — Frontend Architecture Documentation
**Phase 5 Deliverable | NASA Space Apps Challenge 2026**

---

## 1. Architectural Philosophy

TERRATWIN is designed as an interactive, spatially rich, planetary exploration planning platform. It adheres to three core architectural principles:

1. **Map-First Spatial Immersion:** The interactive Earth canvas fills 100% of the viewport. UI elements float as translucent glassmorphism HUD panels over the map rather than confining the map to a widget.
2. **True Scientific Data Coupling:** The frontend renders verified measurements directly from Phase 2 (Target Profiles) and Phase 3 (Similarity Engine). It never fabricates mock numbers or fake heatmaps.
3. **Dual Execution Mode (Zero Dependencies):**
   - **Mode A (Standalone File):** Operates as a completely self-contained single file (`frontend/index.html`) with embedded JSON payload and client-side scoring logic. Runs offline via `file://` in any browser without npm, node, or web servers.
   - **Mode B (REST API Driven):** Connects to `frontend/server.py` (pure Python standard library) via `/api/` endpoints to dynamically recalculate complex queries and serve live payloads.

---

## 2. Component Structure

```
frontend/
├── index.html              # Master standalone application (HTML5/CSS3/Canvas/JS)
├── server.py               # REST API & static server (zero external dependencies)
├── build_index.py          # Generator injecting verified Phase 2/3 datasets
├── terratwin_data.json     # Consolidated Phase 2 & 3 JSON payload (~68 KB)
├── README.md               # Quickstart and usage manual
└── tests/
    └── test_api.py         # Automated test suite (7 passing unit/integration tests)
```

### Key UI Subsystems

1. **Top HUD Header:**
   - **Planetary Target Selector:** Instant toggle between `moon_south_pole`, `mars_jezero_crater`, and `mars_oxia_planum`. Updates mission profile, ranking list, radar chart, and mini-target HUD.
   - **Mission Preset Selector:** Quick-switches between `balanced_default`, `rover_mobility`, `cold_trap_ice`, and `thermal_cycling`.
   - **View Mode Switcher:** Seamless transition between **3D Globe** (spherical projection with orbital starfield) and **2D Map** (Equirectangular $-180^\circ$ to $+180^\circ$ projection).
   - **Camera Reset & Telemetry Status.**

2. **Left Sidebar — Ranked Candidate Dossiers:**
   - Scrollable card stack sorted by overall similarity score.
   - Filter pills: `All Sites (15)`, `Famous Only (5)`, `Overlooked Only (10)`.
   - Search bar filtering dynamically by site name, country, or coordinates.
   - Per-card micro-visuals: Rank badge, score badge, top 2 matching features (`[✓]`), top 2 deviating features (`[✕]`), and one-click `Fly to Site →` trigger.

3. **Center Viewport — Interactive Canvas Engine:**
   - **3D Globe Engine:** Custom spherical coordinates transformation ($x = r\cos\phi\sin\theta$, $y = -r\sin\phi$, $z = r\cos\phi\cos\theta$) with pitch and yaw rotations, smooth inertia, mouse drag, and wheel zoom.
   - **Spatial Heat Layer:** Renders continuous radial heat halos around candidate coordinate centroids with color-coded intensity ($0\%$ dark slate $\rightarrow$ $70\%$ cyan $\rightarrow$ $80\%$ emerald $\rightarrow$ $100\%$ gold).
   - **Pulsating Radar Pins:** Animated multi-ring radar markers centered on candidate locations.
   - **2D Flat Map Engine:** Full rectangular projection with latitude/longitude graticules at $30^\circ$ intervals and heat dissipation envelopes.

4. **Right Sidebar — Multi-Tab Analytics:**
   - **Tab 1: Comparison HUD:** Dual-polygon Canvas Radar Chart plotting Earth Site vs Planetary Target across 6 key axes, plus a detailed feature matrix with units, target values, Earth values, and subscores.
   - **Tab 2: Where the Analogy Breaks Down:** Visually distinct warning panel detailing the fundamental physical limits that Earth cannot replicate (gravity, atmosphere, radiation, regolith abrasiveness, cryogenic cold traps).
   - **Tab 3: Weight Calibration:** 8 real-time sliders allowing users to dynamically adjust feature weights with instant recalculation of all candidate rankings in $<1\text{ ms}$.
   - **Tab 4: Target Overview:** Detailed metadata for the selected planetary target, including AOI bounding box, CRS, geological epoch, and instrument data provenance.

5. **Mini-Target HUD (Lower Right):**
   - Segregated coordinate viewer displaying the planetary target's local topography, crater contours, and CRS. Strictly separated from Earth geography to prevent coordinate confusion.

6. **Bottom HUD Footer:**
   - Continuous color gradient scale bar ($0\%$ to $100\%$).
   - Opacity slider controlling the spatial heat layer opacity from $0\%$ to $100\%$.
   - Live telemetry status: Active target ID, Active preset ID, Cursor latitude/longitude coordinates.
