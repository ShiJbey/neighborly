# pylint: disable=W0621
"""Test for Neighborly's Trait System.

"""

import pathlib

import pytest

from neighborly.helpers.character import create_character
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.loaders import load_characters, load_skills, load_species, load_traits
from neighborly.plugins import default_character_names, default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


@pytest.fixture
def test_sim() -> Simulation:
    """Create a simulation instance for tests."""

    sim = Simulation()

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")
    load_species(sim, _TEST_DATA_DIR / "species.json")
    load_traits(sim, _TEST_DATA_DIR / "traits.json")

    sim.initialize()

    return sim


def test_add_trait(test_sim: Simulation) -> None:
    """Test that adding a trait makes it visible with has_trait."""

    character = create_character(test_sim.world, "farmer.female")

    assert has_trait(character, "flirtatious") is False

    success = add_trait(character, "flirtatious")

    assert success is True


def test_remove_trait(test_sim: Simulation) -> None:
    """Test that removing a trait makes it not available to has_trait."""

    character = create_character(test_sim.world, "farmer.female")

    assert has_trait(character, "flirtatious") is False

    add_trait(character, "flirtatious")

    assert has_trait(character, "flirtatious") is True

    success = remove_trait(character, "flirtatious")

    assert success is True


def test_add_remove_trait_effects(test_sim: Simulation) -> None:
    """Test that trait effects are added and removed with the trait."""

    farmer = create_character(test_sim.world, "farmer.female")

    get_stat(farmer, "sociability").base_value = 0

    success = add_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 3

    success = remove_trait(farmer, "gullible")

    assert success is True
    assert get_stat(farmer, "sociability").value == 0


def test_try_add_conflicting_trait(test_sim: Simulation) -> None:
    """Test that adding a conflicting trait to a character fails"""

    character = create_character(test_sim.world, "farmer.female")

    success = add_trait(character, "skeptical")

    assert success is True

    success = add_trait(character, "gullible")

    assert success is False

    success = add_trait(character, "skeptical")

    assert success is False
