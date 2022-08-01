import logging
from typing import Dict, List, Optional, Set, cast

from neighborly.core.builtin.events import (
    HomePurchaseEvent,
    MoveResidenceEvent,
    SocializeEvent,
)
from neighborly.core.builtin.statuses import Child, InRelationship, YoungAdult
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.helpers import get_locations, move_to_location, try_generate_family
from neighborly.core.life_event import LifeEventRule
from neighborly.core.location import Location
from neighborly.core.relationship import Relationship, RelationshipTag
from neighborly.core.residence import Residence
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import Routine
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime, TimeDelta
from neighborly.core.utils.utilities import chunk_list

logger = logging.getLogger(__name__)


class RoutineSystem:
    def __call__(self, world: World, **kwargs) -> None:
        date = world.get_resource(SimDateTime)
        engine = world.get_resource(NeighborlyEngine)

        for _, (character, routine) in world.get_components(GameCharacter, Routine):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            routine_entries = routine.get_entries(date.weekday_str, date.hour)

            if routine_entries:
                chosen_entry = engine.rng.choice(routine_entries)
                location_id = (
                    character.location_aliases[str(chosen_entry.location)]
                    if isinstance(chosen_entry.location, str)
                    else chosen_entry.location
                )
                move_to_location(
                    world,
                    character,
                    world.get_gameobject(location_id).get_component(Location),
                )
            else:

                potential_locations = get_locations(world)

                if potential_locations:
                    _, location = engine.rng.choice(potential_locations)
                    move_to_location(world, character, location)


class LinearTimeSystem:
    """
    Advances simulation time using a linear time increment
    """

    __slots__ = "increment"

    def __init__(self, increment: TimeDelta) -> None:
        self.increment: TimeDelta = increment

    def __call__(self, world: World, **kwargs) -> None:
        """Advance time"""
        current_date = world.get_resource(SimDateTime)
        current_date += self.increment


class DynamicLoDTimeSystem:
    """
    Updates the current date/time in the simulation
    using a variable level-of-detail where a subset
    of the days during a year receive more simulation
    ticks

    Attributes
    ----------
    days_per_year: int
        How many high LoD days to simulate per year

    """

    def __init__(self, days_per_year: int) -> None:
        self._low_lod_delta_time: int = 6
        self._days_per_year: int = days_per_year
        self._high_lod_days_for_year: Set[int] = set()
        self._current_year: int = -1

        assert (
            days_per_year < DAYS_PER_YEAR
        ), f"Days per year is greater than max: {DAYS_PER_YEAR}"
        assert days_per_year > 0, f"Days per year must be greater than 0"

    def __call__(self, world: World, **kwargs):
        current_date = world.get_resource(SimDateTime)
        rng = world.get_resource(NeighborlyEngine).rng

        if self._current_year != current_date.year:
            # Generate a new set of days to simulate this year
            self._high_lod_days_for_year = set(
                rng.sample(
                    range(
                        current_date.to_ordinal(),
                        current_date.to_ordinal() + DAYS_PER_YEAR,
                    ),
                    self._days_per_year,
                )
            )
            self._current_year = current_date.year

        if current_date.to_ordinal() in self._high_lod_days_for_year:
            # Increment the time using a smaller time increment (High LoD)
            current_date.increment(hours=self._low_lod_delta_time)
            return
        else:
            # Increment by one whole day (Low LoD)
            current_date.increment(hours=24)

    @staticmethod
    def _generate_sample_days(
        world: World, start_date: SimDateTime, end_date: SimDateTime, n: int
    ) -> List[int]:
        """Samples n days from each year between the start and end dates"""
        ordinal_start_date: int = start_date.to_ordinal()
        ordinal_end_date: int = end_date.to_ordinal()

        sampled_ordinal_dates: List[int] = []

        current_date = ordinal_start_date

        while current_date < ordinal_end_date:
            sampled_dates = world.get_resource(DefaultRNG).sample(
                range(current_date, current_date + DAYS_PER_YEAR), n
            )
            sampled_ordinal_dates.extend(sorted(sampled_dates))
            current_date = min(current_date + DAYS_PER_YEAR, ordinal_end_date)

        return sampled_ordinal_dates


