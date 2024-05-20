# pylint: disable=W0621
"""Stat System Unit Tests.

"""

from __future__ import annotations

import pathlib

import pytest

from neighborly.components.stats import StatComponent
from neighborly.helpers.character import create_character
from neighborly.helpers.stats import get_stat, has_stat
from neighborly.libraries import CharacterLibrary
from neighborly.loaders import load_characters, load_skills, load_species
from neighborly.plugins import default_character_names, default_traits
from neighborly.simulation import Simulation

_DATA_DIR = (
    pathlib.Path(__file__).parent.parent / "src" / "neighborly" / "plugins" / "data"
)


class Hunger(StatComponent):
    """Tracks a GameObject's hunger."""

    __stat_name__ = "hunger"

    MAX_VALUE: int = 1000

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


@pytest.fixture
def test_sim() -> Simulation:
    """Create a simulation instance for tests."""

    sim = Simulation()

    default_traits.load_plugin(sim)
    default_character_names.load_plugin(sim)

    load_characters(sim, _DATA_DIR / "characters.json")
    load_skills(sim, _DATA_DIR / "skills.json")
    load_species(sim, _DATA_DIR / "species.json")

    # IMPORTANT: Stop character from generating with traits
    sim.world.resources.get_resource(CharacterLibrary).get_definition(
        "base_character"
    ).traits.clear()

    sim.initialize()

    return sim


def test_has_stat(test_sim: Simulation) -> None:
    """Test checking for stats."""

    character = create_character(test_sim.world, "farmer.female")

    character.add_component(Hunger(0))

    assert has_stat(character, "hunger") is True

    assert has_stat(character, "health") is False


def test_get_stat(test_sim: Simulation) -> None:
    """Test stat retrieval."""

    character = create_character(test_sim.world, "farmer.female")

    character.add_component(Hunger(0))

    hunger = get_stat(character, "hunger")
    hunger.base_value = 10

    assert hunger.base_value == 10
    assert hunger.value == 10

    hunger.base_value += 100

    assert hunger.base_value == 110
    assert hunger.value == 110
