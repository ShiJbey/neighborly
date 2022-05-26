import pytest

from neighborly.core.routine import (
    DailyRoutine,
    Routine,
    RoutineEntry,
    RoutinePriority,
    parse_schedule_str,
    time_str_to_int,
)


def test_construct_routine_entry():
    """Test that routines entries are created properly"""

    entry_0 = RoutineEntry(8, 12, "home", "liesure", RoutinePriority.HIGH)

    assert entry_0.start == 8
    assert entry_0.end == 12
    assert entry_0.location == "home"
    assert entry_0.priority == RoutinePriority.HIGH

    entry_1 = RoutineEntry(12, 15, "park", "liesure")

    assert entry_1.priority == RoutinePriority.LOW

    with pytest.raises(ValueError):
        # start greater than the end
        RoutineEntry(6, 3, "home", "liesure")
        # start less than zero
        RoutineEntry(-1, 12, "work", "work")
        # end greater than 23
        RoutineEntry(10, 24, "work", "work")
        # start and end times are the same
        RoutineEntry(10, 10, "home", "painting")


def test_daily_routine():
    """Test retrieving routine entries from a daily routine"""

    daily_routine = DailyRoutine()

    # Check that there are no entries
    assert daily_routine.get_entries(8) == []

    # Add a low priority entry
    go_to_park = RoutineEntry(12, 15, "park", "liesure")
    daily_routine.add_entries(go_to_park)
    assert daily_routine.get_entries(12) == [go_to_park]

    # add two mid-level priority entries
    buy_milk = RoutineEntry(12, 13, "store", "errands", RoutinePriority.MED)
    walk_dog = RoutineEntry(11, 13, "park", "walk dog", RoutinePriority.MED)
    daily_routine.add_entries(walk_dog, buy_milk)
    assert daily_routine.get_entries(12) == [walk_dog, buy_milk]

    # add one high-level entry
    mail_taxes = RoutineEntry(11, 16, "post office", "errands", RoutinePriority.HIGH)
    daily_routine.add_entries(mail_taxes)
    assert daily_routine.get_entries(12) == [mail_taxes]

    # remove the high-level entry
    daily_routine.remove_entries(mail_taxes)
    daily_routine.remove_entries(walk_dog)
    assert daily_routine.get_entries(12) == [buy_milk]


def test_routine():
    """Test Routine class"""

    routine = Routine()

    buy_milk = RoutineEntry(12, 13, "store", "errands", RoutinePriority.MED)
    walk_dog = RoutineEntry(11, 13, "park", "walk dog", RoutinePriority.MED)
    mail_taxes = RoutineEntry(11, 16, "post office", "errands", RoutinePriority.HIGH)

    routine.add_entries(["monday", "tuesday"], walk_dog)
    routine.add_entries(["monday"], mail_taxes)
    routine.add_entries(["tuesday"], buy_milk)

    assert routine.get_entries("monday", 12) == [mail_taxes]
    assert routine.get_entries("tuesday", 12) == [walk_dog, buy_milk]

    routine.remove_entries(["monday"], mail_taxes)
    routine.remove_entries(["tuesday"], buy_milk)

    assert routine.get_entries("monday", 12) == [walk_dog]
    assert routine.get_entries("tuesday", 12) == [walk_dog]


def test_timestr_to_int():
    """Test converting 24-hour or 12-hour time strings to ints"""
    assert time_str_to_int("01:00") == 1
    assert time_str_to_int("1:00") == 1
    assert time_str_to_int("1AM") == 1
    assert time_str_to_int("12AM") == 0
    assert time_str_to_int("00:00") == 0
    assert time_str_to_int("0:00") == 0
    assert time_str_to_int("5PM") == 17


def test_parse_schedule_str():
    """Tests parsing schedule strings"""
    assert parse_schedule_str("weekdays morning to evening")["Monday"] == (8, 17)
    assert "Monday" not in parse_schedule_str("weekends evening to midnight")
    assert parse_schedule_str("weekends evening to midnight")["Saturday"] == (17, 23)
    assert parse_schedule_str("weekends evening to midnight")["Sunday"] == (17, 23)
    assert parse_schedule_str("R 2AM to 7PM")["Thursday"] == (2, 19)
