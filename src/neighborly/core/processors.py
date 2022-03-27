import logging
import random
from typing import cast, Optional, Dict, List

import neighborly.ai.behavior_utils as behavior_utils
from neighborly.core.business import BusinessType
from neighborly.core.character.character import GameCharacter
from neighborly.core.character.values import CharacterValues
from neighborly.core.ecs import System, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipTag
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.status import StatusManager
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import Town

logger = logging.getLogger(__name__)


class CharacterProcessor(System):

    def process(self, *args, **kwargs):

        delta_time: float = kwargs["delta_time"]

        for _, character in self.world.get_component(GameCharacter):
            if not character.alive:
                continue

            self._grow_older(character, delta_time)

    def _grow_older(
            self, character: GameCharacter, hours: float
    ) -> None:
        """Increase the character's age and apply flags at major milestones"""
        if character.config.lifecycle.can_age:
            character.age += hours / HOURS_PER_YEAR


class SocializeProcessor(System):
    """Runs logic for characters socializing with the other characters at their location"""

    def process(self, *args, **kwargs):
        for _, character in self.world.get_component(GameCharacter):
            if not character.alive:
                continue

            self._socialize(self.world, character)

    def _socialize(self, world: World, character: GameCharacter) -> None:
        """Have all the characters talk to those around them"""
        if character.location:
            location = self.world.get_gameobject(character.location).get_component(Location)

            relationship_net = self.world.get_resource(RelationshipNetwork)

            character_id = character.gameobject.id

            # Socialize
            for other_character_id in location.characters_present:
                if other_character_id == character.gameobject.id:
                    continue

                if not relationship_net.has_connection(character_id, other_character_id):
                    relationship_net.add_connection(
                        character_id,
                        other_character_id,
                        Relationship(character_id, other_character_id)
                    )

                    other_character = world.get_gameobject(other_character_id).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(character.values, other_character.values)

                    relationship_net.get_connection(character_id, other_character_id).add_tag(
                        RelationshipTag("Compatibility", friendship_increment=compatibility))

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(character_id, other_character_id).add_tag(
                            RelationshipTag("Attracted", romance_increment=1))

                    logger.debug("{} met {}".format(
                        str(character.name),
                        str(world.get_gameobject(other_character_id).get_component(GameCharacter).name)
                    ))
                else:
                    relationship_net.get_connection(character_id, other_character_id).update()

                if not relationship_net.has_connection(other_character_id, character_id):
                    relationship_net.add_connection(
                        other_character_id,
                        character_id,
                        Relationship(
                            other_character_id,
                            character_id,
                        )
                    )

                    other_character = world.get_gameobject(other_character_id).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(character.values, other_character.values)

                    relationship_net.get_connection(other_character_id, character_id).add_tag(
                        RelationshipTag("Compatibility", friendship_increment=compatibility))

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(other_character_id, character_id).add_tag(
                            RelationshipTag("Attracted", romance_increment=1))

                    logger.debug("{} met {}".format(
                        str(world.get_gameobject(other_character_id).get_component(GameCharacter).name),
                        str(character.name)
                    ))
                else:
                    relationship_net.get_connection(other_character_id, character_id).update()


