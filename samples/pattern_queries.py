from __future__ import annotations

from typing import List, Optional, Set, Tuple, Type

from neighborly import SimulationBuilder
from neighborly.builtin.helpers import IInheritable, inheritable
from neighborly.core.archetypes import BaseCharacterArchetype
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.query import EcsFindClause, Query, ne_, where, where_not
from neighborly.core.relationship import Relationships
from neighborly.plugins.defaults import DefaultNameDataPlugin


def friendship_gt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.friendship > threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def friendship_lt(threshold: float) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, relationships in world.get_component(Relationships):
            for r in relationships.get_all():
                if r.friendship < threshold:
                    results.append((gid, r.target))
        return results

    return precondition


def has_component(component_type: Type[Component]) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        return list(
            map(lambda result: (result[0],), world.get_component(component_type))
        )

    return precondition


def has_fur_color(fur_color: str) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given fur color"""

    def precondition(world: World):
        return list(
            map(
                lambda result: (result[0],),
                filter(
                    lambda result: fur_color in result[1].values,
                    world.get_component(FurColor),
                ),
            )
        )

    return precondition


@inheritable(always_inherited=True)
class FurColor(Component, IInheritable):

    __slots__ = "values"

    def __init__(self, colors: List[str]) -> None:
        super().__init__()
        self.values: Set[str] = set(colors)

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tcolors: {self.values}")

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

        fur_color = world.get_resource(NeighborlyEngine).rng.choice(
            ["Red", "Green", "Blue", "Yellow", "Orange", "White", "Black", "Purple"]
        )

        gameobject.add_component(FurColor([fur_color]))
        gameobject.add_component(Relationships())

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


def bind_roles(world, query: Query) -> Optional[Tuple[GameObject, ...]]:
    """Searches the ECS for a game object that meets the given conditions"""

    result_set = query.execute(world)

    if len(result_set):
        return tuple(
            map(
                lambda gid: world.get_gameobject(gid),
                world.get_resource(NeighborlyEngine).rng.choice(list(result_set)),
            )
        )

    return None


def main():
    sim = SimulationBuilder(seed=1010).add_plugin(DefaultNameDataPlugin()).build()

    for _ in range(30):
        FuzzCharacterArchetype().create(sim.world)

    query = Query(
        find=("X", "Y"),
        clauses=[
            where(has_component(GameCharacter), "X"),
            where(has_component(HasHorns), "X"),
            where(has_component(GameCharacter), "Y"),
            where_not(has_component(HasHorns), "Y"),
            ne_(("X", "Y")),
        ],
    )

    result = bind_roles(sim.world, query)

    if result:
        for r in result:
            r.pprint()
    else:
        print(None)


if __name__ == "__main__":
    main()
