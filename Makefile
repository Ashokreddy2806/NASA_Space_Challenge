# Phase-level entry points. Run from NASA_Space_Challenge/.
# On Windows the virtual environment is at ../.venv/Scripts/python.exe.
PYTHON ?= ../.venv/Scripts/python.exe

.PHONY: phase0 inventory test

phase0: test inventory

inventory:
	$(PYTHON) -m backend.pipeline.inspect_datasets

test:
	$(PYTHON) -m pytest -q
