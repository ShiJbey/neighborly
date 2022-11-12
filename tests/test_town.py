import pytest

from neighborly.core.town import LandGrid, Town


def test_town_increment_population():
    town = Town("Test Town")
    town.increment_population()
    town.increment_population()
    assert town.population == 2


def test_town_decrement_population():
    town = Town("Test Town", 2)
    town.decrement_population()
    assert town.population == 1


def test_town_to_dict():
    town = Town("Test Town", 3)
    town_dict = town.to_dict()
    assert town_dict["name"] == "Test Town"
    assert town_dict["population"] == 3


def test_land_grid_shape():
    grid = LandGrid((5, 4))
    assert grid.shape == (5, 4)

    with pytest.raises(AssertionError):
        LandGrid((-1, 8))


def test_land_grid_in_bounds():
    grid = LandGrid((5, 4))
    assert grid.in_bounds((1, 3)) is True
    assert grid.in_bounds((0, 5)) is False
    assert grid.in_bounds((5, 4)) is False
    assert grid.in_bounds((-1, -1)) is False


def test_land_grid_get_neighbors():
    grid = LandGrid((5, 4))

    # Without diagonals
    assert grid.get_neighbors((0, 0)) == [(1, 0), (0, 1)]
    assert grid.get_neighbors((4, 0)) == [(4, 1), (3, 0)]
    assert grid.get_neighbors((4, 3)) == [(4, 2), (3, 3)]
    assert grid.get_neighbors((0, 3)) == [(0, 2), (1, 3)]

    # With diagonals
    assert grid.get_neighbors((0, 0), True) == [(1, 0), (1, 1), (0, 1)]
    assert grid.get_neighbors((4, 0), True) == [(4, 1), (3, 1), (3, 0)]
    assert grid.get_neighbors((4, 3), True) == [(3, 2), (4, 2), (3, 3)]
    assert grid.get_neighbors((0, 3), True) == [(0, 2), (1, 2), (1, 3)]


def test_land_grid_get_vacancies():
    land_grid = LandGrid((5, 3))
    assert len(land_grid.get_vacancies()) == 15

    land_grid = LandGrid((1, 1))
    assert land_grid.get_vacancies() == [(0, 0)]


def test_land_grid_has_vacancy():
    land_grid = LandGrid((5, 3))
    assert land_grid.has_vacancy()


def test_land_grid_len():
    land_grid = LandGrid((5, 3))
    assert len(land_grid) == 15

    land_grid = LandGrid((1, 1))
    assert len(land_grid) == 1


def test_land_grid_get_set_item():
    land_grid = LandGrid((5, 3))

    assert land_grid.has_vacancy()

    assert len(land_grid.get_vacancies()) == 15

    land_grid[2, 2] = 8080

    assert len(land_grid.get_vacancies()) == 14

    for pos in sorted(list(land_grid.get_vacancies())):
        land_grid[pos] = 8080

    assert land_grid.has_vacancy() is False

    assert len(land_grid.get_vacancies()) == 0

    land_grid[2, 2] = None

    assert land_grid.has_vacancy() is True

    assert len(land_grid.get_vacancies()) == 1


def test_land_grid_setitem_raises_runtime_error():
    land_grid = LandGrid((5, 3))
    land_grid[2, 2] = 8080
    with pytest.raises(RuntimeError):
        land_grid[2, 2] = 700
