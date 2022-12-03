from neighborly.core.utils.utilities import merge, parse_number_range


def test_merge():
    d0 = {
        "produce": {
            "apples": 3,
            "oranges": 4,
            "bananas": 1,
        },
        "waffles": 5,
        "toiletries": {"soap": 2, "tissues": 4, "toothpaste": 1},
    }

    d1 = {"produce": {"apples": 6}, "waffles": 0}

    assert 0 == merge(d1, d0)["waffles"]
    assert 1 == merge(d1, d0)["produce"]["bananas"]
    assert 6 == merge(d1, d0)["produce"]["apples"]
    assert 1 == d0["produce"]["bananas"]  # type: ignore


def test_parse_number_range():
    assert (0, 3) == parse_number_range("0-3")
    assert (6, 45) == parse_number_range("6-45")
    assert (5, 30) == parse_number_range("5-30")
