from dataclasses import dataclass, field
from typing import Dict, Tuple
from neighborly.core.character.values import CharacterValues


@dataclass(frozen=True)
class Activity:
    name: str
    trait_names: Tuple[str, ...]
    character_traits: CharacterValues = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'character_traits', CharacterValues(
            {name: 1 for name in self.trait_names}, default=0))


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


# Register some default activities
register_activity(
    Activity('gambling', ('wealth', 'excitement', 'adventure', 'lust')))
register_activity(Activity('shopping', ('material', 'excitement')))
register_activity(Activity('recreation', ('health', 'excitement')))
register_activity(Activity('studying', ('knowledge', 'power', 'ambition')))
register_activity(Activity('errands', ('reliability', 'health', 'family')))
register_activity(Activity('eating', ('social', 'health', 'liesure-time')))
register_activity(Activity('socializing', ('social', 'friendship')))
register_activity(
    Activity('drinking', ('social', 'confidence', 'friendship', 'excitement')))
register_activity(
    Activity('relaxing', ('health', 'tranquility', 'liesure-time')))
