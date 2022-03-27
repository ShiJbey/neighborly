from typing import List, Tuple, cast

from neighborly.core.activity import get_activity_flags
from neighborly.core.character.character import GameCharacter
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.location import Location
from neighborly.core.relationship import RelationshipTag
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime
from neighborly.core.town import Town


def get_date(world: World) -> SimDateTime:
    return world.get_resource(SimDateTime)


def get_town(world: World) -> Town:
    return world.get_resource(Town)


def get_relationship_net(world: World) -> RelationshipNetwork:
    return world.get_resource(RelationshipNetwork)


def get_engine(world: World) -> NeighborlyEngine:
    return world.get_resource(NeighborlyEngine)


def move_character(world: World, character_id: int, location_id: int) -> None:
    destination: Location = world.get_gameobject(location_id).get_component(Location)
    character: GameCharacter = world.get_gameobject(character_id).get_component(GameCharacter)

    if location_id == character.location:
        return

    if character.location is not None:
        current_location: Location = world.get_gameobject(character.location).get_component(Location)
        current_location.remove_character(character_id)

    destination.add_character(character_id)
    character.location = location_id


def get_locations(world: World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def find_places_with_activities(world: World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have the given activities"""
    locations = cast(List[Tuple[int, Location]], world.get_component(Location))

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

    def score_location(loc: Location) -> int:
        location_score: int = 0
        for flag in flags:
            if loc.activity_flags & flag > 0:
                location_score += 1
        return location_score

    locations = cast(List[Tuple[int, Location]], world.get_component(Location))

    matches: List[Tuple[int, int]] = []

    for location_id, location in locations:
        score = score_location(location)
        if score > 0:
            matches.append((score, location_id))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]


def is_child(world: World, character_id: int) -> bool:
    """Return True if the character is a child"""
    character = world.get_gameobject(character_id).get_component(GameCharacter)
    return character.age < character.config.lifecycle.adult_age


def is_adult(world: World, character_id: int) -> bool:
    """Return True if the character is an adult"""
    character = world.get_gameobject(character_id).get_component(GameCharacter)
    return character.age >= character.config.lifecycle.adult_age


def is_senior(world: World, character_id: int) -> bool:
    """Return True if the character is a senior"""
    character = world.get_gameobject(character_id).get_component(GameCharacter)
    return character.age >= character.config.lifecycle.senior_age


def add_relationship_tag(
        world: World, owner_id: int, target_id: int, tag: RelationshipTag
) -> None:
    """Add a relationship modifier on the subject's relationship to the target"""
    get_relationship_net(world).get_connection(owner_id, target_id).add_tag(tag)
