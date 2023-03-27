import pytest

from neighborly.core.time import SimDateTime, TimeDelta


def test_get_time_of_day():
    assert SimDateTime(hour=5).get_time_of_day() == "night"
    assert SimDateTime(hour=6).get_time_of_day() == "morning"
    assert SimDateTime(hour=7).get_time_of_day() == "day"
    assert SimDateTime(hour=17).get_time_of_day() == "day"
    assert SimDateTime(hour=18).get_time_of_day() == "evening"
    assert SimDateTime(hour=19).get_time_of_day() == "night"


def test_copy():
    original_date = SimDateTime()
    copy_date = original_date.copy()

    assert id(original_date) != id(copy_date)


def test__sub__():
    date_2 = SimDateTime(year=1, month=3, day=23)
    date_1 = SimDateTime(year=1, month=2, day=23)

    diff = date_2 - date_1

    assert diff.years == 0
    assert diff.months == 1
    assert diff.hours == 0
    assert diff.total_days == 28
    assert diff.total_hours == 28 * 24


def test__add__():
    date = SimDateTime()
    new_date = date + TimeDelta(months=5, days=27)
    assert new_date.month == 6
    assert new_date.day == 28
    assert date.month == 1
    assert date.day == 1


def test__iadd__():
    date = SimDateTime()
    date += TimeDelta(months=5, days=27)
    assert date.month == 6
    assert date.day == 28


def test__le__():
    assert (SimDateTime() <= SimDateTime()) is True
    assert (SimDateTime() <= SimDateTime(year=2000)) is True
    assert (SimDateTime(year=3000) <= SimDateTime()) is False


def test__lt__():
    assert (SimDateTime() < SimDateTime()) is False
    assert (SimDateTime() < SimDateTime(year=2000)) is True
    assert (SimDateTime(year=3000) < SimDateTime()) is False


def test__ge__():
    assert (SimDateTime() >= SimDateTime()) is True
    assert (SimDateTime() >= SimDateTime(year=2000)) is False
    assert (SimDateTime(year=3000) >= SimDateTime()) is True


def test__gt__():
    assert (SimDateTime() > SimDateTime()) is False
    assert (SimDateTime() > SimDateTime(year=2000)) is False
    assert (SimDateTime(year=3000) > SimDateTime()) is True


def test__eq__():
    assert (SimDateTime() == SimDateTime()) is True
    assert (SimDateTime() == SimDateTime(year=2000)) is False
    assert (SimDateTime(year=3000) == SimDateTime()) is False
    assert (SimDateTime(year=3000) == SimDateTime(year=3000)) is True
    assert SimDateTime(1, 4, 6) == SimDateTime(1, 4, 6)
    assert SimDateTime(2023, 6, 5) == SimDateTime(2023, 6, 5, 0)


def test_to_date_str():
    date = SimDateTime(2022, 6, 27)
    assert date.to_date_str() == "Fri, 27/06/2022 @ 00:00"

    date = SimDateTime(2022, 9, 3)
    assert date.to_date_str() == "Tue, 03/09/2022 @ 00:00"


def test_to_iso_str():
    date = SimDateTime(2022, 6, 27)
    assert date.to_iso_str() == "2022-06-27T00:00:00"

    date = SimDateTime(2022, 9, 3)
    assert date.to_iso_str() == "2022-09-03T00:00:00"


def test_to_hours():
    date = SimDateTime(2022, 6, 27)
    assert date.to_hours() == 16_301_328

    date = SimDateTime(2022, 9, 3)
    assert date.to_hours() == 16_302_768


def test_from_iso_str():
    date = SimDateTime.from_str("2022-11-10T00:36:19.362Z")
    assert date == SimDateTime(2022, 11, 10)


def test_from_str():
    date = SimDateTime.from_str("03/10/0002")
    assert date == SimDateTime(2, 10, 3)


def test_increment():
    date = SimDateTime(1, 1, 1)
    date.increment(hours=26)
    assert date == SimDateTime(1, 1, 2, 2)
    date.increment(hours=24, days=4)
    assert date == SimDateTime(1, 1, 7, 2)
    date.increment(days=28)
    assert date == SimDateTime(1, 2, 7, 2)
    date.increment(months=12)
    assert date == SimDateTime(2, 2, 7, 2)

    date = SimDateTime(2022, 12, 27)
    date.increment(days=1)
    assert date == SimDateTime(2022, 12, 28)
    date.increment(days=1)
    assert date == SimDateTime(2023, 1, 1)
    date.increment(days=336)
    assert date == SimDateTime(2024, 1, 1)


def test__init__():
    d = SimDateTime()
    assert d.day == 1
    assert d.hour == 0
    assert d.weekday == 0
    assert d.month == 1
    assert d.year == 1
    assert d.weekday_str == "Sunday"

    d = SimDateTime(2001, 7, 13, 8)
    assert d.day == 13
    assert d.hour == 8
    assert d.weekday == 5
    assert d.month == 7
    assert d.year == 2001
    assert d.weekday_str == "Friday"

    with pytest.raises(ValueError):
        # Year cannot be less than 1
        SimDateTime(-1, 10, 10)

    with pytest.raises(ValueError):
        # Month cannot be less than 1
        SimDateTime(0, 10, 10)

    with pytest.raises(ValueError):
        # Month cannot be greater than 12
        SimDateTime(2023, 13, 10)

    with pytest.raises(ValueError):
        # Day cannot be less than 1
        SimDateTime(2023, 12, 0)

    with pytest.raises(ValueError):
        # Day cannot be greater than 28
        SimDateTime(2023, 13, 29)
