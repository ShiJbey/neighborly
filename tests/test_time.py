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
    assert new_date.month == 5
    assert new_date.day == 27
    assert date.month == 0
    assert date.day == 0


def test__iadd__():
    date = SimDateTime()
    date += TimeDelta(months=5, days=27)
    assert date.month == 5
    assert date.day == 27


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


def test_to_date_str():
    date = SimDateTime(2022, 6, 27)
    assert date.to_date_str() == "Sat, 27/06/2022 @ 00:00"

    date = SimDateTime(2022, 9, 3)
    assert date.to_date_str() == "Wed, 03/09/2022 @ 00:00"


def test_to_iso_str():
    date = SimDateTime(2022, 6, 27)
    assert date.to_iso_str() == "2022-06-27T00:00:00"

    date = SimDateTime(2022, 9, 3)
    assert date.to_iso_str() == "2022-09-03T00:00:00"


def test_to_hours():
    date = SimDateTime(2022, 6, 27)
    assert date.to_hours() == 16310088

    date = SimDateTime(2022, 9, 3)
    assert date.to_hours() == 16311528


def test_to_ordinal():
    date = SimDateTime(2022, 6, 27)
    assert date.to_ordinal() == 679587

    date = SimDateTime(2022, 9, 3)
    assert date.to_ordinal() == 679647


def test_from_ordinal():
    date = SimDateTime.from_ordinal(679710)
    assert date.day == 10
    assert date.hour == 0
    assert date.weekday == 3
    assert date.month == 11
    assert date.year == 2022


def test_from_iso_str():
    date = SimDateTime.from_iso_str("2022-11-10T00:36:19.362Z")
    assert date.day == 10
    assert date.hour == 0
    assert date.weekday == 3
    assert date.month == 11
    assert date.year == 2022


def test_from_str():
    date = SimDateTime.from_str("2-10-3-1")
    assert date.day == 3
    assert date.hour == 1
    assert date.weekday == 3
    assert date.month == 10
    assert date.year == 2


def test_increment():
    date = SimDateTime()
    date.increment(hours=26)
    assert date.hour == 2
    assert date.day == 1
    date.increment(hours=24, days=4)
    assert date.hour == 2
    assert date.day == 6
    date.increment(days=28)
    assert date.hour == 2
    assert date.day == 6
    assert date.month == 1
    date.increment(months=12)
    assert date.month == 1
    assert date.year == 1


def test__init__():
    time = SimDateTime()
    assert time.day == 0
    assert time.hour == 0
    assert time.weekday == 0
    assert time.month == 0
    assert time.year == 0
    assert time.weekday_str == "Sunday"
