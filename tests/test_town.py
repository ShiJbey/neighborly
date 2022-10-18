from neighborly.core.town import LandGrid


def test_land_grid():
    land_grid = LandGrid((5, 3))

    assert land_grid.shape == (5, 3)

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
