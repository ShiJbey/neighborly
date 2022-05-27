import logging
from typing import List, cast, Dict, Optional
from neighborly.core.builtin.events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeElderEvent,
    BecomeYoungAdultEvent,
    HomePurchaseEvent,
    MoveResidenceEvent,
    SocializeEvent,
)

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.helpers import get_locations, move_character, try_generate_family
from neighborly.core.life_event import (
    LifeEventLogger,
    LifeEventRule,
    check_gameobject_preconditions,
    handle_gameobject_effects,
)
from neighborly.core.position import Position2D
from neighborly.core.residence import Residence
from neighborly.core.routine import Routine
from neighborly.core.builtin.statuses import (
    AdolescentStatus,
    AdultStatus,
    ChildStatus,
    ElderStatus,
    YoungAdultStatus,
)
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import Town
from neighborly.core.utils.utilities import chunk_list

logger = logging.getLogger(__name__)


class CharacterSystem:
    """Updates the age of all alive characters"""

    def __call__(self, world: World, delta_time: int, **kwargs):

        for _, character in world.get_component(GameCharacter):
            if "deceased" not in character.tags:
                character.age += float(delta_time) / HOURS_PER_YEAR


class RoutineSystem:
    def __call__(self, world: World, **kwargs) -> None:
        date = world.get_resource(SimDateTime)
        engine = world.get_resource(NeighborlyEngine)

        for entity, (character, routine) in world.get_components(
            GameCharacter, Routine
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            routine_entries = routine.get_entries(date.weekday_str, date.hour)

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


class TimeSystem:
    def __call__(self, world: World, delta_time: int, **kwargs):
        sim_time = world.get_resource(SimDateTime)
        sim_time.increment(hours=delta_time)


class LifeEventSystem:
    _event_registry: Dict[str, LifeEventRule] = {}

    def __init__(self, interval: int = 36) -> None:
        self.interval = interval
        self.time_until_run = interval

    @classmethod
    def register_event(cls, *events: LifeEventRule) -> None:
        """Add a new life event to the registry"""
        for event in events:
            cls._event_registry[event.name] = event

    def __call__(self, world: World, delta_time: int, **kwargs) -> None:
        """Check if life events will fire this round"""

        self.time_until_run -= delta_time

        # Run when timer reaches zero then reset
        if self.time_until_run > 0:
            return
        else:
            self.time_until_run = self.interval

        rng = world.get_resource(NeighborlyEngine).get_rng()

        for event_rule in self._event_registry.values():
            for event, participants in event_rule.pattern_fn(world):
                if rng.random() < event_rule.probability:
                    preconditions_pass = all(
                        [check_gameobject_preconditions(g, event) for g in participants]
                    )
                    if preconditions_pass:
                        for g in participants:
                            handle_gameobject_effects(g, event)
                    if event_rule.effect_fn:
                        event_rule.effect_fn(world)


class ChildSystem:
    """Ages children into adolescents"""

    def __call__(self, world: World, **kwargs) -> None:

        date_time = world.get_resource(SimDateTime)
        event_logger = world.get_resource(LifeEventLogger)

        for _, (character, child_status) in world.get_components(
            GameCharacter, ChildStatus
        ):
            character = cast(GameCharacter, character)
            if (
                character.age
                >= character.character_def.lifecycle.life_stages["adolescent"]
            ):
                character.gameobject.remove_component(child_status)
                character.gameobject.add_component(AdolescentStatus())
                event = BecomeAdolescentEvent(
                    timestamp=date_time.to_iso_str(),
                    character_id=character.gameobject.id,
                    character_name=str(character.name),
                )
                handle_gameobject_effects(character.gameobject, event)
                event_logger.log_event(event, [character.gameobject.id])


class AdolescentSystem:
    """Ages adolescents into young adults"""

    def __call__(self, world: World, **kwargs) -> None:
        date_time = world.get_resource(SimDateTime)
        event_logger = world.get_resource(LifeEventLogger)

        for _, (character, adolescent_status) in world.get_components(
            GameCharacter, AdolescentStatus
        ):
            character = cast(GameCharacter, character)
            if (
                character.age
                >= character.character_def.lifecycle.life_stages["young_adult"]
            ):
                character.gameobject.remove_component(adolescent_status)
                character.gameobject.add_component(YoungAdultStatus())
                event = BecomeYoungAdultEvent(
                    timestamp=date_time.to_iso_str(),
                    character_id=character.gameobject.id,
                    character_name=str(character.name),
                )
                handle_gameobject_effects(character.gameobject, event)
                event_logger.log_event(event, [character.gameobject.id])


class YoungAdultSystem:
    """Ages young adults into adults"""

    def __call__(self, world: World, **kwargs) -> None:
        date_time = world.get_resource(SimDateTime)
        event_logger = world.get_resource(LifeEventLogger)

        for _, (character, young_adult_status) in world.get_components(
            GameCharacter, YoungAdultStatus
        ):
            character = cast(GameCharacter, character)
            if character.age >= character.character_def.lifecycle.life_stages["adult"]:
                character.gameobject.remove_component(young_adult_status)
                character.gameobject.add_component(AdultStatus())
                event = BecomeAdultEvent(
                    timestamp=date_time.to_iso_str(),
                    character_id=character.gameobject.id,
                    character_name=str(character.name),
                )
                handle_gameobject_effects(character.gameobject, event)
                event_logger.log_event(event, [character.gameobject.id])


class AdultSystem:
    """Ages adults into elders"""

    def __call__(self, world: World, **kwargs) -> None:
        date_time = world.get_resource(SimDateTime)
        event_logger = world.get_resource(LifeEventLogger)

        for _, (character, adult_status) in world.get_components(
            GameCharacter, AdultStatus
        ):
            character = cast(GameCharacter, character)
            if character.age >= character.character_def.lifecycle.life_stages["elder"]:
                character.gameobject.remove_component(adult_status)
                character.gameobject.add_component(ElderStatus())
                event = BecomeElderEvent(
                    timestamp=date_time.to_iso_str(),
                    character_id=character.gameobject.id,
                    character_name=str(character.name),
                )
                handle_gameobject_effects(character.gameobject, event)
                event_logger.log_event(event, [character.gameobject.id])


class SocializeSystem:
    def __init__(self, interval: int = 12) -> None:
        self.interval = interval
        self.time_until_run = interval

    def __call__(self, world: World, **kwargs) -> None:
        for pair in chunk_list(world.get_component(GameCharacter), 2):
            character_0 = pair[0][1].gameobject
            character_1 = pair[1][1].gameobject

            # choose an interaction type
            interaction_type = (
                world.get_resource(NeighborlyEngine)
                .get_rng()
                .choice(
                    [
                        "neutral",
                        "friendly",
                        "flirty",
                        "bad",
                        "boring",
                        "good",
                        "exciting",
                    ]
                )
            )

            socialize_event = SocializeEvent(
                timestamp=world.get_resource(SimDateTime).to_iso_str(),
                character_names=(
                    str(character_0.get_component(GameCharacter).name),
                    str(character_1.get_component(GameCharacter).name),
                ),
                character_ids=(
                    character_0.id,
                    character_1.id,
                ),
                interaction_type=interaction_type,
            )

            character_0_consent = check_gameobject_preconditions(
                character_0, socialize_event
            )
            character_1_consent = check_gameobject_preconditions(
                character_1, socialize_event
            )

            if character_0_consent and character_1_consent:
                handle_gameobject_effects(character_0, socialize_event)
                handle_gameobject_effects(character_1, socialize_event)


class AddResidentsSystem:
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

    __slots__ = "interval", "time_until_run", "character_weights", "residence_weights"

    def __init__(
        self,
        interval: int = 24,
        character_weights: Optional[Dict[str, int]] = None,
        residence_weights: Optional[Dict[str, int]] = None,
    ) -> None:
        self.interval = 24
        self.time_until_run = interval
        self.character_weights: Dict[str, int] = (
            character_weights if character_weights else {}
        )
        self.residence_weights: Dict[str, int] = (
            residence_weights if residence_weights else {}
        )

    def __call__(self, world: World, delta_time: int, **kwargs) -> None:
        engine = world.get_resource(NeighborlyEngine)
        date_time = world.get_resource(SimDateTime)
        event_logger = world.get_resource(LifeEventLogger)

        self.time_until_run -= delta_time

        # Run when timer reaches zero then reset
        if self.time_until_run > 0:
            return
        else:
            self.time_until_run = self.interval

        # Attempt to build or find a house for this character to move into
        residence = self.try_build_residence(engine, world)
        if residence is None:
            residence = self.try_get_abandoned(engine, world)
        if residence is None:
            return

        chosen_archetype = self.select_random_character_archetype(engine)
        character = engine.create_character(chosen_archetype, age_range="young_adult")
        world.add_gameobject(character)

        family = try_generate_family(engine, character)
        spouse: Optional[GameObject] = family.get("spouse")
        children: List[GameObject] = family.get("children", [])

        if spouse:
            world.add_gameobject(spouse)
        for c in children:
            world.add_gameobject(c)

        # Create a home purchase event

        home_owner_ids: List[int] = [character.id]
        home_owner_names: List[str] = [str(character.get_component(GameCharacter).name)]

        if spouse:
            home_owner_ids.append(spouse.id)
            home_owner_names.append(str(spouse.get_component(GameCharacter).name))

        home_purachase_event = HomePurchaseEvent(
            timestamp=date_time.to_iso_str(),
            character_ids=tuple(home_owner_ids),
            character_names=tuple(home_owner_names),
            residence_id=residence.id,
        )

        handle_gameobject_effects(character, home_purachase_event)
        if spouse:
            handle_gameobject_effects(spouse, home_purachase_event)

        event_logger.log_event(home_purachase_event, home_owner_ids)

        # Create and handle move event

        resident_ids: List[int] = [character.id]
        resident_names: List[str] = [str(character.get_component(GameCharacter).name)]

        residence_comp = residence.get_component(Residence)
        residence_comp.add_tenant(character.id, True)

        if spouse:
            resident_ids.append(spouse.id)
            resident_names.append(str(spouse.get_component(GameCharacter).name))
            residence_comp.add_tenant(spouse.id, True)

        for c in children:
            resident_ids.append(c.id)
            resident_names.append(str(c.get_component(GameCharacter).name))
            residence_comp.add_tenant(c.id)

        residence_move_event = MoveResidenceEvent(
            timestamp=date_time.to_iso_str(),
            residence_id=residence.id,
            character_ids=tuple(resident_ids),
            character_names=tuple(resident_names),
        )

        for i in resident_ids:
            handle_gameobject_effects(world.get_gameobject(i), residence_move_event)

        event_logger.log_event(residence_move_event, resident_ids)

    def select_random_character_archetype(self, engine: NeighborlyEngine) -> str:
        """Randomly select from the available character archetypes using weighted random"""
        rng = engine.get_rng()

        archetype_names = [a.get_name() for a in engine.get_character_archetypes()]
        weights = []

        # override weights
        for name in archetype_names:
            weights.append(self.character_weights.get(name, 1))

        return rng.choices(archetype_names, weights=weights, k=1)[0]

    def try_build_residence(
        self, engine: NeighborlyEngine, world: World
    ) -> Optional[GameObject]:
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

        archetype_names = [a.get_name() for a in engine.get_residence_archetypes()]
        weights = []

        # override weights
        for name in archetype_names:
            weights.append(self.residence_weights.get(name, 1))

        return rng.choices(archetype_names, weights=weights, k=1)[0]

    def try_get_abandoned(
        self, engine: NeighborlyEngine, world: World
    ) -> Optional[GameObject]:
        residences = list(
            filter(lambda res: res[1].is_vacant(), world.get_component(Residence))
        )
        if residences:
            return engine.get_rng().choice(residences)[1].gameobject
        return None
