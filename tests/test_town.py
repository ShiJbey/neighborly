from neighborly.core.town import LandGrid


def test_town_layout():
    layout = LandGrid(5, 4)

    assert layout.grid.shape == (5, 4)
    assert layout.has_vacancy() is True
    space = layout.reserve_space(0)
    assert space == (0, 0)

    for i in range(19):
        layout.reserve_space(0)

    assert layout.has_vacancy() is False

    layout.free_space((3, 3))

    assert layout.has_vacancy() is True
