from collections import defaultdict
from typing import DefaultDict, Dict, Generic, NamedTuple, Tuple, TypeVar, cast

from ordered_set import OrderedSet

_T = TypeVar("_T")


class BDGraphNode(NamedTuple):
    incoming: OrderedSet[int]
    outgoing: OrderedSet[int]


class DirectedGraph(Generic[_T]):
    """Directed graph that represents information that connects characters"""

    __slots__ = "_nodes", "_edges"

    def __init__(self) -> None:
        self._nodes: DefaultDict[int, BDGraphNode] = defaultdict(
            lambda: BDGraphNode(OrderedSet([]), OrderedSet([]))
        )
        self._edges: Dict[Tuple[int, int], _T] = {}

    def add_connection(self, owner: int, target: int, data: _T) -> None:
        """Insert a new connection between characters"""
        self._nodes[owner].outgoing.add(target)
        self._nodes[target].incoming.add(owner)
        self._edges[(owner, target)] = data

    def has_connection(self, owner: int, target: int) -> bool:
        """Return true if a connection exists from the owner to the target"""
        return (owner, target) in self._edges

    def get_connection(self, owner: int, target: int) -> _T:
        """Get a connection between two characters if one exists"""
        return self._edges[(owner, target)]

    def remove_node(self, node: int) -> None:
        """Remove a node and delete incoming and outgoing connections"""
        if node not in self._nodes:
            raise KeyError

        node_to_remove = self._nodes[node]

        # Delete all the outgoing connections
        for other_node in [*node_to_remove.outgoing]:
            self.remove_connection(node, other_node)

        # Delete incoming connections
        for other_node in [*node_to_remove.incoming]:
            self.remove_connection(other_node, node)

        del self._nodes[node]

    def remove_connection(self, owner: int, target: int) -> None:
        """Remove a connection from the social graph"""
        self._nodes[owner].outgoing.remove(target)
        self._nodes[target].incoming.remove(owner)
        del self._edges[owner, target]


class UndirectedGraph(Generic[_T]):
    """Manages information about characters shared feeling towards each other

    This class is for modeling symmetric social connections
    """

    def __init__(self) -> None:
        self._nodes: Dict[int, OrderedSet[int]] = {}
        self._edges: Dict[Tuple[int, int], _T] = {}

    def add_connection(self, node_a: int, node_b: int, data: _T) -> None:
        """Insert a new connection between characters"""

        if node_a not in self._nodes:
            self._nodes[node_a] = OrderedSet([])

        if node_b not in self._nodes:
            self._nodes[node_b] = OrderedSet([])

        self._nodes[node_a].add(node_b)
        self._nodes[node_b].add(node_a)

        nodes = cast(Tuple[int, int], tuple(sorted((node_a, node_b))))
        self._edges[nodes] = data

    def has_connection(self, node_a: int, node_b: int) -> bool:
        """Return true if a connection exists from the owner to the target"""
        nodes = tuple(sorted((node_a, node_b)))
        return nodes in self._edges

    def get_connection(self, node_a: int, node_b: int) -> _T:
        """Get a connection between two characters if one exists"""
        nodes = cast(Tuple[int, int], tuple(sorted((node_a, node_b))))
        return self._edges[nodes]

    def remove_node(self, node: int) -> None:
        """Remove a node and delete incoming and outgoing connections"""
        for other_node in self._nodes[node]:
            self.remove_connection(node, other_node)

        del self._nodes[node]

    def remove_connection(self, node_a: int, node_b: int) -> None:
        """Remove a connection from the social graph"""
        nodes = cast(Tuple[int, int], tuple(sorted((node_a, node_b))))
        del self._edges[nodes]
