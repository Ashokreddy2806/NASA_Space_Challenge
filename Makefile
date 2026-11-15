# Phase-level entry points. Run from NASA_Space_Challenge/.
# On Windows the virtual environment is at ../.venv/Scripts/python.exe.
PYTHON ?= ../.venv/Scripts/python.exe

.PHONY: phase0 phase1 phase2 inventory climate terrain features targets test

phase0: test inventory

phase1: climate terrain features test

phase2: targets test

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

test:
	$(PYTHON) -m pytest -q
