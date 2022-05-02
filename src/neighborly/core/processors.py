import logging
from typing import Tuple, cast, Dict, List

from neighborly.core.activity import get_activity_flags
from neighborly.core.character.character import GameCharacter
from neighborly.core.character.values import CharacterValues
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.location import Location
from neighborly.core.relationship import (
    Relationship,
    RelationshipModifier,
    RelationshipTag,
)
from neighborly.core.routine import Routine
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime


logger = logging.getLogger(__name__)


class CharacterProcessor:
    """Updates the age of all alive characters"""

    def __call__(self, world: World, **kwargs):

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        for _, character in world.get_component(GameCharacter):
            if character.alive and character.character_def.lifecycle.can_age:
                character.age += delta_time / HOURS_PER_YEAR


class SocializeProcessor:
    """Runs logic for characters socializing with the other characters at their location"""

    def __call__(self, world: World, **kwargs):

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        if kwargs.get("full_sim"):
            return

        for _, character in world.get_component(GameCharacter):
            if not character.alive:
                continue

            self._socialize(world, character)

    def _socialize(self, world: World, character: GameCharacter) -> None:
        """Have all the characters talk to those around them"""
        if character.location:
            location = world.get_gameobject(character.location).get_component(Location)

            relationship_net = world.get_resource(RelationshipNetwork)

            character_id = character.gameobject.id

            # Socialize
            for other_character_id in location.characters_present:
                if other_character_id == character.gameobject.id:
                    continue

                if not relationship_net.has_connection(
                    character_id, other_character_id
                ):
                    relationship_net.add_connection(
                        character_id,
                        other_character_id,
                        Relationship(character_id, other_character_id),
                    )

                    other_character = world.get_gameobject(
                        other_character_id
                    ).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(
                        character.values, other_character.values
                    )

                    relationship_net.get_connection(
                        character_id, other_character_id
                    ).add_modifier(
                        RelationshipModifier(
                            "Compatibility", friendship_increment=compatibility
                        )
                    )

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(
                            character_id, other_character_id
                        ).add_modifier(
                            RelationshipModifier("Attracted", romance_increment=1)
                        )

                    logger.debug(
                        "{} met {}".format(
                            str(character.name),
                            str(
                                world.get_gameobject(other_character_id)
                                .get_component(GameCharacter)
                                .name
                            ),
                        )
                    )
                else:
                    relationship_net.get_connection(
                        character_id, other_character_id
                    ).update()

                if not relationship_net.has_connection(
                    other_character_id, character_id
                ):
                    relationship_net.add_connection(
                        other_character_id,
                        character_id,
                        Relationship(
                            other_character_id,
                            character_id,
                        ),
                    )

                    other_character = world.get_gameobject(
                        other_character_id
                    ).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(
                        character.values, other_character.values
                    )

                    relationship_net.get_connection(
                        other_character_id, character_id
                    ).add_modifier(
                        RelationshipModifier(
                            "Compatibility", friendship_increment=compatibility
                        )
                    )

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(
                            other_character_id, character_id
                        ).add_modifier(
                            RelationshipModifier("Attracted", romance_increment=1)
                        )

                    logger.debug(
                        "{} met {}".format(
                            str(
                                world.get_gameobject(other_character_id)
                                .get_component(GameCharacter)
                                .name
                            ),
                            str(character.name),
                        )
                    )
                else:
                    relationship_net.get_connection(
                        other_character_id, character_id
                    ).update()


class RoutineProcessor:
    def __call__(self, world: World, **kwargs) -> None:
        date = world.get_resource(SimDateTime)
        engine = world.get_resource(NeighborlyEngine)

        for entity, (character, routine) in world.get_components(
            GameCharacter, Routine
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            routine_entries = routine.get_activity(date.weekday_str, date.hour)

            if routine_entries:
                chosen_entry = engine.get_rng().choice(routine_entries)
                location_id = (
                    character.location_aliases[str(chosen_entry.location)]
                    if isinstance(chosen_entry.location, str)
                    else chosen_entry.location
                )
                move_character(
                    world,
                    entity,
                    location_id,
                )

            potential_locations = get_locations(world)
            if potential_locations:
                loc_id, _ = engine.get_rng().choice(potential_locations)
                move_character(world, entity, loc_id)


class TimeProcessor:
    def __call__(self, world: World, **kwargs):
        delta_time: int = kwargs["delta_time"]
        sim_time = world.get_resource(SimDateTime)
        sim_time.increment(hours=delta_time)


class LifeEventProcessor:
    _event_registry: Dict[str, LifeEvent] = {}

    @classmethod
    def register_event(cls, *events: LifeEvent) -> None:
        """Add a new life event to the registry"""
        for event in events:
            cls._event_registry[event.name] = event

    def __call__(self, world: World, **kwargs) -> None:
        """Check if the life event"""

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        if kwargs.get("full_sim"):
            return

        rng = world.get_resource(NeighborlyEngine).get_rng()
        delta_time = kwargs["delta_time"]

        for _, character in world.get_component(GameCharacter):
            for event in self._event_registry.values():
                if rng.random() < event.probability(
                    character.gameobject
                ) and event.precondition(character.gameobject):
                    event.effect(character.gameobject, delta_time=delta_time)


# ----------------------------------------
# Helpers
# ----------------------------------------


def move_character(world: World, character_id: int, location_id: int) -> None:
    destination: Location = world.get_gameobject(location_id).get_component(Location)
    character: GameCharacter = world.get_gameobject(character_id).get_component(
        GameCharacter
    )

    if location_id == character.location:
        return

    if character.location is not None:
        current_location: Location = world.get_gameobject(
            character.location
        ).get_component(Location)
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


def add_relationship_tag(
    world: World, owner_id: int, target_id: int, tag: RelationshipTag
) -> None:
    """Add a relationship modifier on the subject's relationship to the target"""
    world.get_resource(RelationshipNetwork).get_connection(owner_id, target_id).add_tag(
        tag
    )
