from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, Optional, Set

from neighborly.core.ecs import Component


class Activities(Component):
    """A collection of all the activities available at a location

    Systems look for an Activities component to:
    1) Help characters determine where they frequent/want to go
    2) Add content to flesh out the narrative setting of the simulation
    """

    __slots__ = "_activities"

    def __init__(self, activities: Optional[Iterable[str]] = None) -> None:
        """
        Parameters
        ----------
        activities: Set[str]
            A collection of activities
        """
        super().__init__()
        self._activities: Set[str] = set()

        if activities:
            for name in activities:
                self.add_activity(name)

    def to_dict(self) -> Dict[str, Any]:
        return {"activities": [str(a) for a in self._activities]}

    def add_activity(self, activity: str) -> None:
        self._activities.add(activity.lower())

    def remove_activity(self, activity: str) -> None:
        self._activities.remove(activity.lower())

    def __iter__(self) -> Iterator[str]:
        return self._activities.__iter__()

    def __contains__(self, activity: str) -> bool:
        return activity.lower() in self._activities

    def __str__(self) -> str:
        return ", ".join(self._activities)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._activities.__repr__()})"
