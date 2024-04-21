"""Stat System Unit Tests.

"""

from __future__ import annotations

import pathlib

from neighborly.components.stats import StatComponent
from neighborly.ecs import GameObject
from neighborly.helpers.character import create_character
from neighborly.helpers.stats import get_stat, has_stat
from neighborly.loaders import load_characters, load_skills
from neighborly.plugins import default_traits
from neighborly.simulation import Simulation

_TEST_DATA_DIR = pathlib.Path(__file__).parent / "data"


class Hunger(StatComponent):
    """Tracks a GameObject's hunger."""

    __stat_name__ = "hunger"

    MAX_VALUE: int = 1000

    def __init__(
        self,
        gameobject: GameObject,
        base_value: float = 0,
    ) -> None:
        super().__init__(gameobject, base_value, (0, self.MAX_VALUE), True)


def test_has_stat() -> None:
    """Test checking for stats."""
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer.female")

    character.add_component(Hunger(character, 0))

    assert has_stat(character, "hunger") is True

    assert has_stat(character, "health") is False


def test_get_stat() -> None:
    """Test stat retrieval."""
    sim = Simulation()

    load_characters(sim, _TEST_DATA_DIR / "characters.json")
    load_skills(sim, _TEST_DATA_DIR / "skills.json")

    default_traits.load_plugin(sim)

    sim.initialize()

    character = create_character(sim.world, "farmer.female")

    character.add_component(Hunger(character, 0))

    hunger = get_stat(character, "hunger")
    hunger.base_value = 10

    assert hunger.base_value == 10
    assert hunger.value == 10

    hunger.base_value += 100

    assert hunger.base_value == 110
    assert hunger.value == 110
