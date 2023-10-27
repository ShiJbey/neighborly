"""A plugin with sample content.

"""

import pathlib

from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
    load_tracery,
    load_traits,
)
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent.parent / "tests" / "data"


def load_plugin(sim: Simulation) -> None:
    """Load plugin content."""

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_traits(sim, _TEST_DATA_DIR / "traits.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")
    load_tracery(
        sim,
        _TEST_DATA_DIR / "character_names.tracery.json",
    )
    load_tracery(
        sim,
        _TEST_DATA_DIR / "settlement_names.tracery.json",
    )
