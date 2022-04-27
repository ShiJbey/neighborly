import logging
import random
from typing import cast, Optional, Dict, List

import neighborly.ai.behavior_utils as behavior_utils
from neighborly.core.business import BusinessDefinition
from neighborly.core.character.character import GameCharacter
from neighborly.core.character.values import CharacterValues
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipModifier
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import Town
from neighborly.data.statuses import MarriedStatus

logger = logging.getLogger(__name__)


class CharacterProcessor:
    """Updates the age of all alive characters"""

    def __call__(self, world: World, **kwargs):

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        for _, character in world.get_component(GameCharacter):
            if character.alive is False:
                continue

            self._grow_older(character, delta_time)

    def _grow_older(self, character: GameCharacter, hours: float) -> None:
        """Increase the character's age and apply flags at major milestones"""
        if character.character_def.lifecycle.can_age:
            character.age += hours / HOURS_PER_YEAR


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
            location = world.get_gameobject(
                character.location).get_component(Location)

            relationship_net = world.get_resource(RelationshipNetwork)

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

                    other_character = world.get_gameobject(
                        other_character_id).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(
                        character.values, other_character.values)

                    relationship_net.get_connection(character_id, other_character_id).add_tag(
                        RelationshipModifier("Compatibility", friendship_increment=compatibility))

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(character_id, other_character_id).add_tag(
                            RelationshipModifier("Attracted", romance_increment=1))

                    logger.debug("{} met {}".format(
                        str(character.name),
                        str(world.get_gameobject(
                            other_character_id).get_component(GameCharacter).name)
                    ))
                else:
                    relationship_net.get_connection(
                        character_id, other_character_id).update()

                if not relationship_net.has_connection(other_character_id, character_id):
                    relationship_net.add_connection(
                        other_character_id,
                        character_id,
                        Relationship(
                            other_character_id,
                            character_id,
                        )
                    )

                    other_character = world.get_gameobject(
                        other_character_id).get_component(GameCharacter)

                    # Add compatibility
                    compatibility = CharacterValues.calculate_compatibility(
                        character.values, other_character.values)

                    relationship_net.get_connection(other_character_id, character_id).add_tag(
                        RelationshipModifier("Compatibility", friendship_increment=compatibility))

                    if other_character.gender in character.attracted_to:
                        relationship_net.get_connection(other_character_id, character_id).add_tag(
                            RelationshipModifier("Attracted", romance_increment=1))

                    logger.debug("{} met {}".format(
                        str(world.get_gameobject(
                            other_character_id).get_component(GameCharacter).name),
                        str(character.name)
                    ))
                else:
                    relationship_net.get_connection(
                        other_character_id, character_id).update()


class RoutineProcessor:

    def __call__(self, world: World, **kwargs):
        date = world.get_resource(SimDateTime)
        engine = world.get_resource(NeighborlyEngine)

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        if kwargs.get("full_sim"):
            return

        for entity, (character, routine) in world.get_components(
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
                        world,
                        entity,
                        character.location_aliases[str(chosen_entry.location)],
                    )
                    return
                else:
                    behavior_utils.move_character(
                        world,
                        entity,
                        int(chosen_entry.location),
                    )
                    return

            potential_locations = behavior_utils.get_locations(world)
            if potential_locations:
                loc_id, _ = random.choice(potential_locations)
                behavior_utils.move_character(world, entity, loc_id)


class TimeProcessor:

    def __call__(self, world: World, **kwargs):
        delta_time: int = kwargs["delta_time"]
        sim_time = world.get_resource(SimDateTime)
        sim_time.increment(hours=delta_time)


