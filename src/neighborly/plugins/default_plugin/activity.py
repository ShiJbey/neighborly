from dataclasses import dataclass, field
from typing import Dict, Tuple, List

from neighborly.core.ecs import Component
from neighborly.plugins.default_plugin.character_values import CharacterValues


@dataclass(frozen=True)
class Activity:
    """Activities that a character can do at a location in the town

    Attributes
    ----------
    name: str
        The name of the activity
    traits_names: Tuple[str, ...]
        Character values that associated with this activity
    character_traits: CharacterValues
        CharacterValues instance that encodes the list of trait_names
        as a vector of 0's and 1's for non-applicable and applicable
        character values respectively.
    """

    name: str
    trait_names: Tuple[str, ...]
    character_traits: CharacterValues = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "character_traits",
            CharacterValues({name: 1 for name in self.trait_names}, default=0),
        )


_activity_registry: Dict[str, Activity] = {}
_activity_flags: Dict[str, int] = {}


def register_activity(activity: Activity) -> None:
    """Registers an activity instance for use in other places"""
    next_flag = 1 << len(_activity_registry.keys())
    _activity_registry[activity.name] = activity
    _activity_flags[activity.name] = next_flag


def get_activity_flags(*activities: str) -> Tuple[int, ...]:
    """Return flags corresponding to given activities"""
    return tuple([_activity_flags[activity] for activity in activities])


def get_activity(activity: str) -> Activity:
    """Return Activity instance corresponding to a given string"""
    return _activity_registry[activity]


def get_all_activities() -> List[Activity]:
    """Return all activity instances in the registry"""
    return list(_activity_registry.values())


class ActivityCenter(Component):
    def __init__(self, activities: List[str]) -> None:
        self.activities: List[str] = activities
        self.activity_flags: int = 0

        for activity in self.activities:
            self.activity_flags |= get_activity_flags(activity)[0]

    def has_flags(self, *flag_strs: str) -> bool:
        flags = get_activity_flags(*flag_strs)
        for flag in flags:
            if self.activity_flags & flag == 0:
                return False
        return True
