"""Target profile generation and schema specifications for Moon and Mars analog matching."""

from .mars_target import (
    MarsTargetProfile,
    get_oxia_planum_profile,
    get_jezero_crater_profile,
    generate_all_mars_profiles,
)

__all__ = [
    "MarsTargetProfile",
    "get_oxia_planum_profile",
    "get_jezero_crater_profile",
    "generate_all_mars_profiles",
]
