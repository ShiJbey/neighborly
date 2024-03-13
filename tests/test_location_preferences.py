"""Test Location Preference Functionality.

"""

import pathlib

import pytest

from neighborly.defs.base_types import (
    BusinessGenOptions,
    CharacterGenOptions,
    DistrictGenOptions,
    SettlementGenOptions,
)
from neighborly.helpers.business import create_business
from neighborly.helpers.character import create_character
from neighborly.helpers.location import score_location
from neighborly.helpers.settlement import create_district, create_settlement
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.loaders import (
    load_businesses,
    load_characters,
    load_districts,
    load_job_roles,
    load_residences,
    load_settlements,
    load_skills,
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
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    settlement = create_settlement(
        sim.world, SettlementGenOptions(definition_id="basic_settlement")
    )

    district = create_district(
        sim.world,
        settlement,
        DistrictGenOptions(definition_id="entertainment_district"),
    )

    cafe = create_business(
        sim.world, district, BusinessGenOptions(definition_id="cafe")
    )

    bar = create_business(sim.world, district, BusinessGenOptions(definition_id="bar"))

    farmer = create_character(sim.world, CharacterGenOptions(definition_id="farmer"))

    assert score_location(farmer, cafe) == 0.5
    assert score_location(farmer, bar) == 0.5

    add_trait(farmer, "drinks_too_much")

    assert score_location(farmer, cafe) == 0.5
    assert score_location(farmer, bar) == pytest.approx(0.65, 0.001)  # type: ignore

    remove_trait(farmer, "drinks_too_much")

    assert score_location(farmer, bar) == 0.5
