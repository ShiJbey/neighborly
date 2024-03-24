"""Stat System Unit Tests.

"""

from __future__ import annotations

import pathlib

from neighborly.components.stats import Stat
from neighborly.defs.base_types import CharacterGenOptions
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

    character = create_character(sim.world, CharacterGenOptions(definition_id="farmer"))

    assert has_stat(character, "hunger") is False

    assert has_stat(character, "health") is True


def test_get_stat() -> None:
    """Test stat retrieval."""
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, CharacterGenOptions(definition_id="farmer"))

    health = get_stat(character, "health")
    health.base_value = 10

    assert health.base_value == 10

    health.base_value += 100

    assert health.base_value == 110
    assert health.value == 110


def test_add_stat() -> None:
    """Test stat addition."""

    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, CharacterGenOptions(definition_id="farmer"))

    hunger = add_stat(
        character, Stat(name="hunger", base_value=100, min_value=0, max_value=255)
    )

    assert hunger.base_value == 100
