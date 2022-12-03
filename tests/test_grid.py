import pytest

from neighborly.core.utils.grid import Grid


@pytest.fixture
def int_grid() -> Grid[int]:
    grid: Grid[int] = Grid((3, 3), lambda: -1)
    grid[1, 1] = -99
    return grid


def test_get_item(int_grid: Grid[int]):
    assert int_grid[1, 1] == -99
    assert int_grid[0, 0] == -1


def test_get_item_raises_index_error(int_grid: Grid[int]):
    with pytest.raises(IndexError):
        assert int_grid[-1, 0]


def test_set_item(int_grid: Grid[int]):
    int_grid[2, 2] = 56
    assert int_grid[2, 2] == 56


def test_set_item_raises_index_error(int_grid: Grid[int]):
    with pytest.raises(IndexError):
        assert int_grid[-1, 0] == 88
