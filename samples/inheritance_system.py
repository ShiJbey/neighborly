"""
This is another attempt at improving the entity generation process. As I have gained
a better understanding of how I should model characters, it has helped realize the
problems with previous interfaces. For this iteration, we are breaking apart the pieces
of characters into more individual components and placing probabilities on those
components being present at spawn-time.
"""
from __future__ import annotations

import pprint
import random
from typing import List, Optional, Set

from neighborly.builtin.archetypes import BaseCharacterArchetype
from neighborly.builtin.helpers import generate_child
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.inheritable import IInheritable, inheritable
from neighborly.plugins.defaults import DefaultNameDataPlugin
from neighborly.simulation import SimulationBuilder


@inheritable(always_inherited=True)
class FurColor(Component, IInheritable):

    __slots__ = "values"

    def __init__(self, colors: List[str]) -> None:
        super().__init__()
        self.values: Set[str] = set(colors)

    @classmethod
    def from_parents(cls, *components: FurColor) -> FurColor:
        all_colors = set()
        for parent in components:
            for color in parent.values:
                all_colors.add(color)

        return FurColor(list(all_colors))


class FuzzCharacterArchetype(BaseCharacterArchetype):
    def create(self, world: World, **kwargs) -> GameObject:
        gameobject = super().create(world, **kwargs)

        fur_color = random.choice(
            ["Red", "Green", "Blue", "Yellow", "Orange", "White", "Black", "Purple"]
        )

        gameobject.add_component(FurColor([fur_color]))

        if world.get_resource(NeighborlyEngine).rng.random() < 0.3:
            gameobject.add_component(HasHorns())

        return gameobject


@inheritable(inheritance_chance=(0.5, 0.7))
class HasHorns(Component, IInheritable):
    @classmethod
    def from_parents(
        cls, parent_a: Optional[Component], parent_b: Optional[Component]
    ) -> Component:
        return HasHorns()


def main():
    sim = SimulationBuilder().add_plugin(DefaultNameDataPlugin()).build()

    c1 = FuzzCharacterArchetype().create(sim.world)
    c2 = FuzzCharacterArchetype().create(sim.world)
    c3 = generate_child(sim.world, c1, c2)

    pprint.pprint(c1.to_dict())
    pprint.pprint(c2.to_dict())
    pprint.pprint(c3.to_dict())


if __name__ == "__main__":
    main()
