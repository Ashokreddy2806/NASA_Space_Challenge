"""Shared pytest fixtures.

The whole suite reads its geometry, feature list, file names and validation
sites from ``config/*.yaml`` so a config change is the only way to change what
is tested.
"""

from __future__ import annotations

import pytest

from backend.config import AppConfig, load_config


@pytest.fixture(scope="session")
def config() -> AppConfig:
    return load_config()
