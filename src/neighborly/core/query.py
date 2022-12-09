from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Protocol, Tuple, Type

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


class QueryFromFn(Protocol):
    def __call__(self, world: World) -> List[Tuple[int, ...]]:
        raise NotImplementedError


class QueryGetFn(Protocol):
    def __call__(
        self, ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        raise NotImplementedError


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
        return tuple(self._data_frame.columns.tolist())  # type: ignore

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
                    self._data_frame[list(symbols)].itertuples(index=False, name=None)  # type: ignore
                )
            except KeyError:
                # If any symbols are missing, return an empty list
                return []
        else:
            return list(self._data_frame.itertuples(index=False, name=None))  # type: ignore

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
            new_data = self._data_frame.merge(  # type: ignore
                other._data_frame, on=list(shared_symbols)
            )
            # new_data.drop_duplicates()
            return Relation(new_data)

        else:
            new_data = self._data_frame.merge(other._data_frame, how="cross")  # type: ignore
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


def eq_(world: World, *gameobjects: GameObject) -> bool:
    """Query function that removes all instances where two variables are not the same"""
    return gameobjects[0] == gameobjects[1]


class QueryBuilder:
    """
    Helper class that allows users to create ECS queries one operation at a time
    """

    __slots__ = "_output_vars", "_clauses"

    def __init__(self, *output_vars: str) -> None:
        self._output_vars: Tuple[str, ...] = output_vars
        self._clauses: List[IQueryClause] = []

        if len(self._output_vars) == 0:
            # Create a default symbol
            self._output_vars = ("_",)

    def build(self) -> Query:
        return Query(find=self._output_vars, clauses=self._clauses)

    def with_(
        self,
        component_types: Tuple[Type[Component], ...],
        variable: Optional[str] = None,
    ) -> QueryBuilder:
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

        self._clauses.append(clause)

        return self

    def without_(
        self,
        component_types: Tuple[Type[Component], ...],
        variable: Optional[str] = None,
    ) -> QueryBuilder:
        """Adds results to the current query for game objects without the given components"""

        def clause(ctx: QueryContext, world: World) -> Relation:
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

                new_data = ctx.relation.get_data_frame().merge(  # type: ignore
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

        self._clauses.append(clause)

        return self

    def from_(self, fn: QueryFromFn, *symbols: str) -> QueryBuilder:
        def clause(ctx: QueryContext, world: World) -> Relation:
            results = fn(world)
            values_per_symbol = list(zip(*results))

            if values_per_symbol:
                data = {s: values_per_symbol[i] for i, s in enumerate(symbols)}

                if ctx.relation is None:
                    return Relation(pd.DataFrame(data))

                return ctx.relation.unify(Relation(pd.DataFrame(data)))

            return Relation.create_empty()

        self._clauses.append(clause)

        return self

    def filter_(self, filter_fn: QueryFilterFn, *variables: str) -> QueryBuilder:
        """Adds results to the current query for game objects with all the given components"""

        def clause(ctx: QueryContext, world: World) -> Relation:

            if ctx.relation is None:
                raise RuntimeError("Cannot filter a query with no prior clauses")

            rows_to_include: List[int] = []
            relation_symbols = ctx.relation.get_symbols()
            variables_to_check = variables

            # Just assume we are filtering on the only symbol bound
            # in the relation if no variable names were given
            if len(relation_symbols) == 1 and len(variables_to_check) == 0:
                variables_to_check = relation_symbols

            for row in range(ctx.relation.get_data_frame().shape[0]):  # type: ignore
                # convert given variables to GameObject tuple
                gameobjects: Tuple[GameObject, ...] = tuple(
                    map(
                        lambda v: world.get_gameobject(
                            ctx.relation.get_data_frame().iloc[row][v]  # type: ignore
                        ),
                        variables_to_check,
                    )
                )

                if filter_fn(world, *gameobjects):
                    rows_to_include.append(row)

            new_relation = Relation(ctx.relation.get_data_frame().iloc[rows_to_include])  # type: ignore

            return new_relation

        self._clauses.append(clause)
        return self

    def get_(self, fn: QueryGetFn, *variables: str) -> QueryBuilder:
        def clause(ctx: QueryContext, world: World) -> Relation:
            results = fn(ctx, world, *variables)
            values_per_symbol = list(zip(*results))

            if values_per_symbol:
                data = {s: values_per_symbol[i] for i, s in enumerate(variables)}

                if ctx.relation is None:
                    return Relation(pd.DataFrame(data))

                return ctx.relation.unify(Relation(pd.DataFrame(data)))

            return Relation.create_empty()

        self._clauses.append(clause)

        return self


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

    def execute(self, world: World, *args: int, **kwargs: int) -> List[Tuple[int, ...]]:
        """
        Perform a query on the world instance

        Parameters
        ----------
        world: World
            The world instance to run the query on
        *args: GameObject
            Positional GameObject bindings to variables
        **kwargs: GameObject
            Keyword bindings of GameObjects to variables

        Returns
        -------
        List[Tuple[int, ...]]
            Tuples of GameObjectIDs that match the requirements of the query
        """
        # Construct a starting relation with the variables mapped to values
        ctx = QueryContext(output_symbols=self._symbols)

        if len(args) and len(kwargs):
            raise RuntimeError(
                "Cannot use positional and keyword binding at the same time"
            )

        if len(args):
            ctx.relation = Relation.from_bindings(
                **{str(s): x for s, x in list(zip(self.get_symbols(), args))}
            )

        if len(kwargs):
            ctx.relation = Relation.from_bindings(**kwargs)

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