class RoutineProcessor(System):

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for entity, (character, routine) in self.world.get_components(
                GameCharacter, Routine
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            routine_entries = routine.get_activity(date.weekday_str, date.hour)

            if routine_entries:
                chosen_entry = engine.get_rng().choice(routine_entries)

                if type(chosen_entry.location) == str \
                        and chosen_entry.location in character.location_aliases:
                    behavior_utils.move_character(
                        self.world,
                        entity,
                        character.location_aliases[str(chosen_entry.location)],
                    )
                    return
                else:
                    behavior_utils.move_character(
                        self.world,
                        entity,
                        chosen_entry.location,
                    )
                    return

            potential_locations = behavior_utils.get_locations(self.world)
            if potential_locations:
                loc_id, _ = random.choice(potential_locations)
                behavior_utils.move_character(self.world, entity, loc_id)


class CityPlanner(System):
    """Responsible for adding residents to the town"""

    def __init__(self, weights: Optional[Dict[str, int]] = None):
        super().__init__()
        self.weights: Dict[str, int] = {}
        if weights:
            self.weights.update(weights)

    def process(self, *args, **kwargs) -> None:
        self.try_add_resident()
        self.try_add_business()

    def try_add_resident(self) -> None:
        # Find an empty space to build a house
        residence = self.try_build_house()
        if residence is None:
            residence = self.try_get_abandoned()

        if residence is None:
            return

        # Create a new character to live at the location
        engine = self.world.get_resource(NeighborlyEngine)

        character_archetypes = list(
            map(
                lambda archetype: (self.weights.get(archetype.get_type(), 1), archetype.get_type()),
                engine.get_character_archetypes()
            )
        )

        weights, names = zip(*character_archetypes)
        chosen_archetype = engine.get_rng().choices(names, weights=weights)[0]
        character = engine.create_character(chosen_archetype)

        self.world.add_gameobject(character)
        character.get_component(GameCharacter).location = residence.id
        character.get_component(GameCharacter).location_aliases['home'] = residence.id
        residence.get_component(Residence).add_tenant(character.id, True)
        residence.get_component(Location).characters_present.append(character.id)

    def try_build_house(self) -> Optional[GameObject]:
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)
        if town.layout.has_vacancy():
            space = town.layout.allocate_space()
            place = engine.create_residence("House")
            space.place_id = place.id
            place.get_component(Position2D).x = space.position[0]
            place.get_component(Position2D).y = space.position[1]
            self.world.add_gameobject(place)
            return place
        return None

    def try_get_abandoned(self) -> Optional[GameObject]:
        residences = list(filter(lambda res: res[1].is_vacant(), self.world.get_component(Residence)))
        if residences:
            return residences[0][1].gameobject
        return None

    def try_add_business(self) -> None:
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)

        # Get eligible businesses
        eligible_business_types = self.get_eligible_types(self.world)

        if not eligible_business_types:
            return

        business_type_to_build = engine.get_rng().choice(eligible_business_types).name

        if town.layout.has_vacancy():
            space = town.layout.allocate_space()
            engine.filter_place_archetypes({"includes": []})
            place = engine.create_business(business_type_to_build)
            space.place_id = place.id
            self.world.add_gameobject(place)
            logger.debug(f"Added business {place}")

    @classmethod
    def get_eligible_types(cls, world: World) -> List['BusinessType']:
        """
        Return all business types that may be built
        given the state of the simulation
        """
        population = world.get_resource(Town).population
        engine = world.get_resource(NeighborlyEngine)

        eligible_types: List['BusinessType'] = []

        for t in BusinessType.get_all_types():
            if t.instances >= t.max_instances:
                continue

            if population < t.min_population:
                continue

            try:
                engine.get_business_archetype(t.name)
            except KeyError:
                continue

            eligible_types.append(t)

        return eligible_types


class StatusManagerProcessor(System):

    def process(self, *args, **kwargs) -> None:
        delta_time: float = kwargs['delta_time']
        for _, status_manager in self.world.get_component(StatusManager):
            status_manager.update(delta_time=delta_time)


class LifeEventProcessor(System):
    _event_registry: Dict[str, LifeEvent] = {}

    @classmethod
    def register_event(cls, *events: LifeEvent) -> None:
        """Add a new life event to the registry"""
        for event in events:
            cls._event_registry[event.name] = event

    def process(self, *args, **kwargs) -> None:
        """Check if the life event"""

        rng = self.world.get_resource(NeighborlyEngine).get_rng()
        delta_time = kwargs["delta_time"]

        for entity, character in self.world.get_component(GameCharacter):
            for event in self._event_registry.values():
                if rng.random() < event.probability(character.gameobject) and event.precondition(character.gameobject):
                    event.effect(character.gameobject, {'delta_time': delta_time})
