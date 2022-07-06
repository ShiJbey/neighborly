from __future__ import annotations

from enum import IntEnum
from typing import Dict, List, Optional, Tuple, Union

from neighborly.core.ecs import Component, World

TIME_ALIAS = {
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

DAY_ALIAS = {
    "weekdays": "MTWRF",
    "weekends": "SU",
    "everyday": "MTWRFSU",
}

DAY_ABBREVIATION = {
    "M": "Monday",
    "T": "Tuesday",
    "W": "Wednesday",
    "R": "Thursday",
    "F": "Friday",
    "S": "Saturday",
    "U": "Sunday",
}


class RoutinePriority(IntEnum):
    LOW = 0
    MED = 1
    HIGH = 2


class RoutineEntry:
    __slots__ = (
        "start",
        "end",
        "priority",
        "description",
        "tags",
        "location",
        "activity",
    )

    def __init__(
        self,
        start: int,
        end: int,
        location: Union[str, int],
        activity: str,
        priority: RoutinePriority = RoutinePriority.LOW,
        tags: Optional[List[str]] = None,
    ) -> None:
        self.start: int = start
        self.end: int = end
        self.location: Union[str, int] = location
        self.activity: str = activity
        self.priority: RoutinePriority = priority
        self.tags: List[str] = [*tags] if tags else []
        if start < 0 or start > 23:
            raise ValueError("Start time must be within range [0, 23] inclusive.")
        if end < 0 or end > 24:
            raise ValueError("End time must be within range [0,23] inclusive.")
        if start >= end:
            raise ValueError("Start time must be less than end time.")

    def __repr__(self) -> str:
        return "{}({:2d}:00-{:2d}:00, location={}. activity={}, priority={}, tags={})".format(
            self.__class__.__name__,
            self.start,
            self.end,
            self.location,
            self.activity,
            self.priority,
            self.tags,
        )


class DailyRoutine:
    __slots__ = "_entries", "_tracks"

    def __init__(self) -> None:
        self._entries: List[RoutineEntry] = []
        self._tracks: dict[RoutinePriority, List[List[RoutineEntry]]] = {
            RoutinePriority.LOW: [list() for _ in range(24)],
            RoutinePriority.MED: [list() for _ in range(24)],
            RoutinePriority.HIGH: [list() for _ in range(24)],
        }

    def get_entries(self, hour: int) -> List[RoutineEntry]:
        """Get highest-priority entries for a given hour"""
        high_priority_entries = self._tracks[RoutinePriority.HIGH][hour]
        if high_priority_entries:
            return high_priority_entries

        med_priority_entries = self._tracks[RoutinePriority.MED][hour]
        if med_priority_entries:
            return med_priority_entries

        return self._tracks[RoutinePriority.LOW][hour]

    def add_entries(self, *entries: RoutineEntry) -> None:
        """Add an entry to the DailyRoutine"""
        for entry in entries:
            if entry in self._entries:
                continue

            self._entries.append(entry)

            track = self._tracks[entry.priority]

            for hour in range(entry.start, entry.end):
                track[hour].append(entry)

    def remove_entries(self, *entries: RoutineEntry) -> None:
        """Remove an entry from this DailyRoutine"""
        for entry in entries:
            self._entries.remove(entry)

            track = self._tracks[entry.priority]

            for hour in range(entry.start, entry.end):
                track[hour].remove(entry)

    def __repr__(self) -> str:
        return "{}([{}])".format(
            self.__class__.__name__,
            {str(p): [len(h) for h in t] for p, t in self._tracks.items()},
        )


class Routine(Component):
    """
    Manage a character's routine for the week
    """

    __slots__ = "_daily_routines"

    def __init__(self) -> None:
        super().__init__()
        self._daily_routines: dict[str, DailyRoutine] = {
            "monday": DailyRoutine(),
            "tuesday": DailyRoutine(),
            "wednesday": DailyRoutine(),
            "thursday": DailyRoutine(),
            "friday": DailyRoutine(),
            "saturday": DailyRoutine(),
            "sunday": DailyRoutine(),
        }

    def get_entries(self, day: str, hour: int) -> List[RoutineEntry]:
        """Get the scheduled activity for a given day and time"""
        try:
            return self._daily_routines[day.lower()].get_entries(hour)
        except KeyError as e:
            raise ValueError(f"Expected day of the week, but received '{day}'") from e

    def add_entries(self, days: List[str], *entries: RoutineEntry) -> None:
        """Add one or more entries to the daily routines on the given days"""
        for day in days:
            self._daily_routines[day].add_entries(*entries)

    def remove_entries(self, days: List[str], *entries: RoutineEntry) -> None:
        """Remove one or more entries from the daily routines on the given days"""
        for day in days:
            self._daily_routines[day].remove_entries(*entries)

    @classmethod
    def create(cls, world: World, **kwargs) -> Routine:
        return cls()


def time_str_to_int(s: str) -> int:
    """
    Convert 24-hour or 12-hour time string to int hour of the day

    Parameters
    ----------
    s : str
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
        # Make no assumptions about what time they are using
        # throw an error to be safe
        raise ValueError(
            f"Given string '{s}' is not of the form ##:00 or ##AM or ##PM."
        )


def parse_schedule_str(s: str) -> Dict[str, Tuple[int, int]]:
    """
    Convert a schedule string with days and time intervals

    Arguments
    ---------
    s: str
        String representing the hours for a routine entry

    Returns
    -------
    dict[str, tuple(int, int)]
        Time intervals for RoutineEntries mapped to the day of the week

    Notes
    -----
    Accepted strings formats are:
    - MTWRF 9:00 to 17:00, SU 10:00 to 15:00
    - MTWRFSU 9:00 to 21:00
    - weekdays 9:00 to 17:00, weekends 10:00 to 15:00
    - weekdays morning to evening, weekends late-morning to evening
    """
    clauses = s.split(",")

    schedule: dict[str, tuple[int, int]] = {}

    for clause in clauses:
        # all clauses should have 4 tokens
        # skip the "to"
        days, start_str, _, end_str = clause.split(" ")

        if days in DAY_ALIAS:
            days = DAY_ALIAS[days]

        if start_str in TIME_ALIAS:
            start_str = TIME_ALIAS[start_str]

        if end_str in TIME_ALIAS:
            end_str = TIME_ALIAS[end_str]

        start_hour = time_str_to_int(start_str)
        end_hour = time_str_to_int(end_str)

        for abbrev in days:
            day = DAY_ABBREVIATION[abbrev]
            schedule[day] = (start_hour, end_hour)

    return schedule
