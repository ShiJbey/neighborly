"""
John Wick Neighborly Sample
Author: Shi Johnson-Bey
"""
import os
import pathlib
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

import yaml

from neighborly.core.authoring import AbstractFactory, CreationData, SpecificationNode
from neighborly.core.engine import NeighborlyEngine

FILE_DIR = pathlib.Path(os.path.abspath(__file__)).parent
DATA_PATH = FILE_DIR / "data.yaml"


@dataclass
class Assassin:
    """Assassin component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0

    def load_data(self, creation_data: CreationData) -> bool:
        """Load data to from creation data"""
        try:
            spec_attrs = creation_data.get_node().get_attributes()
            self.coins = spec_attrs.get("coins", self.coins)
            self.kills = spec_attrs.get("kills", self.kills)
            return True
        except:
            return False


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

    def load_data(self, creation_data: CreationData) -> bool:
        """Load data to from creation data"""
        try:
            spec_attrs = creation_data.get_node().get_attributes()
            self.coins = spec_attrs.get("coins", self.coins)
            self.kills = spec_attrs.get("kills", self.kills)
            self.range = spec_attrs.get("range", self.range)
            return True
        except:
            return False


class DefaultAssassinConstructor:
    def create(self, cd: CreationData) -> Optional[Assassin]:
        if cd.get_node().get_type() != "Assassin":
            return None

        try:
            assassin = Assassin(**cd.get_node().get_attributes())
            return assassin
        except:
            return None

class SniperConstructor:
    def create(self, cd: CreationData) -> Optional[Assassin]:
        if cd.get_node().get_type() != "Assassin":
            return None

        try:
            assassin = Sniper(**cd.get_node().get_attributes())
            return assassin
        except:
            return None


class AssassinFactory(AbstractFactory[Assassin]):
    """Creates instances of Assassin components"""

class ComponentFactory(AbstractFactory[Any]):
    """Creates an instance of something"""


def process_character_definitions(
    engine: NeighborlyEngine, definitions: Dict[str, Dict[str, Any]]
) -> None:
    """Add the character definitions to th specification tree"""
    for name, data in definitions.items():

        # if "GameCharacter" not in data:
        #     raise ValueError("Character definition missing 'GameCharacter' field")

        components: Dict[str, Dict[str, Any]] = data.get("components", {})

        game_obj_def: Dict[str, Any] = {**data}
        del game_obj_def["components"]

        if "GameCharacter" in data:
            components["GameCharacter"] = data["GameCharacter"]
            del game_obj_def["GameCharacter"]

        components["GameObject"] = game_obj_def

        engine.add_character_archetype(name, components)


def process_place_definitions(
    engine: NeighborlyEngine, definitions: Dict[str, Any]
) -> None:
    """Add the place definitions to th specification tree"""
    for name, data in definitions.items():
        engine.add_place_archetype(name, data)


def main():

    engine = NeighborlyEngine()
    component_factory = ComponentFactory()
    component_factory
    engine.register_component_factory()

    with open(DATA_PATH, "r") as f:
        yaml_data = yaml.safe_load(f)

    if "Characters" in yaml_data:
        process_character_definitions(engine, yaml_data["Characters"])

    if "Places" in yaml_data:
        process_place_definitions(engine, yaml_data["Places"])

    print(engine._character_archetypes["Assassin"])
    print(engine._place_archetypes["The Continental Hotel"])

    # assassin_factory = AssassinFactory()
    # # assassin_factory.add_constructor(Assassin, DefaultAssassinConstructor())
    # # assassin_factory.add_constructor(Sniper, DefaultAssassinConstructor())

    # assassin_factory.create(CreationData(SpecificationNode()))


if __name__ == "__main__":
    main()
