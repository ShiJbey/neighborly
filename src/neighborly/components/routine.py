"""Neighborly Routine module.

Routines suggest to characters what they should do at a given time. Each routine is
divided into seven daily routines, one for each day of the week.

"""
from __future__ import annotations

import bisect
from enum import IntEnum
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from neighborly.core.ai.brain import GoalNode
from neighborly.core.ecs import Component, ISerializable
from neighborly.core.time import Weekday


class RoutinePriority(IntEnum):
    """An enumeration of routine entry priority values."""

    LOW = 0
    MED = 1
    HIGH = 2


ROUTINE_PRIORITY_BOOSTS: Dict[RoutinePriority, float] = {
    RoutinePriority.LOW: 0.1,
    RoutinePriority.MED: 0.3,
    RoutinePriority.HIGH: 0.5,
}
"""Priority value buffs applied to goals based on their routine priority."""


class RoutineEntry:
    """An entry within a routine.

    Notes
    -----
    If the end time is less than the start time, then the entry wraps around to the
    following day.
    """

    __slots__ = "days", "start_time", "end_time", "goal", "priority"

    days: Set[Weekday]
    """What days is this entry for."""

    start_time: int
    """The time that this routine task begins."""

    end_time: int
    """The time that this routine task ends."""

    goal: GoalNode
    """The location or location alias for a location."""

    priority: RoutinePriority
    """How important is this entry."""

    def __init__(
        self,
        days: Iterable[Weekday],
        start_time: int,
        end_time: int,
        goal: GoalNode,
        priority: RoutinePriority = RoutinePriority.LOW,
    ) -> None:
        """
        Parameters
        ----------
        days
            What days is this entry for.
        start_time
            The starting time for this entry (0 <= start <= 23).
        end_time
            The starting time for this entry (0 <= end <= 23).
        goal
            What should the character want to do at this time.
        priority
            How important is this entry (defaults to RoutinePriority.LOW).
        """
        self.days = set(days)
        self.start_time = start_time
        self.end_time = end_time
        self.goal = goal
        self.priority = priority

        if start_time < 0 or start_time > 23:
            raise ValueError("Start time must be within range [0, 23] inclusive.")

        if end_time < 0 or end_time > 23:
            raise ValueError("End time must be within range [0,23] inclusive.")

    def __repr__(self) -> str:
        return "{}({:2d}:00-{:2d}:00, goal={})".format(
            self.__class__.__name__,
            self.start_time,
            self.end_time,
            type(self.goal).__name__,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "days": [d.name for d in self.days],
            "start_time": self.start_time,
            "end_time": self.end_time,
            "goal": type(self.goal).__name__,
            "priority": self.priority.name,
        }

    def __le__(self, other: RoutineEntry) -> bool:
        return self.priority <= other.priority

    def __lt__(self, other: RoutineEntry) -> bool:
        return self.priority < other.priority

    def __ge__(self, other: RoutineEntry) -> bool:
        return self.priority >= other.priority

    def __gt__(self, other: RoutineEntry) -> bool:
        return self.priority > other.priority


class Routine(Component, ISerializable):
    """Collection of daily routines that manage behavior for a 7-day week."""

    __slots__ = "_entries"

    _entries: List[RoutineEntry]
    """All the entries within the routine."""

    def __init__(self) -> None:
        super().__init__()
        self._entries = []

    def get_entry_for_time(self, day: Weekday, hour: int) -> Optional[RoutineEntry]:
        """Get an entry for a given day and time.

        Parameters
        ----------
        day
            The day of the daily routine
        hour
            The hour within the daily routine

        Returns
        -------
        RoutineEntry or None
            Returns an entry, or None if schedule is clear for that time.
        """
        # iterate in reverse because the entries are stored in increasing priority order

        for entry in reversed(self._entries):
            if day not in entry.days:
                continue

            if entry.end_time >= entry.start_time:
                if entry.start_time <= hour < entry.end_time:
                    return entry
            else:
                if hour >= entry.start_time or hour < entry.end_time:
                    return entry

        return None

    def add_entry(self, entry: RoutineEntry) -> None:
        """Add an entry to a daily routine.

        Parameters
        ----------
        entry
            The routine entry to add.
        """
        # Entries are stored as a priority queue based on entry priority
        bisect.insort(self._entries, entry)

    def remove_entry(self, entry: RoutineEntry) -> None:
        """Remove an entry from a daily routine.

        Parameters
        ----------
        day
            The day to remove the entry from
        entry
            The entry to remove.
        """
        self._entries.remove(entry)

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            self._entries,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": [e.to_dict() for e in self._entries]}


def time_str_to_int(s: str) -> int:
    """Convert 24-hour or 12-hour time string to int hour of the day.

    Parameters
    ----------
    s
        24-hour or 12-hour time string

    Returns
    -------
    int
        Hour of the day between [0,24)
    """
    if ":" in s:
        # this is a 24-hour string
        return int(s.strip().split(":")[0])
    elif "am" in s.lower():
        # This is a 12-hour string
        return int(s.lower().split("am")[0].strip()) % 12
    elif "pm" in s.lower():
        # This is a 12-hour string
        return (int(s.lower().split("pm")[0].strip()) % 12) + 12
    else:
        try:
            return int(s)
        except ValueError:
            # Make no assumptions about what time they are using
            # throw an error to be safe
            raise ValueError(
                f"Given string '{s}' is not an int or of the form ##:00 or ##AM or ##PM."
            )


def parse_schedule_str(s: str) -> Dict[str, Tuple[int, int]]:
    """Convert a schedule string with days and time intervals.

    Arguments
    ---------
    s
        String representing the hours for a routine entry.

    Returns
    -------
    dict[str, tuple[int, int]]
        Time intervals for RoutineEntries mapped to the day of the week.

    Notes
    -----
    Accepted strings formats are:
    - MTWRF 9:00 to 17:00, SU 10:00 to 15:00
    - MTWRFSU 9:00 to 21:00
    - weekdays 9:00 to 17:00, weekends 10:00 to 15:00
    - weekdays morning to evening, weekends late-morning to evening
    """

    day_alias = {
        "weekdays": "MTWRF",
        "weekends": "SU",
        "everyday": "MTWRFSU",
    }

    time_alias = {
        "early morning": "02:00",
        "dawn": "06:00",
        "morning": "08:00",
        "late-morning": "10:00",
        "noon": "12:00",
        "afternoon": "14:00",
        "evening": "17:00",
        "night": "21:00",
        "midnight": "23:00",
    }

    clauses = s.split(",")

    schedule: dict[str, tuple[int, int]] = {}

    for clause in clauses:
        # all clauses should have 4 tokens
        # skip the "to"
        days, start_str, _, end_str = clause.split(" ")

        if days in day_alias:
            days = day_alias[days]

        if start_str in time_alias:
            start_str = time_alias[start_str]

        if end_str in time_alias:
            end_str = time_alias[end_str]

        start_hour = time_str_to_int(start_str)
        end_hour = time_str_to_int(end_str)

        for abbrev in days:
            day = str(Weekday.from_abbr(abbrev))
            schedule[day] = (start_hour, end_hour)

    return schedule
