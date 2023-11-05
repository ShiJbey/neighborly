"""Test Location Preference Functionality.

"""

import pathlib

import pytest

from neighborly.components.location import LocationPreferences
from neighborly.helpers.business import create_business
from neighborly.helpers.character import create_character
from neighborly.helpers.settlement import create_district, create_settlement
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
)
from neighborly.plugins import default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_trait_with_location_preferences() -> None:
    """Test traits that apply social rules"""
    sim = Simulation()

    load_districts(sim, _TEST_DATA_DIR / "districts.json")
    load_settlements(sim, _TEST_DATA_DIR / "settlements.json")
    load_businesses(sim, _TEST_DATA_DIR / "businesses.json")
    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_residences(sim, _TEST_DATA_DIR / "residences.json")
    load_job_roles(sim, _TEST_DATA_DIR / "job_roles.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    settlement = create_settlement(sim.world, "basic_settlement")

    district = create_district(sim.world, settlement, "entertainment_district")

    cafe = create_business(sim.world, district, "cafe")
    bar = create_business(sim.world, district, "bar")

    farmer = create_character(sim.world, "farmer", n_traits=0)

    farmer_preferences = farmer.get_component(LocationPreferences)

    assert farmer_preferences.score_location(cafe) == 0.5
    assert farmer_preferences.score_location(bar) == 0.5

    add_trait(farmer, "drinks_too_much")

    assert farmer_preferences.score_location(cafe) == 0.5
    assert farmer_preferences.score_location(bar) == pytest.approx(0.65, 0.001)  # type: ignore

    remove_trait(farmer, "drinks_too_much")

    assert farmer_preferences.score_location(bar) == 0.5
