from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

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


def get_top_activities(character_values: CharacterValues, n: int = 3) -> Tuple[str, ...]:
    """Return the top activities a character would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for name, activity in _activity_registry.items():
        score: int = np.dot(character_values.traits,
                            activity.character_traits.traits)
        scores.append((score, name))

    return tuple([activity_score[1] for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)][:n])