class LifeEventSystem:
    _event_registry: Dict[str, LifeEventRule] = {}

    def __init__(self, interval: int = 48) -> None:
        self.interval = interval
        self.time_until_run = interval

    @classmethod
    def register_event(cls, *events: LifeEventRule) -> None:
        """Add a new life event to the registry"""
        for event in events:
            cls._event_registry[event.name] = event

    def __call__(self, world: World, **kwargs) -> None:
        """Check if life events will fire this round"""
        delta_time = world.get_resource(SimDateTime).delta_time
        self.time_until_run -= delta_time

        # Run when timer reaches zero then reset
        if self.time_until_run > 0:
            return
        else:
            self.time_until_run = self.interval

        # rng = world.get_resource(DefaultRNG)
        # for event_rule in self._event_registry.values():
        #     for event, participants in event_rule.pattern_fn(world):
        #         if rng.random() < event_rule.probability:
        #             preconditions_pass = all(
        #                 [check_gameobject_preconditions(g, event) for g in participants]
        #             )
        #             if preconditions_pass:
        #                 for g in participants:
        #                     handle_gameobject_effects(g, event)
        #             if event_rule.effect_fn:
        #                 event_rule.effect_fn(world)


class SocializeSystem:
    def __init__(self, interval: int = 12) -> None:
        self.interval = interval
        self.time_until_run = interval

    def __call__(self, world: World, **kwargs) -> None:
        for pair in chunk_list(world.get_component(GameCharacter), 2):
            character_0 = pair[0][1].gameobject
            character_1 = pair[1][1].gameobject

            # choose an interaction type
            interaction_type = world.get_resource(DefaultRNG).choice(
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

            if character_0.will_handle_event(
                socialize_event
            ) and character_1.will_handle_event(socialize_event):
                character_0.handle_event(socialize_event)
                character_1.handle_event(socialize_event)


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

    def __call__(self, world: World, **kwargs) -> None:
        engine = world.get_resource(NeighborlyEngine)
        date_time = world.get_resource(SimDateTime)

        return

        for _, residence in world.get_component(Residence):
            character = engine.spawn_character(world)
            character.add_component(YoungAdult())
            world.add_gameobject(character)

            family = try_generate_family(engine, character)
            spouse: Optional[GameObject] = family.get("spouse")
            children: List[GameObject] = family.get("children", [])

            if spouse:
                world.add_gameobject(spouse)
                spouse.add_component(YoungAdult())

                spouse.get_component(RelationshipManager).add_relationship(
                    Relationship(spouse.id, character.id)
                )
                relationship = spouse.get_component(
                    RelationshipManager
                ).get_relationship(character.id)
                if relationship:
                    relationship.add_tags(RelationshipTag.Spouse)
                spouse.add_component(
                    InRelationship("marriage", character.id, str(character.name))
                )

                character.get_component(RelationshipManager).add_relationship(
                    Relationship(character.id, spouse.id)
                )
                relationship = character.get_component(
                    RelationshipManager
                ).get_relationship(spouse.id)
                if relationship:
                    relationship.add_tags(RelationshipTag.Spouse)
                character.add_component(
                    InRelationship("marriage", spouse.id, str(spouse.name))
                )
            for c in children:
                world.add_gameobject(c)
                c.add_component(Child())

            # Create a home purchase event

            home_owner_ids: List[int] = [character.id]
            home_owner_names: List[str] = [
                str(character.get_component(GameCharacter).name)
            ]

            if spouse:
                home_owner_ids.append(spouse.id)
                home_owner_names.append(str(spouse.get_component(GameCharacter).name))

            home_purchase_event = HomePurchaseEvent(
                timestamp=date_time.to_iso_str(),
                character_ids=tuple(home_owner_ids),
                character_names=tuple(home_owner_names),
                residence_id=residence.id,
            )

            character.handle_event(home_purchase_event)
            if spouse:
                spouse.handle_event(home_purchase_event)

            # Create and handle move event

            resident_ids: List[int] = [character.id]
            resident_names: List[str] = [
                str(character.get_component(GameCharacter).name)
            ]

            residence_comp = residence.gameobject.get_component(Residence)
            residence_comp.add_resident(character.id)
            residence_comp.add_owner(character.id)

            if spouse:
                resident_ids.append(spouse.id)
                resident_names.append(str(spouse.get_component(GameCharacter).name))
                residence_comp.add_resident(spouse.id)
                residence_comp.add_owner(spouse.id)

            for c in children:
                resident_ids.append(c.id)
                resident_names.append(str(c.get_component(GameCharacter).name))
                residence_comp.add_resident(c.id)

            residence_move_event = MoveResidenceEvent(
                timestamp=date_time.to_iso_str(),
                residence_id=residence.id,
                character_id=tuple(resident_ids),
                character_name=tuple(resident_names),
            )

            for i in resident_ids:
                world.get_gameobject(i).handle_event(residence_move_event)
