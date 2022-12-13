from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    DefaultDict,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    Union,
    overload,
)

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


class SymbolsNotInRelation(Exception):
    """Exception raised when attempting to retrieve values for symbols not in a relation"""

    def __init__(self, *args: str) -> None:
        super(Exception, self).__init__(*args)
        self.symbols: Tuple[str] = args

    def __str__(self) -> str:
        return f"SymbolsNotInRelation: {self.symbols}"


class Relation:
    """
    Relation is a collection of values associated with variables
    from a query.
    """

    def __init__(
        self, symbols: Tuple[str, ...], bindings: List[Tuple[int, ...]]
    ) -> None:
        self._symbols: Tuple[str, ...] = symbols
        self._symbol_map: Dict[str, int] = {s: i for i, s in enumerate(symbols)}
        self._bindings: List[Tuple[int, ...]] = bindings

    def get_symbols(self) -> Tuple[str]:
        return self._symbols

    def get_bindings(self) -> List[Tuple[int, ...]]:
        return self._bindings

    @overload
    def get_as_dict(self, idx: int, *symbols: str) -> Dict[str, int]:
        ...

    @overload
    def get_as_dict(self, idx: slice, *symbols: str) -> List[Dict[str, int]]:
        ...

    def get_as_dict(
        self, idx: Union[int, slice], *symbols: str
    ) -> Union[Dict[str, int], List[Dict[str, int]]]:
        return_symbols = symbols if symbols else self._symbols

        if isinstance(idx, int):
            binding = dict(zip(self._symbols, self._bindings[idx]))

            return {k: binding[k] for k in return_symbols}

        results: List[Dict[str, int]] = []
        for entry in self._bindings[idx]:
            binding = dict(zip(self._symbols, entry))
            results.append({k: binding[k] for k in return_symbols})
        return results

    @overload
    def get_as_tuple(self, idx: int, *symbols: str) -> Tuple[int, ...]:
        ...

    @overload
    def get_as_tuple(self, idx: slice, *symbols: str) -> List[Tuple[int, ...]]:
        ...

    def get_as_tuple(
        self, idx: Union[int, slice], *symbols: str
    ) -> Union[Tuple[int, ...], List[Tuple[int, ...]]]:
        return_symbols = symbols if symbols else self._symbols

        symbols_not_in_relation = [s for s in return_symbols if s not in self._symbols]
        if symbols_not_in_relation:
            raise SymbolsNotInRelation(*symbols_not_in_relation)

        if isinstance(idx, int):
            binding = dict(zip(self._symbols, self._bindings[idx]))

            return tuple([binding[k] for k in return_symbols])

        results: List[Tuple[int, ...]] = []
        for entry in self._bindings[idx]:
            binding = dict(zip(self._symbols, entry))
            results.append(tuple([binding[k] for k in return_symbols]))
        return results

    def get_tuples(self, *symbols: str) -> List[Tuple[int, ...]]:
        """Return tuples containing the values from this relation"""
        if symbols:
            results_per_symbol: List[List[int]] = []
            for s in symbols:
                binding_index = self._symbol_map[s]

                results: List[int] = []
                for entry in self._bindings:
                    results.append(entry[binding_index])

                results_per_symbol.append(results)

            return list(zip(*results_per_symbol))

        return self._bindings

    def is_empty(self) -> bool:
        """Return True if the relation has no bindings"""
        return len(self._bindings) == 0

    @classmethod
    def create_empty(cls, *symbols: str) -> Relation:
        """Create an empty relation with no symbols or bindings"""
        return cls(symbols, [])

    @classmethod
    def from_bindings(cls, **bindings: int) -> Relation:
        return Relation(tuple(bindings.keys()), [tuple(bindings.values())])

    def hash_join(self, other: Relation, *symbols: str) -> Relation:
        """Perform a join between the relations using the given symbols for equivalency"""
        h: DefaultDict[Tuple[int, ...], List[int]] = defaultdict(list)

        for i, s in enumerate(other.get_tuples(*symbols)):
            h[s].append(i)

        results: List[Tuple[int, ...]] = []

        symbols_to_concat = tuple(
            set(other.get_symbols()).difference(set(self.get_symbols()))
        )

        for i, s in enumerate(self.get_tuples(*symbols)):
            binding = self.get_bindings()[i]
            matches = h.get(s)
            if matches is not None:  # join
                for match in matches:
                    if symbols_to_concat:
                        results.append(
                            binding + other.get_as_tuple(match, *symbols_to_concat)
                        )
                    else:
                        results.append(binding)

        new_symbols = self.get_symbols() + symbols_to_concat

        return Relation(new_symbols, results)

    def cross_merge(self, other: Relation) -> Relation:
        """Perform a cross merge between the relations using the given symbols for equivalency"""
        all_symbols = self._symbols + other._symbols
        new_bindings = [
            x + y for x, y in itertools.product(self._bindings, other._bindings)
        ]
        return Relation(all_symbols, new_bindings)

    def unify(self, other: Relation) -> Relation:
        """Unify variables between this Relation and another"""
        if self.is_empty() or other.is_empty():
            return Relation.create_empty()

        shared_symbols = set(self.get_symbols()).intersection(set(other.get_symbols()))

        if shared_symbols:
            # Merge on shared symbols
            return self.hash_join(other, *shared_symbols)
        else:
            # Perform a cross product
            return self.cross_merge(other)

    def copy(self) -> Relation:
        return Relation(tuple(self._symbols), [*self._bindings])

    def __repr__(self) -> str:
        return "{}(symbols={}, bindings={})".format(
            self.__class__.__name__, self._symbols, self._bindings
        )


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

            chosen_variable = (
                variable if variable is not None else ctx.output_symbols[0]
            )

            if results:
                if ctx.relation is None:
                    return Relation((chosen_variable,), results)

                return ctx.relation.unify(Relation((chosen_variable,), results))

            return Relation.create_empty()

        self._clauses.append(clause)

        return self

    # def without_(
    #     self,
    #     component_types: Tuple[Type[Component], ...],
    #     variable: Optional[str] = None,
    # ) -> QueryBuilder:
    #     """Adds results to the current query for game objects without the given components"""

    #     def clause(ctx: QueryContext, world: World) -> Relation:
    #         results = list(
    #             map(lambda result: (result[0],), world.get_components(*component_types))
    #         )

    #         chosen_variable = (
    #             variable if variable is not None else ctx.output_symbols[0]
    #         )

    #         if results:
    #             if ctx.relation is None:
    #                 raise RuntimeError(
    #                     "where_not clause is missing relation within context"
    #                 )

    #             new_data = ctx.relation.get_data_frame().merge(  # type: ignore
    #                 data, how="outer", indicator=True
    #             )

    #             new_data = new_data.loc[new_data["_merge"] == "left_only"]

    #             new_relation = Relation(new_data)

    #             return new_relation
    #         else:
    #             if ctx.relation is None:
    #                 return Relation.create_empty()

    #             return ctx.relation.copy()

    #     self._clauses.append(clause)

    #     return self

    def from_(self, fn: QueryFromFn, *symbols: str) -> QueryBuilder:
        def clause(ctx: QueryContext, world: World) -> Relation:
            results = fn(world)

            if results:

                if ctx.relation is None:
                    return Relation(symbols, results)

                return ctx.relation.unify(Relation(symbols, results))

            return Relation.create_empty()

        self._clauses.append(clause)

        return self

    def filter_(self, filter_fn: QueryFilterFn, *variables: str) -> QueryBuilder:
        """Adds results to the current query for game objects with all the given components"""

        def clause(ctx: QueryContext, world: World) -> Relation:

            if ctx.relation is None:
                raise RuntimeError("Cannot filter a query with no prior clauses")

            relation_symbols = ctx.relation.get_symbols()
            variables_to_check = variables

            # Just assume we are filtering on the only symbol bound
            # in the relation if no variable names were given
            if len(relation_symbols) == 1 and len(variables_to_check) == 0:
                variables_to_check = relation_symbols

            # Only keep rows that pass the filter
            valid_bindings = [
                row
                for i, row in enumerate(ctx.relation.get_bindings())
                if filter_fn(
                    world,
                    *[
                        world.get_gameobject(gid)
                        for gid in ctx.relation.get_as_tuple(i, *variables_to_check)
                    ],
                )
            ]

            return Relation(relation_symbols, valid_bindings)

        self._clauses.append(clause)
        return self

    def get_(self, fn: QueryGetFn, *variables: str) -> QueryBuilder:
        def clause(ctx: QueryContext, world: World) -> Relation:
            results = fn(ctx, world, *variables)

            if results:

                if ctx.relation is None:
                    return Relation(variables, results)

                return ctx.relation.unify(Relation(variables, results))

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

            if ctx.relation.is_empty():
                # Return an empty list because the last clause failed to
                # find proper results
                return []

        # Return tuples for only the symbols specified in the constructor
        if ctx.relation is not None:
            return ctx.relation.get_tuples(*self._symbols)

        return []
