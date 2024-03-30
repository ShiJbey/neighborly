"""Stat System Unit Tests.

"""

from __future__ import annotations

import pathlib

from neighborly.helpers.character import create_character
from neighborly.helpers.stats import add_stat, get_stat, has_stat
from neighborly.loaders import load_characters, load_skills
from neighborly.plugins import default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


def test_has_stat() -> None:
    """Test checking for stats."""
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer")

    add_stat(character, "hunger", base_value=0, bounds=(0, 255))

    assert has_stat(character, "hunger") is True

    assert has_stat(character, "health") is False


def test_get_stat() -> None:
    """Test stat retrieval."""
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer")

    add_stat(character, "hunger", base_value=0, bounds=(0, 255))

    hunger = get_stat(character, "hunger")
    hunger.base_value = 10

    assert hunger.base_value == 10

    hunger.base_value += 100

    assert hunger.base_value == 110
    assert hunger.value == 110


def test_add_stat() -> None:
    """Test stat addition."""

    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer")

    hunger = add_stat(character, "hunger", base_value=100, bounds=(0, 255))

    assert hunger.base_value == 100
