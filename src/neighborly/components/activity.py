from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, Set

from neighborly.core.ecs import Component


@dataclass(frozen=True)
class Activity:
    """An activity that characters do at a location

    An activity is a single reference shared by multiple components with the same
    activities. Activity instances should not be created directly. They should be
    instantiated using the ActivityLibrary.get(...) method.

    Attributes
    ----------
    uid: int
        The unique identifier for this activity
    name: str
        The name of the activity
    """

    uid: int
    name: str

    def __hash__(self) -> int:
        return self.uid

    def __str__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Activity):
            return self.uid == other.uid
        raise TypeError(f"Expected Activity but was {type(object)}")


class Activities(Component):
    """A collection of all the activities available at a location

    Systems look for an Activities component to:
    1) Help characters determine where they frequent/want to go
    2) Add content to flesh out the narrative setting of the simulation
    """

    __slots__ = "_activities"

    def __init__(self, activities: Set[Activity]) -> None:
        """
        Parameters
        ----------
        activities: Set[Activity]
            A collection of activities
        """
        super().__init__()
        self._activities: Set[Activity] = activities

    def to_dict(self) -> Dict[str, Any]:
        return {"activities": [str(a) for a in self._activities]}

    def add_activity(self, activity: Activity) -> None:
        self._activities.add(activity)

    def remove_activity(self, activity: Activity) -> None:
        self._activities.remove(activity)

    def __iter__(self) -> Iterator[Activity]:
        return self._activities.__iter__()

    def __contains__(self, activity: Activity) -> bool:
        return activity in self._activities

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._activities.__repr__()})"
