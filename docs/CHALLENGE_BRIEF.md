# Challenge brief (reference)

**NASA Space Apps Challenge 2026 — Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars**
Difficulty: Beginner/Youth, Intermediate, Advanced · Subjects: Earth Science, Planets & Moons, Software, Space Exploration
Source: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/

This is a condensed copy of the official brief, kept so the team and AI assistants share one reading of the goal.
See [PROBLEM_STATEMENT.md](../PROBLEM_STATEMENT.md) for our interpretation and [PLAN.md](../PLAN.md) for the approach.

## The ask

Use open Earth, Moon and Mars data from NASA and other space agencies to **identify and characterize new terrestrial analogs** for future Moon bases or Mars landing and exploration sites, then **present the findings as a map, visualization or other tool**. Look at deserts, polar regions, volcanic and arid terrain, caves and other environments that share conditions with the lunar or Martian surface.

Known analogs (Atacama, Haughton Crater, Death Valley) exist, but terrestrial analog sites are not well characterized, and no place on Earth reproduces another body completely. Different places are good analogs for different characteristics.

## Objectives

- Identify and characterize one or more Earth locations that are useful analogs for a candidate Moon-base location or a Mars site.
- Explain what makes each one analogous, which characteristics or processes are a strong match, **where the analogy breaks down**, and how studying it helps prepare lunar or Mars exploration.
- The goal is **not** to rediscover famous sites or to find one place that merely looks like the Moon or Mars. Combine datasets creatively; explain similarity with data, not appearance.
- Format is open: written report, interactive map, visualization, app, similarity-ranking system, ML tool, or a single compelling site.

## Dimensions of analogy (any subset is fine)

- Geology, mineralogy, surface materials
- Terrain: elevation, slope, roughness, craters
- Temperature, illumination, environmental extremes
- Water, ice, permafrost, other resources
- Dust, wind, erosion, atmospheric and surface processes (processes count, not only places)
- Biology, extremophiles, habitability, biosignatures
- Caves, lava tubes, subsurface environments
- Conditions for landing, mobility, navigation, robotics, human exploration, construction

## Considerations

- An analog does not have to match everything; say what is similar, how similar, and what differs.
- Look beyond Antarctica, Atacama, Iceland and Hawaii; global Earth-observation data may reveal less-studied places.
- Consider scale: a single crater, valley, volcanic field or cave can beat a whole desert.
- Connect the analog to exploration: testing instruments and technology, rehearsing operations, resource search, habitability, risk reduction.
- Earth cannot reproduce reduced gravity, the lunar vacuum, the thin Martian atmosphere or the radiation environment; stating this is part of good analysis.
- "Surprise us": an unexpected location, or an unexpected connection between Earth and the Moon or Mars.

## How this project answers it

A data-driven similarity search over the whole Earth (0.05° grid) against the lunar south pole and Jezero, Mars: per-feature evidence, honest "does not match" and "Earth cannot replicate" notes, and an interactive 3D globe on satellite imagery for presenting results.
