from typing import Tuple, cast, List

import esper

from neighborly.core.town.town import Town
from neighborly.core.time import SimDateTime
from neighborly.core.character import GameCharacter
from neighborly.core.location import Location


def get_date(world: esper.World) -> SimDateTime:
    return cast(SimDateTime, world.get_component(SimDateTime)[0][1])


def get_town(world: esper.World) -> Town:
    return cast(Town, world.get_component(Town)[0][1])


def get_character(world: esper.World, character_id: int) -> GameCharacter:
    return cast(GameCharacter, world.component_for_entity(character_id, GameCharacter))


def get_place(world: esper.World, location_id: int) -> Location:
    return cast(Location, world.component_for_entity(location_id, Location))


def move_character(world: esper.World, character_id: int, location_id: int) -> None:
    place: Location = get_place(world, location_id)
    character: GameCharacter = get_character(world, character_id)
    place.characters_present.append(character_id)
    character.location = location_id


def get_locations(world: esper.World) -> List[Tuple[int, Location]]:
    return cast(List[Tuple[int, Location]], world.get_component(Location))
