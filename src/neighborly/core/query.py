from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Tuple, Type

import pandas as pd
from ordered_set import OrderedSet  # type: ignore

from neighborly.core.ecs import Component, GameObject, World


class QueryFilterFn(Protocol):
    """
    Function that attempts to reduce the number of results within a query
    by defining a precondition that must be true for a result to be valid
    """

    def __call__(self, world: World, *gameobjects: GameObject) -> bool:
        """
        Check the precondition for the given result

        Parameters
        ----------
        world: World
            The current world instance

        *gameobjects: Tuple[GameObject, ...]
            GameObject references from the current relation

        Returns
        -------
        bool
            True if the precondition passes, False otherwise
        """
        raise NotImplementedError


def and_(
    *preconditions: QueryFilterFn,
) -> QueryFilterFn:
    """Join multiple occupation precondition functions into a single function"""

    def wrapper(world: World, *gameobjects: GameObject) -> bool:
        return all([p(world, *gameobjects) for p in preconditions])

    return wrapper


def or_(
    *preconditions: QueryFilterFn,
) -> QueryFilterFn:
    """Only one of the given preconditions has to pass to return True"""

    def wrapper(world: World, *gameobjects: GameObject) -> bool:
        for p in preconditions:
            if p(world, *gameobjects):
                return True
        return False

    return wrapper


def not_(
    precondition: QueryFilterFn,
) -> QueryFilterFn:
    """Only one of the given preconditions has to pass to return True"""

    def wrapper(world: World, *gameobjects: GameObject) -> bool:
        return not precondition(world, *gameobjects)

    return wrapper


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


def get_with_components(
    component_types: Tuple[Type[Component], ...], variable: Optional[str] = None
) -> IQueryClause:
    def clause(ctx: QueryContext, world: World) -> Relation:
        results = list(
            map(lambda result: (result[0],), world.get_components(*component_types))
        )

        values_per_symbol = list(zip(*results))

        chosen_variable = variable if variable is not None else ctx.output_symbols[0]

        if values_per_symbol:
            data = {s: values_per_symbol[i] for i, s in enumerate([chosen_variable])}

            if ctx.relation is None:
                return Relation(pd.DataFrame(data))

            return ctx.relation.unify(Relation(pd.DataFrame(data)))

        return Relation.create_empty()

    return clause


def get_without_components(
    component_types: Tuple[Type[Component], ...], variable: Optional[str] = None
) -> IQueryClause:
    def clause(ctx: QueryContext, world: World) -> Relation:
        results = list(
            map(lambda result: (result[0],), world.get_components(*component_types))
        )

        values_per_symbol = list(zip(*results))

        chosen_variable = variable if variable is not None else ctx.output_symbols[0]

        if values_per_symbol:
            data = pd.DataFrame(
                {s: values_per_symbol[i] for i, s in enumerate([chosen_variable])}
            )

            if ctx.relation is None:
                raise RuntimeError(
                    "where_not clause is missing relation within context"
                )

            new_data: pd.DataFrame = ctx.relation.get_data_frame().merge(  # type: ignore
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

    return clause


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
            # new_data.drop_duplicates()
            return Relation(new_data)

        else:
            new_data = self._data_frame.merge(other._data_frame, how="cross")
            # new_data.drop_duplicates()
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
    output_symbols: Tuple[str, ...] = ()


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
            )
            # ).drop_duplicates()
        )

        if ctx.relation is None:
            return new_relation
        else:
            return ctx.relation.unify(new_relation)

    return run


def filter_(precondition: QueryFilterFn, *variables: str) -> IQueryClause:
    """Wraps a precondition function and returns an ECSFindClause"""

    def run(ctx: QueryContext, world: World) -> Relation:

        rows_to_drop: List[int] = []
        relation_symbols = ctx.relation.get_symbols()
        variables_to_check = variables

        # Just assume we are filtering on the only symbol bound
        # in the relation if no variable names were given
        if len(relation_symbols) == 1 and len(variables_to_check) == 0:
            variables_to_check = relation_symbols

        for row in range(ctx.relation.get_data_frame().shape[0]):
            # convert given variables to GameObject tuple
            gameobjects: Tuple[GameObject, ...] = tuple(
                map(
                    lambda v: world.get_gameobject(
                        ctx.relation.get_data_frame().iloc[row][v]
                    ),
                    variables_to_check,
                )
            )

            if not precondition(world, *gameobjects):
                rows_to_drop.append(row)

        new_relation = Relation(ctx.relation.get_data_frame().drop(rows_to_drop))

        return new_relation

    return run


