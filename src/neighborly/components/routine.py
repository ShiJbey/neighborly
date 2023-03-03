from __future__ import annotations

from enum import IntEnum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from neighborly.core.ecs import Component
from neighborly.core.time import Weekday


class RoutinePriority(IntEnum):
    LOW = 0
    MED = 1
    HIGH = 2


class RoutineEntry:
    """
    An entry within a routine for when an entity needs to be
    at a specific location and for how long

    Attributes
    ----------
    start: int
        The time that this routine task begins
    end: int
        The time that this routine task ends
    priority: RoutinePriority
        The priority associated with this task. High priority tasks
        override lower priority tasks
    location: Union[str, int]
        The location or location alias for a location. Location
        aliases can be looked up on the GameCharacter class
    tags: Set[str]
        A set of tags associated with this entry
    """

    __slots__ = (
        "start",
        "end",
        "priority",
        "tags",
        "location",
    )

    def __init__(
        self,
        start: int,
        end: int,
        location: Union[str, int],
        priority: RoutinePriority = RoutinePriority.LOW,
        tags: Optional[List[str]] = None,
    ) -> None:
        self.start: int = start
        self.end: int = end
        self.location: Union[str, int] = location
        self.priority: RoutinePriority = priority
        self.tags: Set[str] = set(*tags) if tags else set()

        if start < 0 or start > 23:
            raise ValueError("Start time must be within range [0, 23] inclusive.")
        if end < 0 or end > 23:
            raise ValueError("End time must be within range [0,23] inclusive.")

    def __repr__(self) -> str:
        return "{}({:2d}:00-{:2d}:00, location={}, priority={}, tags={})".format(
            self.__class__.__name__,
            self.start,
            self.end,
            self.location,
            self.priority,
            self.tags,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start": self.start,
            "end": self.end,
            "location": self.location,
            "priority": self.priority,
            "tags": list(self.tags),
        }


class DailyRoutine:
    """
    A collection of RoutineEntries that manage where an
    entity should be for a given day

    Attributes
    ----------
    _entries: Dict[str, RoutineEntry]
        All the RoutineEntry instances associated with this DailyRoutine
    _tracks: Dict[RoutinePriority, List[List[RoutineEntry]]
        Pointers to the RoutineEntry instances organized by hour
    """

    __slots__ = "_entries", "_tracks"

    def __init__(self) -> None:
        self._entries: Dict[str, RoutineEntry] = {}
        # Each track holds 24 slots, one for each hour
        # Each slot holds a list of events registered to that time
        self._tracks: Dict[RoutinePriority, List[List[RoutineEntry]]] = {
            RoutinePriority.LOW: [list() for _ in range(24)],
            RoutinePriority.MED: [list() for _ in range(24)],
            RoutinePriority.HIGH: [list() for _ in range(24)],
        }

    def get(self, hour: int) -> List[RoutineEntry]:
        """Get highest-priority entries for a given hour"""
        high_priority_entries = self._tracks[RoutinePriority.HIGH][hour]
        if high_priority_entries:
            return high_priority_entries

        med_priority_entries = self._tracks[RoutinePriority.MED][hour]
        if med_priority_entries:
            return med_priority_entries

        return self._tracks[RoutinePriority.LOW][hour]

    def add(self, entry_id: str, entry: RoutineEntry) -> None:
        """
        Add an entry to the DailyRoutine

        Parameters
        ----------
        entry_id: str
            Unique ID used to remove this entry at a later time
        entry: RoutineEntry
            Entry to add to the routine
        """
        if entry_id in self._entries:
            return

        self._entries[entry_id] = entry

        track = self._tracks[entry.priority]

        if entry.start > entry.end:
            duration = (23 - entry.start) + entry.end
            for hour in range(entry.start, entry.start + duration):
                track[hour % 24].append(entry)

        else:
            for hour in range(entry.start, entry.end):
                track[hour].append(entry)

    def remove(self, entry_id: str) -> None:
        """
        Remove an entry from this DailyRoutine

        Parameters
        ----------
        entry_id: str
            Unique ID of the entry to remove from the routine
        """
        entry = self._entries[entry_id]

        track = self._tracks[entry.priority]

        if entry.start > entry.end:
            duration = (23 - entry.start) + entry.end
            for hour in range(entry.start, entry.start + duration):
                track[hour % 24].remove(entry)

        else:
            for hour in range(entry.start, entry.end):
                track[hour].remove(entry)

        del self._entries[entry_id]

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            self._entries,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"entries": {k: v.to_dict() for k, v in self._entries.items()}}


class Routine(Component):
    """
    Collection of DailyRoutine Instances that manages an entity's
    behavior for a 7-day week

    Attributes
    ----------
    _daily_routines: Tuple[DailyRoutine, DailyRoutine, DailyRoutine,
        DailyRoutine, DailyRoutine, DailyRoutine, DailyRoutine]
        DailyRoutines in order from day zero to seven
    """

    __slots__ = "_daily_routines"

    def __init__(self) -> None:
        super().__init__()
        self._daily_routines: List[DailyRoutine] = [
            DailyRoutine(),
            DailyRoutine(),
            DailyRoutine(),
            DailyRoutine(),
            DailyRoutine(),
            DailyRoutine(),
            DailyRoutine(),
        ]

    def get_entry(self, day: int, hour: int) -> Optional[RoutineEntry]:
        """Get a single activity for a given day and time"""
        entries = self._daily_routines[day].get(hour)
        if entries:
            return entries[-1]
        return None

    def get_entries(self, day: int, hour: int) -> List[RoutineEntry]:
        """Get the scheduled activity for a given day and time"""
        return self._daily_routines[day].get(hour)

    def add_entries(
        self, entry_id: str, days: List[int], *entries: RoutineEntry
    ) -> None:
        """Add one or more entries to the daily routines on the given days"""
        for day in days:
            for entry in entries:
                self._daily_routines[day].add(entry_id, entry)

    def remove_entries(self, days: List[int], entry_id: str) -> None:
        """Remove one or more entries from the daily routines on the given days"""
        for day in days:
            self._daily_routines[day].remove(entry_id)

    def __repr__(self) -> str:
        return f"Routine({self._daily_routines})"

    def to_dict(self) -> Dict[str, Any]:
        return {"days": [dr.to_dict() for dr in self._daily_routines]}


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
        try:
            return int(s)
        except ValueError:
            # Make no assumptions about what time they are using
            # throw an error to be safe
            raise ValueError(
                f"Given string '{s}' is not an int or of the form ##:00 or ##AM or ##PM."
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
