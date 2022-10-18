from __future__ import annotations

from typing import Dict, List, Set, Tuple

import numpy.typing as npt

from neighborly.core.ecs import Component
from neighborly.core.personal_values import PersonalValues


class Activity:
    """Activities that a entity can do at a location in the town

    Attributes
    ----------
    name: str
        The name of the activity
    trait_names: Tuple[str, ...]
        Character values that associated with this activity
    personal_values: PersonalValues
        The list of trait_names encoded as a vector of 0's and 1's
        for non-applicable and applicable entity values respectively.
    """

    __slots__ = "name", "trait_names", "personal_values"

    def __init__(self, name: str, trait_names: List[str]) -> None:
        self.name: str = name
        self.trait_names: List[str] = trait_names
        self.personal_values: npt.NDArray = PersonalValues(
            {name: 1 for name in self.trait_names}, default=0
        ).traits


class ActivityLibrary:
    """
    Stores information about what kind of activities carious locations
    are known for. Activities help characters make decisions about
    where they want to travel when they have free time.
    """

    _activity_registry: Dict[str, Activity] = {}
    _activity_flags: Dict[str, int] = {}

    @classmethod
    def add(cls, activity: Activity) -> None:
        """Registers an activity instance for use in other places"""
        next_flag = 1 << len(cls._activity_registry.keys())
        cls._activity_registry[activity.name] = activity
        cls._activity_flags[activity.name] = next_flag

    @classmethod
    def get_flags(cls, *activities: str) -> Tuple[int, ...]:
        """Return flags corresponding to given activities"""
        return tuple([cls._activity_flags[activity] for activity in activities])

    @classmethod
    def get(cls, activity: str) -> Activity:
        """Return Activity instance corresponding to a given string"""
        return cls._activity_registry[activity]

    @classmethod
    def get_all(cls) -> List[Activity]:
        """Return all activity instances in the registry"""
        return list(cls._activity_registry.values())


class Activities(Component):
    """Tracks what activities are available to do at a location"""

    __slots__ = "activities"

    def __init__(self, *activities: str) -> None:
        super().__init__()
        self.activities: Set[Activity] = set()
        for activity in activities:
            self.activities.add(ActivityLibrary.get(activity))

    def has_activity(self, activity: str) -> bool:
        return activity in self.activities
