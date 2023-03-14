import pytest

from neighborly.core.settlement import Grid, GridSettlementMap


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


def test_grid_map_shape():
    grid = GridSettlementMap((5, 4))
    assert grid.get_size() == (5, 4)

    with pytest.raises(AssertionError):
        GridSettlementMap((-1, 8))


def test_land_grid_get_neighbors():
    grid = GridSettlementMap((5, 4))

    assert grid.get_neighboring_lots(0) == [1, 6, 5]
    assert grid.get_neighboring_lots(4) == [9, 8, 3]
    assert grid.get_neighboring_lots(7) == [1, 2, 3, 8, 13, 12, 11, 6]
    assert grid.get_neighboring_lots(15) == [10, 11, 16]
    assert grid.get_neighboring_lots(19) == [13, 14, 18]


def test_land_grid_get_vacancies():
    land_grid = GridSettlementMap((5, 3))
    assert len(land_grid.get_vacant_lots()) == 15

    land_grid = GridSettlementMap((1, 1))
    assert land_grid.get_vacant_lots() == [0]


def test_land_grid_get_total_lots():
    land_grid = GridSettlementMap((5, 3))
    assert land_grid.get_total_lots() == 15

    land_grid = GridSettlementMap((1, 1))
    assert land_grid.get_total_lots() == 1


def test_land_grid_get_set_item():
    land_grid = GridSettlementMap((5, 3))

    assert len(land_grid.get_vacant_lots()) == 15

    land_grid.reserve_lot(3, 8080)

    assert len(land_grid.get_vacant_lots()) == 14

    for lot in sorted(list(land_grid.get_vacant_lots())):
        land_grid.reserve_lot(lot, 8080)
    assert len(land_grid.get_vacant_lots()) == 0

    land_grid.free_lot(2)
    assert len(land_grid.get_vacant_lots()) == 1


def test_land_grid_setitem_raises_runtime_error():
    land_grid = GridSettlementMap((5, 3))
    land_grid.reserve_lot(2, 8080)
    with pytest.raises(RuntimeError):
        land_grid.reserve_lot(2, 700)
