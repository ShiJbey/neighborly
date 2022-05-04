import logging
from typing import Tuple, cast, Dict, List

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.location import Location
from neighborly.core.relationship import RelationshipTag
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


def add_relationship_tag(
    world: World, owner_id: int, target_id: int, tag: RelationshipTag
) -> None:
    """Add a relationship modifier on the subject's relationship to the target"""
    world.get_resource(RelationshipNetwork).get_connection(owner_id, target_id).add_tag(
        tag
    )
