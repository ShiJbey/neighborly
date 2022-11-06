from __future__ import annotations

from enum import IntEnum, auto
from typing import List, Optional, Protocol, Set, Tuple, Type

from neighborly.builtin.helpers import IInheritable, inheritable
from neighborly.core.archetypes import BaseCharacterArchetype
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.relationship import Relationships
from neighborly.plugins.defaults import DefaultNameDataPlugin
from neighborly.simulation import SimulationBuilder
from samples.inheritance_system import FurColor


class EcsFindClause(Protocol):
    def __call__(self, world: World) -> Set[int]:
        raise NotImplementedError


def friendship_gt(threshold: float, other: int) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World) -> Set[int]:
        return set(
            map(
                lambda result: result[0],
                filter(
                    lambda res: float(res[1].get_relationship(other).friendship)
                    > threshold,
                    world.get_component(Relationships),
                ),
            )
        )

    return precondition


def friendship_lt(threshold: float, other: int) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World) -> Set[int]:
        return set(
            map(
                lambda result: result[0],
                filter(
                    lambda res: float(res[1].get_relationship(other).friendship)
                    < threshold,
                    world.get_component(Relationships),
                ),
            )
        )

    return precondition


def has_component(component_type: Type[Component]) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World) -> Set[int]:
        return set(map(lambda result: result[0], world.get_component(component_type)))

    return precondition


def has_fur_color(fur_color: str) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given fur color"""

    def precondition(world: World) -> Set[int]:
        return set(
            map(
                lambda result: result[0],
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


class ClauseType(IntEnum):
    Conjunction = auto()
    Negation = auto()
    Disjunction = auto()


class Query:

    __slots__ = "_clauses"

    def __init__(self) -> None:
        self._clauses: List[Tuple[ClauseType, List[EcsFindClause]]] = []

    def where(self, func: EcsFindClause) -> Query:
        """
        Find entities for which a condition hold true
        """
        self._clauses.append((ClauseType.Conjunction, [func]))
        return self

    def where_not(self, func: EcsFindClause) -> Query:
        """
        Remove entities from consideration that satisfy a given clause
        """
        self._clauses.append((ClauseType.Negation, [func]))
        return self

    def where_either(self, *func: EcsFindClause) -> Query:
        """Find entities that match any of the conditions passed"""
        self._clauses.append((ClauseType.Disjunction, list(func)))
        return self

    def test(self, world: World, gid: int) -> bool:
        return gid in self.execute(world, start_set={gid})

    def execute(self, world: World, start_set: Optional[Set[int]] = None) -> Set[int]:
        """Execute the query on the given world instance and return the results"""
        results: Set[int] = start_set if start_set is not None else set()

        for i, (clause_type, clauses) in enumerate(self._clauses):
            if clause_type == ClauseType.Conjunction:
                if start_set is None and i == 0:
                    results = results.union(clauses[0](world))
                else:
                    results = results.intersection(clauses[0](world))
            elif clause_type == ClauseType.Negation:
                results = results - clauses[0](world)
            elif clause_type == ClauseType.Disjunction:
                # Union the sets from the clauses and perform a conjunction with existing
                # results
                clause_results: Set[int] = set()

                for clause in clauses:
                    clause_results = clause_results.union(clause(world))

                results = results.intersection(clause_results)
            else:
                raise RuntimeError(f"Unrecognized clause type: {clause_type}")

        return results


def bind_role(world, query: Query) -> Optional[GameObject]:
    """Searches the ECS for a game object that meets the given conditions"""

    result_set = query.execute(world)

    if len(result_set):
        return world.get_gameobject(
            world.get_resource(NeighborlyEngine).rng.choice(list(result_set))
        )

    return None


def main():
    sim = SimulationBuilder(seed=1010).add_plugin(DefaultNameDataPlugin()).build()

    for _ in range(30):
        FuzzCharacterArchetype().create(sim.world)

    result = bind_role(sim.world, Query().where(has_fur_color("Blue")))

    if result:
        result.pprint()

    query = (
        Query()
        .where(has_component(GameCharacter))
        .where_not(has_component(HasHorns))
        .where_either(has_fur_color("Red"), has_fur_color("Orange"))
    )

    results = query.execute(sim.world)

    print(f"\n=== New query lib results ===\n{results}")

    for gid in results:
        gameobject = sim.world.get_gameobject(gid)
        assert not gameobject.has_component(HasHorns)
        fur_color = gameobject.get_component(FurColor)
        assert "Red" in fur_color.values or "Orange" in fur_color.values

    print(query.test(sim.world, 1))

    sim.world.get_gameobject(1).get_component(Relationships).get_relationship(
        2
    ).friendship.increase(1)
    sim.world.get_gameobject(3).get_component(Relationships).get_relationship(
        5
    ).friendship.decrease(1)

    print(Query().where(friendship_gt(0.6, 2)).execute(sim.world))


if __name__ == "__main__":
    main()
