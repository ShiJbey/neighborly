from __future__ import annotations

import logging
from typing import cast

from neighborly.core.character import GameCharacter
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.helpers import get_locations, move_character
from neighborly.core.life_event import (
    LifeEvent,
    LifeEventLogger,
    LifeEventRule,
    check_gameobject_preconditions,
    handle_gameobject_effects,
)
from neighborly.core.routine import Routine
from neighborly.core.status import (
    AdolescentStatus,
    AdultStatus,
    ChildStatus,
    ElderStatus,
    YoungAdultStatus,
)
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
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
    _event_registry: dict[str, LifeEventRule] = {}

    @classmethod
    def register_event(cls, *events: LifeEventRule) -> None:
        """Add a new life event to the registry"""
        for event in events:
            cls._event_registry[event.name] = event

    def __call__(self, world: World, **kwargs) -> None:
        """Check if life events will fire this round"""
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
            if character.age >= character.character_def.lifecycle.life_stages["teen"]:
                character.gameobject.remove_component(child_status)
                character.gameobject.add_component(AdolescentStatus())
                event = LifeEvent(
                    event_type="became-teen",
                    timestamp=date_time.to_iso_str(),
                    character=character,
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
                event = LifeEvent(
                    event_type="became-young-adult",
                    timestamp=date_time.to_iso_str(),
                    character=character,
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
                event = LifeEvent(
                    event_type="became-adult",
                    timestamp=date_time.to_iso_str(),
                    character=character,
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
                event = LifeEvent(
                    event_type="became-elder",
                    timestamp=date_time.to_iso_str(),
                    character=character,
                )
                handle_gameobject_effects(character.gameobject, event)
                event_logger.log_event(event, [character.gameobject.id])


class SocializeSystem:
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

            socialize_event = LifeEvent(
                event_type="Socialize",
                timestamp=world.get_resource(SimDateTime).to_iso_str(),
                interaction=interaction_type,
                characters=[character_0, character_1],
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
