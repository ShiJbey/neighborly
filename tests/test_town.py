from neighborly.core.town import TownLayout


def test_town_layout():
    layout = TownLayout(5, 4)

    assert layout.shape == (5, 4)
    assert layout.width == 5
    assert layout.length == 4
    assert layout.has_vacancy() is True
    space = layout.allocate_space()
    assert space.space_id == 0

    for i in range(19):
        layout.allocate_space()

    assert layout.has_vacancy() is False

    layout.free_space(10)

    assert layout.has_vacancy() is True
