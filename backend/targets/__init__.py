"""Target profiles for the Moon and Mars, and the Earth-side Phase 2 outputs.

Modules:

* :mod:`backend.targets.psr` — PSR parsing, rasterising and data-driven checks.
* :mod:`backend.targets.thermal` — cited-CSV reader; never invents values.
* :mod:`backend.targets.geometry` — body-CRS helpers (PROJ refuses Earth CRS).
* :mod:`backend.targets.distribution` — median/spread/min/max summaries.
* :mod:`backend.targets.moon_target` — 85°S disc profile from the 80 m DEM.
* :mod:`backend.targets.mars_target` — Jezero 150 km disc from raw MOLA.
* :mod:`backend.targets.hurst_sensitivity` — Hurst with and without the 2 km lag.
"""

from backend.targets.distribution import profile_entry, summarise

__all__ = ["profile_entry", "summarise"]
