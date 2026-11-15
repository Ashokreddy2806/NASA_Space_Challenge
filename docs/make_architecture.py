"""Draw docs/figures/architecture.png.  Run: python docs/make_architecture.py"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

COLS = {"data": "#2b3a55", "pipe": "#1f6f8b", "engine": "#7a5cff", "api": "#c05621", "ui": "#2f855a"}
BOXES = [  # x, y, w, h, kind, text
    (0.2, 6.2, 2.6, 1.3, "data", "Moon: LOLA 80 m DEM,\nroughness/slope/Hurst,\nPSR polygons"),
    (0.2, 4.2, 2.6, 1.3, "data", "Mars: MOLA 16 ppd\n(Jezero)"),
    (0.2, 2.2, 2.6, 1.3, "data", "Earth: ETOPO 2022,\nWorldClim 2.1"),
    (0.2, 0.2, 2.6, 1.3, "data", "Literature CSVs\n(temperatures, cited)"),
    (3.5, 5.2, 2.9, 1.5, "pipe", "Phase 2\ntarget_profiles.py\n2 km grid, same estimators"),
    (3.6, 2.2, 2.6, 1.5, "pipe", "Phase 1\nEarth 0.05° feature grid\n13 features, land mask"),
    (7.0, 3.7, 2.6, 1.7, "engine", "Phase 3 engine\nEarth-percentile scale,\nweighted distance, presets"),
    (10.4, 3.7, 2.4, 1.7, "api", "Phase 4 FastAPI\nscore.png, top sites,\nsite breakdown"),
    (13.4, 3.7, 2.4, 1.7, "ui", "Phase 5 map app\ndeck.gl + MapLibre\n+ Plotly"),
]
fig, ax = plt.subplots(figsize=(16, 7.6))
for x, y, w, h, k, t in BOXES:
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=COLS[k], ec="none"))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", color="white", fontsize=10.5)
for a, b in [((2.8, 6.8), (3.6, 6.1)), ((2.8, 4.8), (3.6, 5.6)), ((2.8, 2.9), (3.6, 2.95)), ((2.8, 0.9), (3.6, 5.3)),
             ((6.2, 5.9), (7.0, 4.9)), ((6.2, 2.95), (7.0, 4.2)), ((9.6, 4.55), (10.4, 4.55)), ((12.8, 4.55), (13.4, 4.55))]:
    ax.annotate("", xy=b, xytext=a, arrowprops=dict(arrowstyle="-|>", color="#555", lw=1.6))
ax.text(8.0, 7.6, "Earth Analog Finder: data to map", ha="center", fontsize=15, weight="bold")
ax.text(8.0, -0.5, "Every target value is placed on the Earth percentile scale; temperatures stay unscored until "
        "site-specific cited values exist.", ha="center", fontsize=10, color="#444")
ax.set_xlim(0, 16), ax.set_ylim(-1, 8), ax.axis("off")
fig.savefig("docs/figures/architecture.png", dpi=130, bbox_inches="tight", facecolor="white")
