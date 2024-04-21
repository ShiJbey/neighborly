# pylint: disable=redefined-outer-name
"""Test Relationship Components, Systems, and Helper Functions.

"""

import pathlib

import pytest

from neighborly.helpers.character import create_character
from neighborly.helpers.relationship import (
    add_relationship,
    get_relationship,
    has_relationship,
)
from neighborly.helpers.stats import get_stat
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


@pytest.fixture
def sim() -> Simulation:
    """Create sample simulation to use for test cases"""
    simulation = Simulation()

    load_districts(simulation, _TEST_DATA_DIR / "districts.json")
    load_settlements(simulation, _TEST_DATA_DIR / "settlements.json")
    load_businesses(simulation, _TEST_DATA_DIR / "businesses.json")
    load_characters(simulation, _TEST_DATA_DIR / "characters.json")
    load_residences(simulation, _TEST_DATA_DIR / "residences.json")
    load_job_roles(simulation, _TEST_DATA_DIR / "job_roles.json")
    load_skills(simulation, _TEST_DATA_DIR / "skills.json")
    default_traits.load_plugin(simulation)

    simulation.initialize()

    return simulation


def test_get_relationship(sim: Simulation) -> None:
    """Test that get_relationship creates new relationship if one does not exist."""

    a = create_character(sim.world, "person.female")
    b = create_character(sim.world, "person.male")

    assert has_relationship(a, b) is False
    assert has_relationship(b, a) is False

    a_to_b = get_relationship(a, b)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is False

    b_to_a = get_relationship(b, a)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is True

    assert id(a_to_b) != id(b_to_a)

    a_to_b_again = get_relationship(a, b)

    assert id(a_to_b) == id(a_to_b_again)


def test_add_relationship(sim: Simulation) -> None:
    """Test that adding a relationship create a new relationship or returns the old"""

    a = create_character(sim.world, "person.male")
    b = create_character(sim.world, "person.female")

    assert has_relationship(a, b) is False
    assert has_relationship(b, a) is False

    add_relationship(a, b)

    assert has_relationship(a, b) is True
    assert has_relationship(b, a) is False


def test_trait_with_social_rules(sim: Simulation) -> None:
    """Test traits that apply social rules"""

    farmer = create_character(sim.world, "farmer.female")
    merchant = create_character(sim.world, "merchant.male")
    noble = create_character(sim.world, "nobility.female")

    rel_to_noble = add_relationship(farmer, noble)

    assert get_stat(rel_to_noble, "reputation").value == 0

    add_trait(farmer, "gullible")

    assert get_stat(rel_to_noble, "reputation").value == 5

    rel = add_relationship(farmer, merchant)

    assert get_stat(rel, "reputation").value == 5

    remove_trait(farmer, "gullible")

    assert get_stat(rel, "reputation").value == 0
    assert get_stat(rel_to_noble, "reputation").value == 0