class QueryBuilder:
    @staticmethod
    def with_(
        variable: Optional[str] = None,
        *component_types: Type[Component],
    ) -> IQueryClause:
        """Adds results to the current query for game objects with all the given components"""

        def clause(ctx: QueryContext, world: World) -> Relation:
            results = list(
                map(lambda result: (result[0],), world.get_components(*component_types))
            )

            values_per_symbol = list(zip(*results))

            chosen_variable = (
                variable if variable is not None else ctx.output_symbols[0]
            )

            if values_per_symbol:
                data = {
                    s: values_per_symbol[i] for i, s in enumerate([chosen_variable])
                }

                if ctx.relation is None:
                    return Relation(pd.DataFrame(data))

                return ctx.relation.unify(Relation(pd.DataFrame(data)))

            return Relation.create_empty()

        return clause

    @staticmethod
    def without_(
        variable: Optional[str] = None,
        *component_types: Type[Component],
    ) -> IQueryClause:
        """Adds results to the current query for game objects without the given components"""

        def run(ctx: QueryContext, world: World) -> Relation:
            results = list(
                map(lambda result: (result[0],), world.get_components(*component_types))
            )

            values_per_symbol = list(zip(*results))

            chosen_variable = (
                variable if variable is not None else ctx.output_symbols[0]
            )

            if values_per_symbol:
                data = pd.DataFrame(
                    {s: values_per_symbol[i] for i, s in enumerate([chosen_variable])}
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

    @staticmethod
    def filter_(filter_fn: QueryFilterFn, *variables: str) -> IQueryClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    def not_(*clauses: IQueryClause) -> IQueryClause:
        """Adds results to the current query for game objects without all the given components"""
        ...

    @staticmethod
    def and_(*clauses: IQueryClause) -> IQueryClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    def or_(*clauses: IQueryClause) -> IQueryClause:
        """Adds results to the current query for game objects with all the given components"""
        ...


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

    def get(self, fn: EcsFindClause, *variables: str) -> Query:
        """Finds entities that match its given clause"""

        def clause(ctx: QueryContext, world: World) -> Relation:
            results = fn(world)
            values_per_symbol = list(zip(*results))

            relation_symbols = ctx.relation.get_symbols()
            variables_to_check = variables

            # Just assume we are filtering on the only symbol bound
            # in the relation if no variable names were given
            if len(relation_symbols) == 1 and len(variables_to_check) == 0:
                variables_to_check = relation_symbols

            if values_per_symbol:
                data = {
                    s: values_per_symbol[i] for i, s in enumerate(variables_to_check)
                }

                if ctx.relation is None:
                    return Relation(pd.DataFrame(data))

                return ctx.relation.unify(Relation(pd.DataFrame(data)))

            return Relation.create_empty()

        self._clauses.append(clause)
        return self

    def filter(self, precondition: QueryFilterFn, *variables: str) -> Query:
        """Wraps a precondition function and returns an ECSFindClause"""

        def clause(ctx: QueryContext, world: World) -> Relation:

            rows_to_drop: List[int] = []
            relation_symbols = ctx.relation.get_symbols()
            variables_to_check = variables

            # Just assume we are filtering on the only symbol bound
            # in the relation if no variable names were given
            if len(relation_symbols) == 1 and len(variables_to_check) == 0:
                variables_to_check = relation_symbols

            for row in range(ctx.relation.get_data_frame().shape[0]):
                # convert given variables to GameObject tuple
                gameobjects: Tuple[GameObject, ...] = tuple(
                    map(
                        lambda v: world.get_gameobject(
                            ctx.relation.get_data_frame().iloc[row][v]
                        ),
                        variables_to_check,
                    )
                )

                if not precondition(world, *gameobjects):
                    rows_to_drop.append(row)

            new_relation = Relation(ctx.relation.get_data_frame().drop(rows_to_drop))

            return new_relation

        self._clauses.append(clause)
        return self

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
        if ctx.relation is not None:
            return ctx.relation.get_tuples(*self._symbols)
        
        return []
