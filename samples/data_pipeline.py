import os
import pathlib
from dataclasses import dataclass

import esper

import neighborly.core.name_generation as name_gen
from neighborly.core.authoring import ComponentSpec, AbstractFactory
from neighborly.engine import NeighborlyEngine
from neighborly.factories.factories import GameCharacterFactory, RoutineFactory, LocationFactory
from neighborly.loaders import YamlDataLoader


@dataclass
class Hitman:
    """Assassin component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0


class HitmanFactory(AbstractFactory):
    """Creates instances of Assassin components"""

    def __init__(self) -> None:
        super().__init__("Hitman")

    def create(self, spec: ComponentSpec) -> Hitman:
        return Hitman(**spec.get_attributes())


def main():
    engine: NeighborlyEngine = NeighborlyEngine()
    engine.add_component_factory(GameCharacterFactory())
    engine.add_component_factory(RoutineFactory())
    engine.add_component_factory(HitmanFactory())
    engine.add_component_factory(LocationFactory())

    name_gen.register_rule("first_name", "Joe")
    name_gen.register_rule("last_name", "Black")
    name_gen.register_rule("hitman_first_name", ["John", "Agent"])
    name_gen.register_rule("hitman_last_name", ["Wick", "47"])

    yaml_path = pathlib.Path(os.path.abspath(__file__)).parent / "all_data.yaml"

    yaml_loader = YamlDataLoader(filepath=yaml_path)

    yaml_loader.load(engine)

    world: esper.World = esper.World()
    
    for _ in range(10):
        civilian_id = engine.create_character(world, "Civilian")
        print(world.components_for_entity(civilian_id))

    hitman_id = engine.create_character(world, "Hitman")
    print(world.components_for_entity(hitman_id))

    grocery_store_id = engine.create_place(world, "Grocery Store")
    print(world.components_for_entity(grocery_store_id))


if __name__ == "__main__":
    main()
