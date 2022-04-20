from enum import IntEnum
from typing import Dict, List, Optional, Union

from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


class RoutinePriority(IntEnum):
    LOW = 0
    MED = 1
    HIGH = 2


class RoutineEntry:
    __slots__ = "start", "end", "priority", "description", "tags", "location", "activity"

    def __init__(
            self,
            start: int,
            end: int,
            location: Union[str, int],
            activity: str,
            priority: RoutinePriority = RoutinePriority.LOW,
            tags: Optional[List[str]] = None
    ) -> None:
        self.start: int = start
        self.end: int = end
        self.location: Union[str, int] = location
        self.activity: str = activity
        self.priority: RoutinePriority = priority
        self.tags: List[str] = [*tags] if tags else []

    def __repr__(self) -> str:
        return "{}({:2d}:00-{:2d}:00, location={}. activity={}, priority={}, tags={})".format(
            self.__class__.__name__,
            self.start,
            self.end,
            self.location,
            self.activity,
            self.priority,
            self.tags
        )


class DailyRoutine:
    __slots__ = "_entries", "_tracks"

    def __init__(self) -> None:
        self._entries: List[RoutineEntry] = []
        self._tracks: Dict[RoutinePriority, List[List[RoutineEntry]]] = {
            RoutinePriority.LOW: [list() for _ in range(24)],
            RoutinePriority.MED: [list() for _ in range(24)],
            RoutinePriority.HIGH: [list() for _ in range(24)],
        }

    def get_activity(self, hour: int) -> List[RoutineEntry]:
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
            {str(p): [len(h) for h in t] for p, t in self._tracks.items()}
        )


class Routine(Component):
    """
    Manage a character's routine for the week
    """

    __slots__ = "_daily_routines"

    def __init__(self) -> None:
        super().__init__()
        self._daily_routines: Dict[str, DailyRoutine] = {
            "monday": DailyRoutine(),
            "tuesday": DailyRoutine(),
            "wednesday": DailyRoutine(),
            "thursday": DailyRoutine(),
            "friday": DailyRoutine(),
            "saturday": DailyRoutine(),
            "sunday": DailyRoutine(),
        }

    def get_activity(self, day: str, hour: int) -> List[RoutineEntry]:
        """Get the scheduled activity for a given day and time"""
        try:
            return self._daily_routines[day.lower()].get_activity(hour)
        except KeyError as e:
            raise ValueError(
                f"Expected day of the week, but received '{day}'") from e

    def add_entries(self, days: List[str], *entries: RoutineEntry) -> None:
        """Add one or more entries to the daily routines on the given days"""
        for day in days:
            self._daily_routines[day].add_entries(*entries)

    def remove_entries(self, days: List[str], *entries: RoutineEntry) -> None:
        """Remove one or more entries from the daily routines on the given days"""
        for day in days:
            self._daily_routines[day].remove_entries(*entries)


class RoutineFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Routine")

    def create(self, spec: ComponentSpec, **kwargs) -> Routine:
        return Routine()
