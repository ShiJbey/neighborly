from typing import Dict, List

import pytest

from neighborly.components.routine import (
    Routine,
    RoutineEntry,
    RoutinePriority,
    parse_schedule_str,
    time_str_to_int,
)
from neighborly.core.ai.brain import GoalNode
from neighborly.core.ecs import GameObject, World
from neighborly.core.time import Weekday
from neighborly.factories.routine import RoutineFactory


class _GoToWork(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _GoToWork)


class _GoHome(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _GoHome)


class _RunErrands(GoalNode):
    def is_complete(self) -> bool:
        return super().is_complete()

    def get_utility(self) -> Dict[GameObject, float]:
        return super().get_utility()

    def satisfied_goals(self) -> List[GoalNode]:
        return super().satisfied_goals()

    def __eq__(self, __o: object) -> bool:
        return isinstance(__o, _RunErrands)


def test_routine_entry_init():
    """Test that routines entries are created properly"""

    entry_0 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.HIGH)

    assert entry_0.start_time == 8
    assert entry_0.end_time == 12
    assert entry_0.goal == _GoHome()
    assert entry_0.priority == RoutinePriority.HIGH

    entry_1 = RoutineEntry([Weekday.Monday], 12, 15, _RunErrands())

    assert entry_1.priority == RoutinePriority.LOW

    with pytest.raises(ValueError):
        # start less than zero
        RoutineEntry([Weekday.Monday], -1, 12, _GoToWork())

    with pytest.raises(ValueError):
        # start greater than 23
        RoutineEntry([Weekday.Monday], 25, 12, _GoToWork())

    with pytest.raises(ValueError):
        # end less than zero
        RoutineEntry([Weekday.Monday], -1, -1, _GoToWork())

    with pytest.raises(ValueError):
        # end greater than 23
        RoutineEntry([Weekday.Monday], 10, 24, _GoToWork())


def test_routine_get_entry_for_time():
    routine = Routine()

    entry_0 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.HIGH)

    routine.add_entry(entry_0)

    result = routine.get_entry_for_time(Weekday.Monday, 10)

    assert result == entry_0

    result = routine.get_entry_for_time(Weekday.Tuesday, 10)

    assert result == None

    result = routine.get_entry_for_time(Weekday.Monday, 7)

    assert result == None


def test_routine_add_entry():
    routine = Routine()

    entry_0 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.LOW)
    entry_1 = RoutineEntry([Weekday.Monday], 8, 12, _GoToWork(), RoutinePriority.MED)
    entry_2 = RoutineEntry([Weekday.Monday], 8, 12, _RunErrands(), RoutinePriority.HIGH)
    entry_3 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.HIGH)

    routine.add_entry(entry_0)

    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_0

    routine.add_entry(entry_1)
    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_1

    routine.add_entry(entry_2)
    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_2

    routine.add_entry(entry_3)
    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_3


def test_routine_remove_entry():
    routine = Routine()

    entry_0 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.LOW)
    entry_1 = RoutineEntry([Weekday.Monday], 8, 12, _GoToWork(), RoutinePriority.MED)
    entry_2 = RoutineEntry([Weekday.Monday], 8, 12, _RunErrands(), RoutinePriority.HIGH)
    entry_3 = RoutineEntry([Weekday.Monday], 8, 12, _GoHome(), RoutinePriority.HIGH)

    routine.add_entry(entry_0)
    routine.add_entry(entry_2)
    routine.add_entry(entry_1)
    routine.add_entry(entry_3)

    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_3

    routine.remove_entry(entry_3)

    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_2

    routine.remove_entry(entry_2)

    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_1

    routine.remove_entry(entry_1)

    assert routine.get_entry_for_time(Weekday.Monday, 10) == entry_0


def test_routine_factory():
    world = World()
    gameobject = world.spawn_gameobject()
    gameobject.add_component(RoutineFactory().create(world))
    routine = gameobject.try_component(Routine)

    assert routine is not None


def test_time_str_to_int():
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
