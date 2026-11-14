# Problem Statement

> NASA Space Apps Challenge: **Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars**
> Levels: Beginner/Youth, Intermediate, Advanced · Subjects: Earth Science, Planets & Moons, Software, Space Exploration

This file describes **what** we are solving. It should rarely change. For **how** and **who**, see [PLAN.md](PLAN.md). For **what has been done**, see [PROGRESS_LOG.md](PROGRESS_LOG.md).

---

## In one sentence

Use open Earth, Moon and Mars data to find places on Earth that resemble candidate Moon-base or Mars landing sites, explain why they're similar and where the similarity breaks down, and present the results as a map, visualization or tool.

## Background

NASA already tests rovers, instruments and astronaut procedures at Earth "analog" sites: the Atacama Desert, Haughton Crater (Canada), Death Valley, Iceland, Hawaii and Antarctica. The problems:

- No place on Earth matches the Moon or Mars completely.
- Different sites are good analogs for different things (geology, temperature, ice, dust, etc.).
- Most analog sites were picked by expert intuition, not by a systematic, data-driven search of the whole planet. Many useful sites have probably never been noticed.

## What the challenge asks for

1. **Find** one or more Earth locations that are useful analogs for a candidate permanent Moon base (in practice, the **lunar south pole**) or a **Mars landing / exploration site**.
2. **Characterize** each one: which features match, how closely, and which don't.
3. **Connect it to exploration**: how the site helps test instruments, train crews, prepare for resource prospecting, search for signs of life, or reduce mission risk.
4. **Be honest about Earth's limits**: Earth can't reproduce low gravity, the Moon's vacuum, Mars's thin atmosphere, or the radiation environment. Saying so is part of a good answer.

## Ways a site can be "analogous"

A site does not need to match all of these:

| Dimension | Examples |
|---|---|
| Geology / minerals / surface materials | basalt, regolith-like soils, sulfates, clays, perchlorates |
| Terrain | elevation, slope, roughness, craters |
| Temperature / sunlight / extremes | cold traps, diurnal range, low sun angle, polar illumination |
| Water / ice / permafrost | buried ice, permafrost, hydrated minerals |
| Dust / wind / erosion | dust storms, aeolian features, dunes |
| Biology / habitability | extremophiles, signs of past life |
| Caves / lava tubes / subsurface | lava tubes, ice caves |
| Engineering conditions | landing, rover driving, construction |

**Processes count, not just places.** E.g. a dust storm, sediment deposition, or ice movement on Earth can explain the same process on Mars.

## What judges reward

- **Don't just rediscover famous sites.** Atacama, Antarctica, Iceland and Hawaii are well studied. Prefer an **overlooked site found with global NASA data**.
- **Back up similarity with data**, not "it looks like Mars."
- **Think about scale.** A single crater, valley or lava tube can be a stronger match than a whole desert.
- **Methods are open:** one detailed site study, a comparison of several sites, or a system that ranks every place on Earth by similarity (GIS, statistics, ML, interactive app).
- **"Surprise us":** an unexpected location or connection.

## Data sources (portals, not ready-made datasets — we pick specific products)

### Earth (NASA)
- **NASA Earthdata Search** — https://search.earthdata.nasa.gov/ — land surface temperature (MODIS), elevation (SRTM/ASTER), mineral maps (EMIT, ASTER), soil moisture (SMAP), dust.
- **NASA Worldview** — https://worldview.earthdata.nasa.gov/ — visual browsing; quick checks of candidate sites.

### Moon and Mars (NASA)
- **Planetary Data System (PDS)** — https://pds.nasa.gov/ — archive for all Moon and Mars mission data. Mars data comes from here.
- **LRO at PDS Geosciences** — https://pds-geosciences.wustl.edu/missions/lro/ — LROC (cameras), LOLA (elevation), Diviner (temperature), LEND (hydrogen / ice indicator), Mini-RF (radar).
- **LRO Diviner** — https://pds-geosciences.wustl.edu/missions/lro/diviner.htm — lunar surface temperatures, polar and resource products. Suggested: compare with Earth's coldest, ice-bearing places.

### Partner agencies
- **CSA**: [RADARSAT Constellation](https://donnees-data.asc-csa.gc.ca/en/dataset/rcm), [RADARSAT-1 archive](https://donnees-data.asc-csa.gc.ca/en/dataset/radarsat1) (radar; sees through clouds, day/night — ice & surface texture), [SAR Python tutorial](https://github.com/asc-csa/Synthetic_Aperture_Radar_Tutorial).
- **ESA**: [Copernicus Data Space](https://dataspace.copernicus.eu/) (Sentinel optical/radar/atmosphere), [ESA Open Science Catalog](https://opensciencedata.esa.int/).
- **JAXA**: [G-Portal](https://gportal.jaxa.jp/gpr/index/index) (precipitation, snow, vegetation, …).

## Team constraints

- **Team:** Rahul, Ashok, Mrinalini (3 people). Everyone uses AI coding assistants.
- **Time:** ~24 hours to submission.
- **Hardware:** Macs with ~8 GB RAM. Use **coarse global grids (~1–5 km/pixel)** for the worldwide search; download high-resolution data **only for the top few candidates**. Avoid raw SAR except for a single site.
- **Stack:** Python backend; the visualization must look **really good** (it's a big part of how judges see the project).

## Our angle (summary)

Describe every location (Earth grid cell, a Moon site, a Mars site) as a **vector of measurable features** (temperature, roughness, slope, minerals, moisture, vegetation, ice, …), then **rank every place on Earth** by similarity to a target (e.g. lunar south pole, Jezero Crater), with per-feature breakdowns showing what matches and what doesn't — and explicitly list what Earth can never match.
