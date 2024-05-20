# pylint: disable=#C0104
"""Test Location Preference Functionality.

"""

import pathlib

import pytest

from neighborly.helpers.business import create_business
from neighborly.helpers.character import create_character
from neighborly.helpers.location import score_location
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_settlements,
    load_skills,
    load_species,
)
from neighborly.plugins import (
    default_character_names,
    default_settlement_names,
    default_traits,
)
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


def test_trait_with_location_preferences() -> None:
    """Test traits that apply social rules"""
    sim = Simulation()

    load_districts(sim, _DATA_DIR / "districts.json")
    load_settlements(sim, _DATA_DIR / "settlements.json")
    load_businesses(sim, _DATA_DIR / "businesses.json")
    load_characters(sim, _DATA_DIR / "characters.json")
    load_job_roles(sim, _DATA_DIR / "job_roles.json")
    load_skills(sim, _DATA_DIR / "skills.json")
    load_species(sim, _DATA_DIR / "species.json")

    default_traits.load_plugin(sim)
    default_settlement_names.load_plugin(sim)
    default_character_names.load_plugin(sim)

    sim.initialize()

    cafe = create_business(sim.world, "cafe")
    bar = create_business(sim.world, "bar")

    farmer = create_character(sim.world, "farmer.female")

    assert score_location(farmer, cafe) == 0.5
    assert score_location(farmer, bar) == 0.5

    add_trait(farmer, "drinks_too_much")

    assert score_location(farmer, cafe) == 0.5
    assert score_location(farmer, bar) == pytest.approx(0.65, 0.001)  # type: ignore

    remove_trait(farmer, "drinks_too_much")

    assert score_location(farmer, bar) == 0.5
