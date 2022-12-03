"""
Test the class methods for the DirectedGraph and UndirectedGraph
classes located in the neighborly.core.utils package.
"""
import pytest

from neighborly.core.utils.graph import DirectedGraph, UndirectedGraph


@pytest.fixture()
def sample_directed() -> DirectedGraph[str]:
    graph = DirectedGraph[str]()
    graph.add_connection(1, 2, "friends")
    graph.add_connection(2, 1, "enemies")
    graph.add_connection(2, 3, "married")
    graph.add_connection(3, 2, "married")
    graph.add_connection(3, 1, "crush")
    return graph


@pytest.fixture()
def sample_undirected() -> UndirectedGraph[str]:
    graph = UndirectedGraph[str]()
    graph.add_connection(1, 2, "friends")
    graph.add_connection(2, 3, "married")
    graph.add_connection(3, 1, "crush")
    return graph


def test_directed_has_connection(sample_directed: DirectedGraph[str]):
    assert sample_directed.has_connection(1, 2)
    assert sample_directed.has_connection(2, 1)
    assert sample_directed.has_connection(1, 3) is False


def test_directed_get_connection(sample_directed: DirectedGraph[str]):
    assert sample_directed.get_connection(1, 2) == "friends"
    assert sample_directed.get_connection(2, 1) == "enemies"
    assert sample_directed.get_connection(2, 3) == "married"
    assert sample_directed.get_connection(3, 1) == "crush"


def test_directed_get_connection_exception(sample_directed: DirectedGraph[str]):
    with pytest.raises(KeyError):
        sample_directed.get_connection(1, 3)
        sample_directed.get_connection(1, 1)
        sample_directed.get_connection(3, 2)


def test_directed_remove_node(sample_directed: DirectedGraph[str]):
    sample_directed.remove_node(1)
    assert sample_directed.has_connection(1, 2) is False
    assert sample_directed.has_connection(2, 1) is False
    assert sample_directed.has_connection(3, 1) is False


def test_directed_remove_node_exception(sample_directed: DirectedGraph[str]):
    sample_directed.remove_node(3)

    with pytest.raises(KeyError):
        sample_directed.remove_node(3)
        sample_directed.remove_node(4)
        sample_directed.remove_node(5)


def test_directed_remove_connection(sample_directed: DirectedGraph[str]):
    assert sample_directed.has_connection(1, 2) is True
    sample_directed.remove_connection(1, 2)
    assert sample_directed.has_connection(1, 2) is False

    assert sample_directed.has_connection(3, 1) is True
    sample_directed.remove_connection(3, 1)
    assert sample_directed.has_connection(3, 1) is False


def test_directed_remove_connection_exception(sample_directed: DirectedGraph[str]):
    with pytest.raises(KeyError):
        sample_directed.remove_connection(1, 3)
        sample_directed.remove_connection(4, 3)


def test_undirected_has_connection(sample_undirected: UndirectedGraph[str]):
    assert sample_undirected.has_connection(2, 1) is True
    assert sample_undirected.has_connection(3, 2) is True
    assert sample_undirected.has_connection(1, 3) is True


def test_undirected_get_connection(sample_undirected: UndirectedGraph[str]):
    assert sample_undirected.get_connection(1, 2) == "friends"
    assert sample_undirected.get_connection(2, 1) == "friends"
    assert sample_undirected.get_connection(3, 2) == "married"
    assert sample_undirected.get_connection(2, 3) == "married"
    assert sample_undirected.get_connection(1, 3) == "crush"
    assert sample_undirected.get_connection(3, 1) == "crush"


def test_undirected_get_connection_exception(sample_undirected: UndirectedGraph[str]):
    with pytest.raises(KeyError):
        sample_undirected.get_connection(1, 1)
        sample_undirected.get_connection(3, 3)
        sample_undirected.get_connection(4, 3)


def test_undirected_remove_node(sample_undirected: DirectedGraph[str]):
    sample_undirected.remove_node(1)
    assert sample_undirected.has_connection(1, 2) is False
    assert sample_undirected.has_connection(2, 1) is False
    assert sample_undirected.has_connection(3, 1) is False
    assert sample_undirected.has_connection(1, 3) is False


def test_undirected_remove_node_exception(sample_undirected: UndirectedGraph[str]):
    sample_undirected.remove_node(3)

    with pytest.raises(KeyError):
        sample_undirected.remove_node(3)
        sample_undirected.remove_node(4)
        sample_undirected.remove_node(5)


def test_undirected_remove_connection(sample_undirected: UndirectedGraph[str]):
    assert sample_undirected.has_connection(1, 2) is True
    assert sample_undirected.has_connection(2, 1) is True
    sample_undirected.remove_connection(1, 2)
    assert sample_undirected.has_connection(1, 2) is False
    assert sample_undirected.has_connection(2, 1) is False


def test_undirected_remove_connection_exception(
    sample_undirected: UndirectedGraph[str],
):
    with pytest.raises(KeyError):
        sample_undirected.remove_connection(4, 3)
        sample_undirected.remove_connection(5, 6)
