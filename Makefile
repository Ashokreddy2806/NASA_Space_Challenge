# Phase-level entry points. Run from NASA_Space_Challenge/.
# Picks the first virtual environment found (macOS/Linux or Windows), else system python.
# Override with:  make test PYTHON=/path/to/python
PYTHON ?= $(firstword $(wildcard .venv/bin/python ../.venv/bin/python ../.venv/Scripts/python.exe) python)

.PHONY: phase0 inventory test

phase0: test inventory

inventory:
	$(PYTHON) -m backend.pipeline.inspect_datasets

test:
	$(PYTHON) -m pytest -q
