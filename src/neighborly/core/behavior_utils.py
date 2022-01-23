from typing import List, Tuple, cast

import esper

from neighborly.core.activity import get_activity_flags
from neighborly.core.character.character import GameCharacter
from neighborly.core.location import Location
from neighborly.core.time import SimDateTime
from neighborly.core.town.town import Town
from neighborly.core.weather import Weather, WeatherManager


def get_date(world: esper.World) -> SimDateTime:
    return cast(SimDateTime, world.get_component(SimDateTime)[0][1])


def get_weather(self) -> Weather:
    return self.world.component_for_entity(
        self.simulation_manager, WeatherManager
    ).current_weather


def get_town(world: esper.World) -> Town:
    return cast(Town, world.get_component(Town)[0][1])


def get_character(world: esper.World, character_id: int) -> GameCharacter:
    return cast(GameCharacter, world.component_for_entity(character_id, GameCharacter))


def get_place(world: esper.World, location_id: int) -> Location:
    return cast(Location, world.component_for_entity(location_id, Location))


def move_character(world: esper.World, character_id: int, location_id: int) -> None:
    destination: Location = get_place(world, location_id)
    character: GameCharacter = get_character(world, character_id)

    if location_id == character.location:
        return

    if character.location is not None:
        current_location: Location = get_place(world, character.location)
        current_location.characters_present.remove(character_id)

    destination.characters_present.append(character_id)
    character.location = location_id


def get_locations(world: esper.World) -> List[Tuple[int, Location]]:
    return sorted(
        cast(List[Tuple[int, Location]], world.get_component(Location)),
        key=lambda pair: pair[0],
    )


def find_places_with_activities(world: esper.World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have the given activities"""
    locations = cast(List[Tuple[int, Location]], world.get_component(Location))

    matches: List[int] = []

    for location_id, location in locations:
        if location.has_flags(*activities):
            matches.append(location_id)

    return matches


def find_places_with_any_activities(world: esper.World, *activities: str) -> List[int]:
    """Return a list of entity ID for locations that have any of the given activities

    Results are sorted by how many activities they match
    """

    flags = get_activity_flags(*activities)

    def score_location(loc: Location) -> int:
        score: int = 0
        for flag in flags:
            if loc.activity_flags & flag > 0:
                score += 1
        return score

    locations = cast(List[Tuple[int, Location]], world.get_component(Location))

    matches: List[Tuple[int, int]] = []

    for location_id, location in locations:
        score = score_location(location)
        if score > 0:
            matches.append((score, location_id))

    return [match[1] for match in sorted(matches, key=lambda m: m[0], reverse=True)]


def is_adult(world: esper.World, character_id: int) -> bool:
    """Return tru if the character is an adult"""
    character = get_character(world, character_id)
    return character.age >= character.config.lifecycle.adult_age


def is_senior(world: esper.World, character_id: int) -> bool:
    """Return tru if the character is an adult"""
    character = get_character(world, character_id)
    return character.age >= character.config.lifecycle.senior_age
