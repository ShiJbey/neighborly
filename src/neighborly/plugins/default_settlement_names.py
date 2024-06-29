"""Loads a default set of names for settlements.

"""

import pathlib
import random
from typing import Union

from neighborly.ecs import World
from neighborly.libraries import SettlementNameFactories
from neighborly.simulation import Simulation

_DATA_DIR = pathlib.Path(__file__).parent / "data"


class SimpleNameFactory:

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

    name_factories = sim.world.resources.get_resource(SettlementNameFactories)

    name_factories.add_factory(
        "default", SimpleNameFactory(_DATA_DIR / "settlement_names.txt")
    )
