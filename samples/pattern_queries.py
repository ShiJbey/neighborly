from __future__ import annotations

from typing import Dict, List, Optional, Protocol, Set, Tuple, Type

import pandas as pd
from ordered_set import OrderedSet

from neighborly.builtin.helpers import IInheritable, inheritable
from neighborly.core.archetypes import BaseCharacterArchetype
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.relationship import Relationships
from neighborly.plugins.defaults import DefaultNameDataPlugin
from neighborly.simulation import SimulationBuilder


class EcsFindClause(Protocol):
    def __call__(self, world: World) -> List[Tuple[int]]:
        raise NotImplementedError


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


class Relation:

    __slots__ = "_data_frame"

    def __init__(self, data: pd.DataFrame) -> None:
        self._data_frame: pd.DataFrame = data

    @classmethod
    def create_empty(cls, *symbols: str) -> Relation:
        """
        Create an empty Relation

        Parameters
        ----------
        symbols: Tuple[str]
            Starting symbols for the Relation

        Returns
        -------
        Relation
        """
        df = pd.DataFrame({s: [] for s in OrderedSet(symbols)})
        return Relation(df)

    @classmethod
    def from_bindings(cls, **bindings: int) -> Relation:
        df = pd.DataFrame({k: [v] for k, v in bindings.items()})
        return Relation(df)

    def get_symbols(self) -> List[str]:
        """Get the symbols contained in this relation"""
        return self._data_frame.columns.tolist()

    def is_empty(self) -> bool:
        """Returns True is the Relation has no data"""
        return self._data_frame.empty

    def get_tuples(self, *symbols: str) -> List[Tuple[int, ...]]:
        if symbols:
            try:
                return list(
                    self._data_frame[list(symbols)].itertuples(index=False, name=None)
                )
            except KeyError:
                # If any symbols are missing, return an empty list
                return []
        else:
            return list(self._data_frame.itertuples(index=False, name=None))

    def get_data_frame(self) -> pd.DataFrame:
        return self._data_frame

    def _get_shared_symbols(self, other: Relation) -> Set[str]:
        """Returns true if the other Relation shares symbols with this one"""
        return set(self.get_symbols()).intersection(set(other.get_symbols()))

    def unify(self, other: Relation) -> Relation:
        """
        Joins two relations

        Parameters
        ----------
        other: Relation
            The relation to unify with

        Returns
        -------
        Relation
            A new Relation instance
        """

        if self.is_empty():
            return Relation(other._data_frame.copy())

        elif other.is_empty():
            return Relation(self._data_frame.copy())

        elif shared_symbols := self._get_shared_symbols(other):
            new_data = self._data_frame.merge(
                other._data_frame, on=list(shared_symbols)
            )
            new_data.drop_duplicates()
            return Relation(new_data)

        else:
            new_data = self._data_frame.merge(other._data_frame, how="cross")
            new_data.drop_duplicates()
            return Relation(new_data)

    def copy(self) -> Relation:
        """Create a deep copy of the relation"""
        return Relation(self._data_frame.copy())

    def __bool__(self) -> bool:
        return self.is_empty()

    def __str__(self) -> str:
        return str(self._data_frame)

    def __repr__(self) -> str:
        return self._data_frame.__repr__()


class IQueryClause(Protocol):
    def __call__(self, ctx: Relation, world: World) -> Relation:
        raise NotImplementedError


def not_equal(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: Relation, world: World) -> Relation:
        df = ctx.get_data_frame()
        new_data = df[df[symbols[0]] != df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def equal(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: Relation, world: World) -> Relation:
        df = ctx.get_data_frame()
        new_data = df[df[symbols[0]] == df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def where(fn: EcsFindClause, *symbols: str):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: Relation, world: World) -> Relation:
        results = fn(world)
        values_per_symbol = list(zip(*results))
        data = {s: values_per_symbol[i] for i, s in enumerate(symbols)}
        return ctx.unify(Relation(pd.DataFrame(data)))

    return run


def where_not(fn: EcsFindClause, *symbols: str):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: Relation, world: World) -> Relation:
        results = fn(world)
        values_per_symbol = list(zip(*results))
        data = pd.DataFrame({s: values_per_symbol[i] for i, s in enumerate(symbols)})
        new_data = ctx.get_data_frame().merge(data, how="outer", indicator=True)
        new_data = new_data.loc[new_data["_merge"] == "left_only"]
        new_data = new_data.drop(columns=["_merge"])
        new_relation = Relation(new_data)
        return new_relation

    return run


def where_either(clauses: List[Tuple[EcsFindClause, Tuple[str, ...]]]):
    def run(ctx: Relation, world: World) -> Relation:
        """Evaluates each clause, unifies it with the ctx, and unions the results"""

        relations: List[Relation] = []

        # Run evaluate each clause, union the result
        for clause in clauses:
            fn, symbols = clause

            results = fn(world)
            values_per_symbol = list(zip(*results))
            data = pd.DataFrame(
                {s: values_per_symbol[i] for i, s in enumerate(symbols)}
            )
            relation = ctx.unify(Relation(data))
            if not relation.is_empty():
                relations.append(relation)

        new_relation = Relation(
            pd.concat(
                [ctx.copy().get_data_frame(), *[r.get_data_frame() for r in relations]],
                ignore_index=True,
            )
        )

        return new_relation

    return run


class Query:

    __slots__ = "_clauses", "_symbols"

    def __init__(self, find: Tuple[str, ...], where: List[IQueryClause]) -> None:
        self._clauses: List[IQueryClause] = where
        self._symbols: Tuple[str] = find

    def execute(self, world: World, **bindings: int) -> List[Tuple[int, ...]]:
        """
        Perform a query on the world instance

        Parameters
        ----------
        world: World
            The world instance to run the query on

        bindings: Dict[str, int]
            Symbol strings mapped to GameObjectID to match to

        Returns
        -------
        List[Tuple[int, ...]]
            Tuples of GameObjectIDs that match the requirements of the query
        """
        # Ensure that the bindings exist within the existing symbols list
        for s in bindings.keys():
            if s not in self._symbols:
                raise RuntimeError(f"The symbol '{s}' was not specified in Query(...)")

        # Construct a starting relation with the variables mapped to values
        current_relation = Relation.create_empty()

        for clause in self._clauses:
            current_relation = clause(current_relation, world)

        # Return tuples for only the symbols specified in the constructor
        return current_relation.get_tuples(*self._symbols)


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
        where=[
            where(has_component(GameCharacter), "X"),
            where(has_component(HasHorns), "X"),
            where(has_component(GameCharacter), "Y"),
            where_not(has_component(HasHorns), "Y"),
            not_equal(("X", "Y")),
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
