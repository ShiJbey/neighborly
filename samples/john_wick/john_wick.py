"""
John Wick Neighborly Sample
Author: Shi Johnson-Bey
"""
import os
import pathlib
from dataclasses import dataclass

import neighborly.core.name_generation as name_gen
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentDefinition
from neighborly.loaders import YamlDataLoader
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation


@dataclass
class Assassin(Component):
    """Assassin component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0


class AssassinFactory(AbstractFactory):
    """Creates instances of Assassin components"""

    def __init__(self) -> None:
        super().__init__("Assassin")

    def create(self, spec: ComponentDefinition, **kwargs) -> Assassin:
        return Assassin(**spec.get_attributes())


def main():
    data_path = pathlib.Path(os.path.abspath(__file__)).parent / "data.yaml"
    sim = Simulation.create()
    default_plugin.initialize_plugin(sim.engine)
    YamlDataLoader(filepath=data_path).load(sim.engine)
    sim.engine.add_component_factory(AssassinFactory())
    name_gen.register_rule("hitman_first_name", ["John", "Agent"])
    name_gen.register_rule("hitman_last_name", ["Wick", "47"])

    print(sim.engine.create_character("Assassin"))
    print(sim.engine.spawn_place("The Continental Hotel"))


if __name__ == "__main__":
    main()
