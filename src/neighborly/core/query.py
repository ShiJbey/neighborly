from __future__ import annotations

import itertools
from collections import defaultdict
from dataclasses import dataclass
from typing import (
    Callable,
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

from .ecs import Component, GameObject, World


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

    __slots__ = "_symbols", "_symbol_map", "_bindings", "_is_initialized"

    def __init__(
        self,
        symbols: Tuple[str, ...],
        bindings: List[Tuple[int, ...]],
        is_initialized: bool = True,
    ) -> None:
        self._symbols: Tuple[str, ...] = symbols
        self._symbol_map: Dict[str, int] = {s: i for i, s in enumerate(symbols)}
        self._bindings: List[Tuple[int, ...]] = bindings
        self._is_initialized: bool = is_initialized

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

    def is_uninitialized(self) -> bool:
        return not self._is_initialized

    def is_empty(self) -> bool:
        """Return True if the relation has no bindings"""
        return len(self._bindings) == 0

    @classmethod
    def create_empty(cls, *symbols: str) -> Relation:
        """Create an empty relation with no symbols or bindings"""
        return cls(symbols, [])

    @classmethod
    def from_bindings(cls, bindings: Dict[str, int]) -> Relation:
        return Relation(tuple(bindings.keys()), [tuple(bindings.values())])

    def hash_join(self, other: Relation, *symbols: str) -> Relation:
        """Perform an inner join between the relations using the given symbols"""
        h: DefaultDict[Tuple[int, ...], List[int]] = defaultdict(list)

        # Map tuples of the values of the given symbols in one
        # relation to a list of row indexes
        for i, s in enumerate(other.get_tuples(*symbols)):
            h[s].append(i)

        results: List[Tuple[int, ...]] = []

        # Get the symbols present in the second relation only
        symbols_to_concat = tuple(
            set(other.get_symbols()).difference(set(self.get_symbols()))
        )

        for i, s in enumerate(self.get_tuples(*symbols)):
            binding = self.get_bindings()[i]
            matches = h[s]
            if matches:  # join
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

    @staticmethod
    def left_join(a: Relation, b: Relation, *symbols: str) -> Relation:
        """Join two relations keeping rows only present in the first relation"""
        h: DefaultDict[Tuple[int, ...], List[int]] = defaultdict(list)

        symbols_to_join = tuple(
            symbols
            if symbols
            else set(a.get_symbols()).intersection(set(b.get_symbols()))
        )

        # Map tuples of the values of the given symbols in one
        # relation to a list of row indexes
        # Any rows in the first relation that match keys in this
        # dict are excluded (i.e. left-join)
        for i, s in enumerate(b.get_tuples(*symbols_to_join)):
            h[s].append(i)

        results: List[Tuple[int, ...]] = []

        for i, s in enumerate(a.get_tuples(*symbols_to_join)):
            if s not in h:
                results.append(a.get_bindings()[i])

        return Relation(a.get_symbols(), results)

    def copy(self) -> Relation:
        return Relation(tuple(self._symbols), [*self._bindings])

    def __repr__(self) -> str:
        return "{}(symbols={}, bindings={})".format(
            self.__class__.__name__, self._symbols, self._bindings
        )


class QueryClause(Protocol):
    """An interface implemented by call clauses in a query"""

    def __call__(self, ctx: QueryContext) -> Relation:
        raise NotImplementedError


class WithClause:
    __slots__ = "component_types", "variable"

    def __init__(
        self,
        component_types: Tuple[Type[Component], ...],
        variable: Optional[str] = None,
    ) -> None:
        self.component_types: Tuple[Type[Component], ...] = component_types
        self.variable: Optional[str] = variable

    def __call__(self, ctx: QueryContext) -> Relation:
        results = list(
            map(
                lambda result: (result[0],),
                ctx.world.get_components(self.component_types),
            )
        )

        chosen_variable = (
            self.variable if self.variable is not None else ctx.output_symbols[0]
        )

        if results:
            if ctx.relation.is_uninitialized():
                return Relation((chosen_variable,), results)

            return ctx.relation.unify(Relation((chosen_variable,), results))

        return Relation.create_empty()


class QueryFromFn(Protocol):
    def __call__(self, world: World) -> List[Tuple[int, ...]]:
        raise NotImplementedError


class FromClause:
    __slots__ = "fetch_fn", "variables"

    def __init__(self, fetch_fn: QueryFromFn, *variables: str) -> None:
        self.fetch_fn: QueryFromFn = fetch_fn
        self.variables: Tuple[str, ...] = variables

    def __call__(self, ctx: QueryContext) -> Relation:
        results = self.fetch_fn(ctx.world)

        if results:
            if ctx.relation.is_uninitialized():
                return Relation(self.variables, results)

            return ctx.relation.unify(Relation(self.variables, results))

        return Relation.create_empty()


class FilterClause:
    __slots__ = "filter_fn", "variables"

    def __init__(
        self,
        filter_fn: Union[
            Callable[[GameObject], bool],
            Callable[[GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject, GameObject], bool],
        ],
        variables: Union[
            str, Tuple[str, str], Tuple[str, str, str], Tuple[str, str, str, str]
        ],
    ) -> None:
        self.filter_fn: Union[
            Callable[[GameObject], bool],
            Callable[[GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject, GameObject], bool],
        ] = filter_fn
        if isinstance(variables, tuple):
            self.variables: Tuple[str, ...] = variables
        else:
            self.variables: Tuple[str, ...] = (variables,)

    def __call__(self, ctx: QueryContext) -> Relation:
        if ctx.relation.is_uninitialized():
            raise RuntimeError("Cannot filter a query with no prior clauses")

        relation_symbols = ctx.relation.get_symbols()
        variables_to_check = self.variables

        # Just assume we are filtering on the only symbol bound
        # in the relation if no variable names were given
        if len(relation_symbols) == 1 and len(variables_to_check) == 0:
            variables_to_check = relation_symbols

        # Only keep rows that pass the filter
        valid_bindings = [
            row
            for i, row in enumerate(ctx.relation.get_bindings())
            if self.filter_fn(
                *[
                    ctx.world.get_gameobject(gid)
                    for gid in ctx.relation.get_as_tuple(i, *variables_to_check)
                ],
            )
        ]

        return Relation(relation_symbols, valid_bindings)


class QueryGetFn(Protocol):
    def __call__(
        self, ctx: QueryContext, world: World, *variables: str
    ) -> List[Tuple[int, ...]]:
        raise NotImplementedError


class GetClause:
    __slots__ = "get_fn", "variables"

    def __init__(self, get_fn: QueryGetFn, *variables: str) -> None:
        self.get_fn: QueryGetFn = get_fn
        self.variables: Tuple[str, ...] = variables

    def __call__(self, ctx: QueryContext) -> Relation:
        results = self.get_fn(ctx, ctx.world, *self.variables)

        if results:
            if ctx.relation.is_uninitialized():
                return Relation(self.variables, results)

            return ctx.relation.unify(Relation(self.variables, results))

        return Relation.create_empty()


class AndClause:
    """Perform inner join on all sub-clauses"""

    __slots__ = "clauses"

    def __init__(self, *clauses: QueryClause) -> None:
        self.clauses: Tuple[QueryClause] = clauses

    def __call__(self, ctx: QueryContext) -> Relation:
        joined_relation = ctx.relation

        for clause in self.clauses:
            joined_relation = joined_relation.unify(clause(ctx))

        return joined_relation


class OrClause:
    """Perform inner join on all sub-clauses"""

    __slots__ = "clauses"

    def __init__(self, *clauses: QueryClause) -> None:
        self.clauses: Tuple[QueryClause] = clauses

    def __call__(self, ctx: QueryContext) -> Relation:
        joined_relation = ctx.relation

        for clause in self.clauses:
            joined_relation = joined_relation.unify(clause(ctx))

        return joined_relation


class NotClause:
    __slots__ = "clause"

    def __init__(self, clause: QueryClause) -> None:
        self.clause: QueryClause = clause

    def __call__(self, ctx: QueryContext) -> Relation:
        return Relation.left_join(ctx.relation, self.clause(ctx))


@dataclass
class QueryContext:
    world: World
    relation: Relation
    output_symbols: Tuple[str, ...]


class QB:
    """
    Helper class that allows users to create ECS queries one operation at a time
    """

    @staticmethod
    def query(variables: Union[str, Tuple[str, ...]], *clauses: QueryClause) -> Query:
        if isinstance(variables, str):
            query_vars = (variables,)
        else:
            query_vars = variables
        return Query(query_vars, [*clauses])

    @staticmethod
    def with_(
        component_types: Union[Type[Component], Tuple[Type[Component], ...]],
        variable: Optional[str] = None,
    ) -> WithClause:
        """Adds results to the current query for game objects with all the given components"""
        if isinstance(component_types, tuple):
            return WithClause(component_types, variable)
        else:
            return WithClause((component_types,), variable)

    @staticmethod
    def from_(fn: QueryFromFn, *variables: str) -> FromClause:
        return FromClause(fn, *variables)

    @staticmethod
    @overload
    def filter_(
        filter_fn: Callable[[GameObject], bool],
        variables: str,
    ) -> FilterClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    @overload
    def filter_(
        filter_fn: Callable[[GameObject, GameObject], bool],
        variables: Tuple[str, str],
    ) -> FilterClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    @overload
    def filter_(
        filter_fn: Callable[[GameObject, GameObject, GameObject], bool],
        variables: Tuple[str, str, str],
    ) -> FilterClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    @overload
    def filter_(
        filter_fn: Callable[[GameObject, GameObject, GameObject, GameObject], bool],
        variables: Tuple[str, str, str, str],
    ) -> FilterClause:
        """Adds results to the current query for game objects with all the given components"""
        ...

    @staticmethod
    def filter_(
        filter_fn: Union[
            Callable[[GameObject], bool],
            Callable[[GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject], bool],
            Callable[[GameObject, GameObject, GameObject, GameObject], bool],
        ],
        variables: Union[
            str, Tuple[str, str], Tuple[str, str, str], Tuple[str, str, str, str]
        ],
    ) -> FilterClause:
        """Adds results to the current query for game objects with all the given components"""
        return FilterClause(filter_fn, variables)

    @staticmethod
    def get_(fn: QueryGetFn, *variables: str) -> GetClause:
        """Get entities from the ecs and bind them to variables"""
        return GetClause(fn, *variables)

    @staticmethod
    def and_(*clauses: QueryClause) -> AndClause:
        """Get entities from the ecs and bind them to variables"""
        return AndClause(*clauses)

    @staticmethod
    def or_(*clauses: QueryClause) -> OrClause:
        """Get entities from the ecs and bind them to variables"""
        return OrClause(*clauses)

    @staticmethod
    def not_(clause: QueryClause) -> NotClause:
        """Get entities from the ecs and bind them to variables"""
        return NotClause(clause)


class Query:
    """
    Queries allow users to find one or more entities that match given specifications.
    """

    __slots__ = "_clauses", "_symbols"

    def __init__(self, find: Tuple[str, ...], clauses: List[QueryClause]) -> None:
        """
        _summary_

        Parameters
        ----------
        find : Tuple[str, ...]
            Logical variable names used within the query and returned when executed
        clauses : List[QueryClause]
            List of clauses executed to find entities
        """
        self._clauses: List[QueryClause] = clauses
        self._symbols: Tuple[str, ...] = find

    def get_symbols(self) -> Tuple[str, ...]:
        """Get the output symbols for this pattern"""
        return self._symbols

    def execute(
        self, world: World, bindings: Optional[Dict[str, int]] = None
    ) -> List[Tuple[int, ...]]:
        """
        Perform a query on the world instance

        Parameters
        ----------
        world: World
            The world instance to run the query on
        bindings: Dict[str, int], optional
            Bindings of GameObjects to variables

        Returns
        -------
        List[Tuple[int, ...]]
            Tuples of GameObjectIDs that match the requirements of the query
        """
        # Construct a starting relation with the variables mapped to values

        if bindings is not None:
            ctx = QueryContext(
                world=world,
                output_symbols=self._symbols,
                relation=Relation.from_bindings(bindings),
            )
        else:
            ctx = QueryContext(
                world=world,
                output_symbols=self._symbols,
                relation=Relation(("_",), [], is_initialized=False),
            )

        for clause in self._clauses:
            current_relation = clause(ctx)
            ctx.relation = current_relation

            if ctx.relation.is_empty():
                # Return an empty list because the last clause failed to
                # find proper results
                return []

        # Return tuples for only the symbols specified in the constructor
        if not ctx.relation.is_uninitialized():
            return ctx.relation.get_tuples(*self._symbols)

        return []
