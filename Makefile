# Phase-level entry points. Run from NASA_Space_Challenge/.
# Picks the first virtual environment found (macOS/Linux or Windows), else system python.
# Override with:  make test PYTHON=/path/to/python
PYTHON ?= $(firstword $(wildcard .venv/bin/python ../.venv/bin/python ../.venv/Scripts/python.exe) python)

.PHONY: phase0 phase1 inventory climate terrain features test

phase0: test inventory

phase1: climate terrain features test

inventory:
	$(PYTHON) -m backend.pipeline.inspect_datasets

climate:
	$(PYTHON) -m backend.pipeline.earth_climate

terrain:
	$(PYTHON) -m backend.pipeline.earth_terrain

features:
	$(PYTHON) -m backend.pipeline.build_earth_features

test:
	$(PYTHON) -m pytest -q