class ResidentImmigrationSystem:
    """
    Adds new characters to the simulation

    Attributes
    ----------
    character_weights: Optional[Dict[str, int]]
        Relative frequency overrides for each of the character archetypes
        registered in the engine instance
    residence_weights: Optional[Dict[str, int]]
        Relative frequency overrides for each of the character archetypes
        registered in the engine instance
    """

    def __init__(
            self,
            character_weights: Optional[Dict[str, int]] = None,
            residence_weights: Optional[Dict[str, int]] = None,
    ) -> None:
        self.character_weights: Optional[Dict[str, int]] = character_weights
        self.residence_weights: Optional[Dict[str, int]] = residence_weights

    def __call__(self, world: World, **kwargs) -> None:
        engine = world.get_resource(NeighborlyEngine)

        delta_time: float = float(world.get_resource(SimDateTime).delta_time)

        if kwargs.get("full_sim"):
            return

        # Attempt to build or find a house for this character to move into
        residence = self.try_build_residence(engine, world)
        if residence is None:
            residence = self.try_get_abandoned(engine, world)
        if residence is None:
            return

        chosen_archetype = self.select_random_character_archetype(engine)
        character = engine.create_character(chosen_archetype, age_range='young_adult')

        world.add_gameobject(character)
        character.get_component(GameCharacter).location = residence.id
        character.get_component(
            GameCharacter).location_aliases['home'] = residence.id
        residence.get_component(Residence).add_tenant(character.id, True)
        residence.get_component(
            Location).characters_present.append(character.id)
        world.get_resource(Town).population += 1

        character_def = character.get_component(GameCharacter).character_def

        moved_with_spouse = engine.get_rng().random() < character_def.generation.family.probability_spouse

        spouse: Optional[GameObject] = None

        if moved_with_spouse:
            spouse = self.create_spouse(character.get_component(GameCharacter), engine, chosen_archetype)
            world.add_gameobject(spouse)
            spouse.get_component(GameCharacter).location = residence.id
            spouse.get_component(
                GameCharacter).location_aliases['home'] = residence.id
            residence.get_component(Residence).add_tenant(spouse.id, True)
            residence.get_component(
                Location).characters_present.append(spouse.id)
            world.get_resource(Town).population += 1

            # Marriage specific things
            character.add_component(MarriedStatus(spouse.id, str(spouse.get_component(GameCharacter).name)))
            spouse.add_component(MarriedStatus(character.id, str(character.get_component(GameCharacter).name)))

            # Update Relationship Net
            world.get_resource(RelationshipNetwork).add_connection(
                character.id,
                spouse.id,
                Relationship(character.id, spouse.id))

            world.get_resource(RelationshipNetwork).add_connection(
                spouse.id,
                character.id,
                Relationship(spouse.id, character.id))

        moved_with_children = engine.get_rng().random() < character_def.generation.family.probability_children

        if moved_with_children:
            children = self.create_children(
                character.get_component(GameCharacter),
                engine,
                chosen_archetype,
                spouse.get_component(GameCharacter) if spouse else None)

            for child in children:
                world.add_gameobject(child)
                child.get_component(GameCharacter).location = residence.id
                child.get_component(
                    GameCharacter).location_aliases['home'] = residence.id
                residence.get_component(Residence).add_tenant(child.id)
                residence.get_component(
                    Location).characters_present.append(child.id)
                world.get_resource(Town).population += 1

    def create_spouse(
            self,
            character: GameCharacter,
            engine: NeighborlyEngine,
            archetype_name: str,
    ) -> GameObject:
        return engine.create_character(
            archetype_name,
            age_range='young_adult',
            last_name=character.name.surname,
            attracted_to=[character.gender])

    def create_children(
            self,
            character: GameCharacter,
            engine: NeighborlyEngine,
            archetype_name: str,
            spouse: Optional[GameCharacter] = None
    ) -> List[GameObject]:

        n_children = engine.get_rng().randint(
            character.character_def.generation.family.num_children[0],
            character.character_def.generation.family.num_children[1]
        )

        spouse_age = spouse.age if spouse else 999
        min_parent_age = min(spouse_age, character.age)
        child_age_max = (min_parent_age - character.character_def.lifecycle.marriageable_age)

        children = []

        for _ in range(n_children):
            child = engine.create_character(
                archetype_name, age_range=(0, child_age_max), last_name=character.name.surname)
            children.append(child)

        return children

    def select_random_character_archetype(self, engine: NeighborlyEngine) -> str:
        """Randomly select from the available character archetypes using weighted random"""
        rng = engine.get_rng()

        archetype_names = [a.get_type() for a in engine.get_character_archetypes()]
        weights = []

        # override weights
        for name in archetype_names:
            weights.append(self.character_weights.get(name, 1))

        return rng.choices(archetype_names, weights=weights, k=1)[0]

    def try_build_residence(self, engine: NeighborlyEngine, world: World) -> Optional[GameObject]:
        town = world.get_resource(Town)

        if town.layout.has_vacancy():
            chosen_archetype = self.select_random_residence_archetype(engine)
            residence = engine.create_residence(chosen_archetype)
            space = town.layout.allocate_space(residence.id)
            residence.get_component(Position2D).x = space[0]
            residence.get_component(Position2D).y = space[1]
            world.add_gameobject(residence)
            return residence
        return None

    def select_random_residence_archetype(self, engine: NeighborlyEngine) -> str:
        """Randomly select from the available residence archetypes using weighted random"""
        rng = engine.get_rng()

        archetype_names = [a.get_type() for a in engine.get_residence_archetypes()]
        weights = []

        # override weights
        for name in archetype_names:
            weights.append(self.residence_weights.get(name, 1))

        return rng.choices(archetype_names, weights=weights, k=1)[0]

    def try_get_abandoned(self, engine: NeighborlyEngine, world: World) -> Optional[GameObject]:
        residences = list(
            filter(lambda res: res[1].is_vacant(), world.get_component(Residence)))
        if residences:
            return engine.get_rng().choice(residences)[1].gameobject
        return None


class CityPlanner:
    """Responsible for adding residents to the town"""

    def __init__(self, weights: Optional[Dict[str, int]] = None):
        self.weights: Dict[str, int] = {}
        if weights:
            self.weights.update(weights)

    def __call__(self, world: World, **kwargs):
        self.try_add_business(world)

    def try_add_business(self, world: World) -> None:
        town = world.get_resource(Town)
        engine = world.get_resource(NeighborlyEngine)

        # Get eligible businesses
        eligible_business_types = self.get_eligible_types(world)

        if not eligible_business_types:
            return

        business_type_to_build = engine.get_rng().choice(eligible_business_types).name

        if town.layout.has_vacancy():
            engine.filter_place_archetypes({"includes": []})
            place = engine.create_business(business_type_to_build)
            town.layout.allocate_space(place.id)
            world.add_gameobject(place)
            logger.debug(f"Added business {place}")

    @classmethod
    def get_eligible_types(cls, world: World) -> List['BusinessDefinition']:
        """
        Return all business types that may be built
        given the state of the simulation
        """
        population = world.get_resource(Town).population
        engine = world.get_resource(NeighborlyEngine)

        eligible_types: List['BusinessDefinition'] = []

        for t in BusinessDefinition.get_all_types():
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
                if rng.random() < event.probability(character.gameobject) and event.precondition(character.gameobject):
                    event.effect(character.gameobject, **{'delta_time': delta_time})
