import copy
import datetime

import pytest

from neighborly.datetime import SimDate


def test__copy__():
    d0 = SimDate()
    d1 = copy.copy(d0)

    assert id(d0) != id(d1)
    assert d0 == d1


def test__deepcopy__():
    d0 = SimDate()
    d1 = copy.deepcopy(d0)

    assert id(d0) != id(d1)
    assert d0 == d1


def test__le__():
    assert (SimDate() <= SimDate()) is True
    assert (SimDate() <= SimDate(year=2000)) is True
    assert (SimDate(year=3000) <= SimDate()) is False


def test__lt__():
    assert (SimDate() < SimDate()) is False
    assert (SimDate() < SimDate(year=2000)) is True
    assert (SimDate(year=3000) < SimDate()) is False


def test__ge__():
    assert (SimDate() >= SimDate()) is True
    assert (SimDate() >= SimDate(year=2000)) is False
    assert (SimDate(year=3000) >= SimDate()) is True


def test__gt__():
    assert (SimDate() > SimDate()) is False
    assert (SimDate() > SimDate(year=2000)) is False
    assert (SimDate(year=3000) > SimDate()) is True


def test__eq__():
    assert (SimDate() == SimDate()) is True
    assert (SimDate() == SimDate(year=2000)) is False
    assert (SimDate(year=3000) == SimDate()) is False
    assert (SimDate(year=3000) == SimDate(year=3000)) is True
    assert SimDate(1, 4) == SimDate(1, 4)
    assert SimDate(2023, 6) == SimDate(2023, 6)


def test_to_iso_str():
    date = SimDate(2022, 6)
    assert date.to_iso_str() == "2022-06"

    date = SimDate(2022, 9)
    assert date.to_iso_str() == "2022-09"


def test_increment_month():
    date = SimDate(3, 1)

    assert date.month == 1
    assert date.year == 3
    assert date.total_months == 24

    date.increment_month()

    assert date.month == 2
    assert date.year == 3
    assert date.total_months == 25

    # advance by many months
    for _ in range(13):
        date.increment_month()

    assert date.month == 3
    assert date.year == 4
    assert date.total_months == 38


def test__init__():
    d = SimDate()
    assert d.month == 1
    assert d.year == 1
    assert d.total_months == 0

    d = SimDate(2001, 7)
    assert d.month == 7
    assert d.year == 2001
    assert d.total_months == 24006

    with pytest.raises(ValueError):
        # Year cannot be less than 1
        SimDate(-1, 10)

    with pytest.raises(ValueError):
        # Month cannot be less than 1
        SimDate(2023, -10)

    with pytest.raises(ValueError):
        # Month cannot be greater than 12
        SimDate(2023, 13)


def test_datetime_strptime_compat() -> None:
    """Test that SimDate.to_iso_str is compatible with datetime.strptime"""

    date = SimDate(2023, 6)
    parsed_date = datetime.datetime.strptime(str(date), "%Y-%m")

    assert parsed_date == datetime.datetime(2023, 6, 1)
