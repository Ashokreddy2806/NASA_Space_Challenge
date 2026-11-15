# Phase-level entry points. Run from NASA_Space_Challenge/.
# Picks the first virtual environment found (macOS/Linux or Windows), else system python.
# Override with:  make test PYTHON=/path/to/python
PYTHON ?= $(firstword $(wildcard .venv/bin/python ../.venv/bin/python ../.venv/Scripts/python.exe) python)

.PHONY: phase0 phase1 phase2 phase3 all serve inventory climate terrain features targets scores test

phase0: test inventory

phase1: climate terrain features test

phase2: targets test

phase3: scores test

# Rebuild every result from the raw data in ../Datasets (about 15 minutes), then test.
all: climate terrain features targets scores test

# API + map app at http://localhost:8000/
serve:
	$(PYTHON) -m uvicorn backend.api.main:app --port 8000

inventory:
	$(PYTHON) -m backend.pipeline.inspect_datasets

climate:
	$(PYTHON) -m backend.pipeline.earth_climate

terrain:
	$(PYTHON) -m backend.pipeline.earth_terrain

features:
	$(PYTHON) -m backend.pipeline.build_earth_features

targets:
	$(PYTHON) -m backend.targets.build_target_profiles

scores:
	$(PYTHON) -m backend.engine.build_scores

test:
	$(PYTHON) -m pytest -q
