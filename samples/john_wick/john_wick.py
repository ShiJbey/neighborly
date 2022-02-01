"""
John Wick Neighborly Sample
Author: Shi Johnson-Bey
"""
import os
import pathlib
from dataclasses import dataclass

import yaml

from neighborly.core.engine import NeighborlyEngine
from neighborly.core.authoring import AbstractFactory


@dataclass
class Assassin:
    """Assassin component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0


@dataclass
class Sniper(Assassin):
    """Advanced component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 9999
    kills: int = 0
    range: int = 10


class AssassinFactory(AbstractFactory):
    """Creates instances of Assassin components"""

    def __init__(self) -> None:
        super().__init__("Assassin")

    def create(self, **kwargs) -> Assassin:
        return Assassin(**kwargs)


class SniperFactory(AbstractFactory):
    """Creates instances of Assassin components"""

    def __init__(self) -> None:
        super().__init__("Sniper")

    def create(self, **kwargs) -> Assassin:
        return Sniper(**kwargs)


def main():
    engine = NeighborlyEngine()
    engine.register_component_factory(AssassinFactory())
    engine.register_component_factory(SniperFactory())

    defs_path = pathlib.Path(os.path.abspath(__file__)).parent / "data.yaml"

    with open(defs_path, "r") as f:
        yaml_data = yaml.safe_load(f)

    engine.load_all_definitions(yaml_data)

    print(engine._character_archetypes["Assassin"])
    print(engine._place_archetypes["The Continental Hotel"])


if __name__ == "__main__":
    main()
