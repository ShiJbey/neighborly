"""Helper functions used by various systems in this plugin"""
from typing import List, Tuple

import numpy as np

from neighborly.core.ecs import World

from .activity import ActivityCenter, get_activity_flags, get_all_activities
from .character_values import CharacterValues


def get_top_activities(
    character_values: CharacterValues, n: int = 3
) -> Tuple[str, ...]:
    """Return the top activities a character would enjoy given their values"""

    scores: List[Tuple[int, str]] = []

    for activity in get_all_activities():
        score: int = int(
            np.dot(character_values.traits, activity.character_traits.traits)
        )
        scores.append((score, activity.name))

    return tuple(
        [
            activity_score[1]
            for activity_score in sorted(scores, key=lambda s: s[0], reverse=True)
        ][:n]
    )


def find_places_with_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have the given activities"""
    locations = world.get_component(ActivityCenter)

    matches: List[int] = []

    for location_id, location in locations:
        if location.has_flags(*activities):
            matches.append(location_id)

    return matches


def find_places_with_any_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have any of the given activities

    Results are sorted by how many activities they match
    """

    flags = get_activity_flags(*activities)

    def score_location(loc: ActivityCenter) -> int:
        location_score: int = 0
        for flag in flags:
            if loc.activity_flags & flag > 0:
                location_score += 1
        return location_score

    locations = world.get_component(ActivityCenter)

    matches: List[Tuple[int, int]] = []

    for location_id, location in locations:
        score = score_location(location)
        if score > 0:
            matches.append((score, location_id))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]
