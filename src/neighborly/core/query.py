from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, Type

import pandas as pd
from ordered_set import OrderedSet

from neighborly.core.ecs import Component, GameObject, World


class EcsFindClause(Protocol):
    def __call__(self, world: World) -> List[Tuple[Any, ...]]:
        raise NotImplementedError


def has_components(*component_type: Type[Component]) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        return list(
            map(lambda result: (result[0],), world.get_components(*component_type))
        )

    return precondition


def component_attr(component_type: Type[Component], attr: str) -> EcsFindClause:
    """Returns a list of all the GameObjects with the given component"""

    def precondition(world: World):
        return list(
            map(
                lambda result: (int(result[0]), getattr(result[1], attr)),
                world.get_component(component_type),
            )
        )

    return precondition


def component_method(
    component_type: Type[Component], method: str, *args, **kwargs
) -> EcsFindClause:
    def precondition(world: World):
        return list(
            map(
                lambda result: (
                    int(result[0]),
                    getattr(result[1], method)(*args, **kwargs),
                ),
                world.get_component(component_type),
            )
        )

    return precondition


class Relation:
    """
    Relation is a collection of values associated with variables
    from a query.
    """

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
        """
        Creates a new Relation with symbols bound to starting values

        Parameters
        ----------
        **bindings: Dict[str, Optional[int]]
            Query variables mapped to GameObject IDs

        Returns
        -------
        Relation
        """
        df = pd.DataFrame(
            {k: [v] if v is not None else [] for k, v in bindings.items()}
        )
        return Relation(df)

    def get_symbols(self) -> Tuple[str]:
        """Get the symbols contained in this relation"""
        return tuple(self._data_frame.columns.tolist())

    @property
    def empty(self) -> bool:
        """Returns True is the Relation has no data"""
        return self._data_frame.empty

    def get_tuples(self, *symbols: str) -> List[Tuple[int, ...]]:
        """
        Get tuples of results mapped to the given symbols

        Returns
        -------
        List[Tuple[int, ...]]
            Results contained in this relation of values mapped to the given symbols
        """
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
        """Returns a Pandas DataFrame object representing the relation"""
        return self._data_frame

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

        if self.empty or other.empty:
            return Relation.create_empty()

        shared_symbols = set(self.get_symbols()).intersection(set(other.get_symbols()))

        if shared_symbols:
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
        return self.empty

    def __str__(self) -> str:
        return str(self._data_frame)

    def __repr__(self) -> str:
        return self._data_frame.__repr__()


class IQueryClause(Protocol):
    """A callable sued in a Query"""

    def __call__(self, ctx: QueryContext, world: World) -> Relation:
        raise NotImplementedError


@dataclass
class QueryContext:
    relation: Optional[Relation] = None


def le_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("not_equal clause is missing relation within context")

        if ctx.relation.empty:
            return ctx.relation.copy()

        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] <= df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def lt_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("not_equal clause is missing relation within context")

        if ctx.relation.empty:
            return ctx.relation.copy()

        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] < df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def ge_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("not_equal clause is missing relation within context")

        if ctx.relation.empty:
            return ctx.relation.copy()

        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] >= df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def gt_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("not_equal clause is missing relation within context")

        if ctx.relation.empty:
            return ctx.relation.copy()

        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] > df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def ne_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("not_equal clause is missing relation within context")

        if ctx.relation.empty:
            return ctx.relation.copy()

        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] != df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def eq_(symbols: Tuple[str, str]):
    """Query function that removes all instances where two variables are not the same"""

    def run(ctx: QueryContext, world: World) -> Relation:
        if ctx.relation is None:
            raise RuntimeError("equal clause is missing relation within context")
        df = ctx.relation.get_data_frame()
        new_data = df[df[symbols[0]] == df[symbols[1]]]
        return Relation(pd.DataFrame(new_data))

    return run


def where(fn: EcsFindClause, *symbols: str):
    """Finds entities that match its given clause"""

    def run(ctx: QueryContext, world: World) -> Relation:
        results = fn(world)
        values_per_symbol = list(zip(*results))

        if values_per_symbol:
            data = {s: values_per_symbol[i] for i, s in enumerate(symbols)}

            if ctx.relation is None:
                return Relation(pd.DataFrame(data))

            return ctx.relation.unify(Relation(pd.DataFrame(data)))

        return Relation.create_empty()

    return run


def where_not(fn: EcsFindClause, *symbols: str):
    """Performs a NOT operation removing entities that match its clause"""

    def run(ctx: QueryContext, world: World) -> Relation:
        results = fn(world)
        values_per_symbol = list(zip(*results))
        if values_per_symbol:
            data = pd.DataFrame(
                {s: values_per_symbol[i] for i, s in enumerate(symbols)}
            )

            if ctx.relation is None:
                raise RuntimeError(
                    "where_not clause is missing relation within context"
                )

            new_data = ctx.relation.get_data_frame().merge(
                data, how="outer", indicator=True
            )
            new_data = new_data.loc[new_data["_merge"] == "left_only"]
            new_data = new_data.drop(columns=["_merge"])
            new_relation = Relation(new_data)
            return new_relation
        else:
            if ctx.relation is None:
                return Relation.create_empty()

            return ctx.relation.copy()

    return run


def where_any(*clauses: IQueryClause):
    """Performs an OR operation matching variables to any of the given clauses"""

    def run(ctx: QueryContext, world: World) -> Relation:
        relations: List[Relation] = []

        # Run evaluate each clause, union the result
        for clause in clauses:
            relation = clause(ctx, world)
            relations.append(relation)

        new_relation = Relation(
            pd.concat(
                [*[r.get_data_frame() for r in relations]],
                ignore_index=True,
            ).drop_duplicates()
        )

        if ctx.relation is None:
            return new_relation
        else:
            return ctx.relation.unify(new_relation)

    return run


def to_clause(
    precondition: Callable[[World, GameObject], bool], *component_types: Type[Component]
) -> EcsFindClause:
    """Wraps a precondition function and returns an ECSFindClause"""

    def fn(world: World):
        results: List[Tuple[int, ...]] = []
        for gid, _ in world.get_components(*component_types):
            gameobject = world.get_gameobject(gid)
            if precondition(world, gameobject) is True:
                results.append((gid,))
        return results

    return fn


class Query:
    """
    Queries allow users to find one or more entities that match given specifications.
    """

    __slots__ = "_clauses", "_symbols"

    def __init__(self, find: Tuple[str, ...], clauses: List[IQueryClause]) -> None:
        """
        _summary_

        Parameters
        ----------
        find : Tuple[str, ...]
            Logical variable names used within the query and returned when executed
        clauses : List[IQueryClause]
            List of clauses executed to find entities
        """
        self._clauses: List[IQueryClause] = clauses
        self._symbols: Tuple[str, ...] = find

    def get_symbols(self) -> Tuple[str, ...]:
        """Get the output symbols for this pattern"""
        return self._symbols

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
        # Construct a starting relation with the variables mapped to values
        ctx = QueryContext()

        if len(bindings):
            ctx.relation = Relation.from_bindings(**bindings)

        for clause in self._clauses:
            current_relation = clause(ctx, world)
            ctx.relation = current_relation

            if ctx.relation.empty:
                # Return an empty list because the last clause failed to
                # find proper results
                return []

        # Return tuples for only the symbols specified in the constructor
        return ctx.relation.get_tuples(*self._symbols)
