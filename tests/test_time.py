import pytest

from neighborly.core.time import get_time_of_day, SimDateTime


def test_get_time_of_day():
    with pytest.raises(IndexError):
        get_time_of_day(-1)
        get_time_of_day(24)

    assert get_time_of_day(5) == 'night'
    assert get_time_of_day(6) == 'morning'
    assert get_time_of_day(7) == 'day'
    assert get_time_of_day(17) == 'day'
    assert get_time_of_day(18) == 'evening'
    assert get_time_of_day(19) == 'night'


def test_increment_time():
    time = SimDateTime()
    time.increment(hours=26)
    assert time.hour == 2
    assert time.day == 1
    time.increment(hours=24, days=4)
    assert time.hour == 2
    assert time.day == 6
    time.increment(days=28)
    assert time.hour == 2
    assert time.day == 6
    assert time.month == 1
    time.increment(months=12)
    assert time.month == 1
    assert time.year == 1


def test_time_serialize():
    time = SimDateTime.from_str('2-10-3-1')
    assert time.day == 3
    assert time.hour == 1
    assert time.weekday == 3
    assert time.month == 10
    assert time.year == 2


def test_time_init():
    time = SimDateTime()
    assert time.day == 0
    assert time.hour == 0
    assert time.weekday == 0
    assert time.month == 0
    assert time.year == 0
    assert time.weekday_str == 'Sunday'
