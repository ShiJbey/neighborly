"""Loads a default set of first names, and last names for characters.

"""

import pathlib
import random
from typing import Union

from neighborly.ecs import World
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


from neighborly.libraries import CharacterNameFactories, ICharacterNameFactory


class SimpleNameFactory(ICharacterNameFactory):

    __slots__ = ("names",)

    names: list[str]

    def __init__(self, name_file: Union[str, pathlib.Path]) -> None:
        with open(name_file, "r", encoding="utf8") as f:
            self.names = f.read().splitlines()

    def __call__(self, world: World) -> str:
        rng = world.resources.get_resource(random.Random)

        return rng.choice(self.names)


def load_plugin(sim: Simulation) -> None:
    """Load the plugin's content."""

    name_factories = sim.world.resources.get_resource(CharacterNameFactories)

    name_factories.add_factory(
        "masculine-first",
        SimpleNameFactory(_DATA_DIR / "masculine_first_names.txt"),
        ["male"],
    )

    name_factories.add_factory(
        "feminine-first",
        SimpleNameFactory(_DATA_DIR / "feminine_first_names.txt"),
        ["female"],
    )

    name_factories.add_factory(
        "default-last", SimpleNameFactory(_DATA_DIR / "last_names.txt")
    )
