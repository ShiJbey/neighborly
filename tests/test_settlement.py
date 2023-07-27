import pytest

from neighborly.simulation import Neighborly
from neighborly.world_map import BuildingMap, Grid


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
    grid = BuildingMap((5, 4))
    assert grid.get_size() == (5, 4)

    with pytest.raises(ValueError):
        BuildingMap((-1, 8))


def test_land_grid_get_neighbors():
    grid = BuildingMap((5, 4))

    assert grid.get_neighboring_lots((0, 0)) == [(1, 0), (1, 1), (0, 1)]
    assert grid.get_neighboring_lots((0, 3)) == [(0, 2), (1, 2), (1, 3)]
    assert grid.get_neighboring_lots((4, 0)) == [(4, 1), (3, 1), (3, 0)]
    assert grid.get_neighboring_lots((4, 3)) == [(3, 2), (4, 2), (3, 3)]
    assert grid.get_neighboring_lots((2, 2)) == [
        (1, 1),
        (2, 1),
        (3, 1),
        (3, 2),
        (3, 3),
        (2, 3),
        (1, 3),
        (1, 2),
    ]


def test_land_grid_get_vacancies():
    land_grid = BuildingMap((5, 3))
    assert len(land_grid.get_vacant_lots()) == 15

    land_grid = BuildingMap((1, 1))
    assert land_grid.get_vacant_lots() == [(0, 0)]


def test_land_grid_get_total_lots():
    land_grid = BuildingMap((5, 3))
    assert land_grid.get_total_lots() == 15

    land_grid = BuildingMap((1, 1))
    assert land_grid.get_total_lots() == 1


def test_land_grid_get_set_item():
    sim = Neighborly()

    building_0 = sim.world.gameobject_manager.spawn_gameobject(name="Building 0")

    land_grid = BuildingMap((5, 3))

    assert len(land_grid.get_vacant_lots()) == 15

    land_grid.add_building((0, 2), building_0)

    assert len(land_grid.get_vacant_lots()) == 14

    for lot in sorted(list(land_grid.get_vacant_lots())):
        building = sim.world.gameobject_manager.spawn_gameobject(
            name=f"building_on_lot_{lot}"
        )
        land_grid.add_building(lot, building)

    assert len(land_grid.get_vacant_lots()) == 0

    land_grid.remove_building_from_lot((0, 2))
    assert len(land_grid.get_vacant_lots()) == 1


def test_land_grid_setitem_raises_runtime_error():
    sim = Neighborly()

    building_0 = sim.world.gameobject_manager.spawn_gameobject(name="Building 0")
    building_1 = sim.world.gameobject_manager.spawn_gameobject(name="Building 1")

    land_grid = BuildingMap((5, 3))
    land_grid.add_building((0, 2), building_0)
    with pytest.raises(RuntimeError):
        land_grid.add_building((0, 2), building_1)
