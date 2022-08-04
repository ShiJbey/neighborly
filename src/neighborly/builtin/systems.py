from __future__ import annotations

import logging
from typing import List, Optional, Set, cast

from neighborly.builtin.helpers import get_locations, move_to_location, move_residence, generate_child_character, \
    generate_young_adult_character
from neighborly.builtin.statuses import Married, Deceased, Child, Teen, YoungAdult, Adult, Elder
from neighborly.core.business import Business, BusinessStatus, Occupation, BusinessArchetype, BusinessArchetypeLibrary
from neighborly.core.character import GameCharacter, CharacterArchetype, CharacterArchetypeLibrary
from neighborly.core.ecs import GameObject, World, ISystem
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEventLog, LifeEvent, EventRole
from neighborly.core.location import Location
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipTag, RelationshipGraph
from neighborly.core.residence import Residence, ResidenceArchetypeLibrary, ResidenceArchetype
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import Routine
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime, TimeDelta, HOURS_PER_YEAR
from neighborly.core.town import Town, LandGrid
from neighborly.core.utils.utilities import chunk_list

logger = logging.getLogger(__name__)


class RoutineSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for _, (character, routine) in self.world.get_components(GameCharacter, Routine):
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
                    self.world,
                    character,
                    self.world.get_gameobject(location_id).get_component(Location),
                )
            else:

                potential_locations = get_locations(self.world)

                if potential_locations:
                    _, location = engine.rng.choice(potential_locations)
                    move_to_location(self.world, character, location)


class LinearTimeSystem(ISystem):
    """
    Advances simulation time using a linear time increment
    """

    __slots__ = "increment"

    def __init__(self, increment: TimeDelta) -> None:
        super().__init__()
        self.increment: TimeDelta = increment

    def process(self, *args, **kwargs) -> None:
        """Advance time"""
        current_date = self.world.get_resource(SimDateTime)
        current_date += self.increment


class DynamicLoDTimeSystem(ISystem):
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
        super().__init__()
        self._low_lod_delta_time: int = 6
        self._days_per_year: int = days_per_year
        self._high_lod_days_for_year: Set[int] = set()
        self._current_year: int = -1

        assert (
            days_per_year < DAYS_PER_YEAR
        ), f"Days per year is greater than max: {DAYS_PER_YEAR}"
        assert days_per_year > 0, f"Days per year must be greater than 0"

    def process(self, *args, **kwargs):
        current_date = self.world.get_resource(SimDateTime)
        rng = self.world.get_resource(NeighborlyEngine).rng

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


class SocializeSystem(ISystem):
    def __init__(self, interval: int = 12) -> None:
        super().__init__()
        self.interval = interval
        self.time_until_run = interval

    def process(self, *args, **kwargs) -> None:
        for pair in chunk_list(self.world.get_component(GameCharacter), 2):
            character_0 = pair[0][1].gameobject
            character_1 = pair[1][1].gameobject

            # choose an interaction type
            interaction_type = self.world.get_resource(DefaultRNG).choice(
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

            # socialize_event = SocializeEvent(
            #     timestamp=world.get_resource(SimDateTime).to_iso_str(),
            #     character_names=(
            #         str(character_0.get_component(GameCharacter).name),
            #         str(character_1.get_component(GameCharacter).name),
            #     ),
            #     character_ids=(
            #         character_0.id,
            #         character_1.id,
            #     ),
            #     interaction_type=interaction_type,
            # )

            # if character_0.will_handle_event(
            #     socialize_event
            # ) and character_1.will_handle_event(socialize_event):
            #     character_0.handle_event(socialize_event)
            #     character_1.handle_event(socialize_event)


class BuildResidenceSystem(ISystem):
    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build

    def choose_random_archetype(self, engine: NeighborlyEngine) -> Optional[ResidenceArchetype]:
        archetype_choices: List[ResidenceArchetype] = []
        archetype_weights: List[int] = []
        for archetype in ResidenceArchetypeLibrary.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.spawn_multiplier)

        if archetype_choices:
            # Choose an archetype at random
            archetype: ResidenceArchetype = engine.rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype

        return None

    def process(self, *args, **kwargs) -> None:
        """Build a new residence when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)
        event_log = self.world.get_resource(LifeEventLog)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(land_grid.get_vacancies())

        archetype = self.choose_random_archetype(engine)

        if archetype is None:
            return None

        # Construct a random residence archetype
        residence = self.world.spawn_archetype(archetype)

        if residence is None:
            return

        # Reserve the space
        land_grid.reserve_space(lot, residence.id)

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))

        event_log.record_event(
            LifeEvent(
                "NewResidenceBuilt",
                date.to_iso_str(),
                roles=[EventRole("Residence", residence.id)]
            )
        )


class BuildBusinessSystem(ISystem):
    __slots__ = "chance_of_build"

    def __init__(self, chance_of_build: float = 0.5) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build

    def choose_random_eligible_business(self, engine: NeighborlyEngine) -> Optional[BusinessArchetype]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        town = self.world.get_resource(Town)

        archetype_choices: List[BusinessArchetype] = []
        archetype_weights: List[int] = []

        for archetype in BusinessArchetypeLibrary.get_all():
            if (
                archetype.instances < archetype.max_instances
                and town.population >= archetype.min_population
            ):
                archetype_choices.append(archetype)
                archetype_weights.append(archetype.spawn_multiplier)

        if archetype_choices:
            # Choose an archetype at random
            archetype: BusinessArchetype = engine.rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype

        return None

    def process(self, *args, **kwargs) -> None:
        """Build a new business when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        engine = self.world.get_resource(NeighborlyEngine)
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        # Return early if there is nowhere to build
        if not land_grid.has_vacancy():
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(land_grid.get_vacancies())

        # Pick random eligible business archetype
        archetype = self.choose_random_eligible_business(engine)

        if archetype is None:
            return

        # Build a random business archetype
        business = self.world.spawn_archetype(archetype)

        # Reserve the space
        land_grid.reserve_space(lot, business.id)

        # Set the position of the residence
        business.get_component(Position2D).x = lot[0]
        business.get_component(Position2D).y = lot[1]

        event_log.record_event(
            LifeEvent(
                "NewBusinessBuilt",
                date.to_iso_str(),
                roles=[EventRole("Business", business.id)]
            )
        )


class SpawnResidentSystem(ISystem):
    """Adds new characters to the simulation"""

    __slots__ = "chance_spawn", "chance_married", "max_kids"

    def __init__(
        self,
        chance_spawn: float = 0.5,
        chance_married: float = 0.5,
        max_kids: int = 3,
    ) -> None:
        super().__init__()
        self.chance_spawn: float = chance_spawn
        self.chance_married: float = chance_married
        self.max_kids: int = max_kids

    def choose_random_character_archetype(self, engine: NeighborlyEngine):
        archetype_choices: List[CharacterArchetype] = []
        archetype_weights: List[int] = []
        for archetype in CharacterArchetypeLibrary.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.spawn_multiplier)

        if archetype_choices:
            # Choose an archetype at random
            archetype: CharacterArchetype = engine.rng.choices(
                population=archetype_choices, weights=archetype_weights, k=1
            )[0]

            return archetype
        else:
            return None

    def process(self, *args, **kwargs) -> None:
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)
        date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)

        for _, residence in self.world.get_component(Residence):
            # Skip occupied residences
            if not residence.is_vacant():
                continue

            # Return early if the random-roll is not sufficient
            if engine.rng.random() > self.chance_spawn:
                return

            archetype = self.choose_random_character_archetype(engine)

            if archetype is None:
                return

            # Create a new character
            character = generate_young_adult_character(self.world, engine, archetype)
            residence.add_resident(character.id)
            residence.add_owner(character.id)
            town.population += 1

            move_residence(character.get_component(GameCharacter), residence)
            move_to_location(
                self.world,
                character.get_component(GameCharacter),
                residence.gameobject.get_component(Location),
            )

            spouse: Optional[GameObject] = None
            # Potentially generate a spouse for this character
            if engine.rng.random() < self.chance_married:
                spouse = generate_young_adult_character(self.world, engine, archetype)
                spouse.get_component(GameCharacter).name.surname = character.get_component(GameCharacter).name.surname
                residence.add_resident(spouse.id)
                residence.add_owner(spouse.id)
                town.population += 1

                move_residence(spouse.get_component(GameCharacter), residence)
                move_to_location(
                    self.world,
                    spouse.get_component(GameCharacter),
                    residence.gameobject.get_component(Location),
                )

                character.add_component(
                    Married(
                        partner_id=spouse.id,
                        partner_name=str(spouse.get_component(GameCharacter).name)
                    )
                )

                spouse.add_component(
                    Married(
                        partner_id=character.id,
                        partner_name=str(character.get_component(GameCharacter).name)
                    )
                )

                # character to spouse
                rel_graph.add_relationship(Relationship(
                    character.id,
                    spouse.id,
                    base_friendship=30,
                    base_romance=50,
                    tags=RelationshipTag.Friend | RelationshipTag.Spouse | RelationshipTag.SignificantOther
                ))

                # spouse to character
                rel_graph.add_relationship(Relationship(
                    spouse.id,
                    character.id,
                    base_friendship=30,
                    base_romance=50,
                    tags=RelationshipTag.Friend | RelationshipTag.Spouse | RelationshipTag.SignificantOther
                ))

            # Note: Characters can spawn as single parents with kids
            num_kids = engine.rng.randint(0, self.max_kids)
            children: List[GameObject] = []
            for _ in range(num_kids):
                child = generate_child_character(self.world, engine, archetype)
                child.get_component(GameCharacter).name.surname = character.get_component(GameCharacter).name.surname
                town.population += 1

                move_residence(child.get_component(GameCharacter), residence)
                move_to_location(
                    self.world,
                    child.get_component(GameCharacter),
                    residence.gameobject.get_component(Location),
                )

                # Add child as resident
                residence.add_resident(child.id)
                children.append(child)

                # child to character
                rel_graph.add_relationship(Relationship(
                    child.id,
                    character.id,
                    base_friendship=20,
                    tags=RelationshipTag.Parent
                ))

                # character to child
                rel_graph.add_relationship(Relationship(
                    character.id,
                    child.id,
                    base_friendship=20,
                    tags=RelationshipTag.Child
                ))

                if spouse:
                    # child to spouse
                    rel_graph.add_relationship(Relationship(
                        child.id,
                        spouse.id,
                        base_friendship=20,
                        tags=RelationshipTag.Parent
                    ))

                    # spouse to child
                    rel_graph.add_relationship(Relationship(
                        spouse.id,
                        child.id,
                        base_friendship=20,
                        tags=RelationshipTag.Child
                    ))

                for sibling in children:
                    # child to sibling
                    rel_graph.add_relationship(Relationship(
                        child.id,
                        sibling.id,
                        base_friendship=20,
                        tags=RelationshipTag.Sibling
                    ))

                    # sibling to child
                    rel_graph.add_relationship(Relationship(
                        sibling.id,
                        child.id,
                        base_friendship=20,
                        tags=RelationshipTag.Sibling
                    ))

            # Record a life event
            event_logger.record_event(
                LifeEvent(
                    name="MoveIntoTown",
                    timestamp=date.to_iso_str(),
                    roles=[
                        EventRole("resident", r.id)
                        for r in [character, spouse, *children] if r is not None
                    ]
                )
            )


class BusinessSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        time = self.world.get_resource(SimDateTime)
        rng = self.world.get_resource(NeighborlyEngine).rng
        for _, business in self.world.get_component(Business):
            if business.status == BusinessStatus.OpenForBusiness:
                # Increment the age of the business
                business.increment_years_in_business(time.delta_time / HOURS_PER_YEAR)

                # Check if this business is going to close
                if rng.random() < 0.3:
                    # Go Out of business
                    business.set_business_status(BusinessStatus.ClosedForBusiness)
                    business.owner = None
                    for employee in business.get_employees():
                        business.remove_employee(employee)
                        self.world.get_gameobject(employee).remove_component(Occupation)


class CharacterAgingSystem(ISystem):

    def process(self, *args, **kwargs) -> None:
        """Handles updating the ages of characters"""

        date_time = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for _, character in self.world.get_component(GameCharacter):
            if character.gameobject.has_component(Deceased):
                continue

            character.age += float(date_time.delta_time) / HOURS_PER_YEAR

            if (
                character.gameobject.has_component(Child)
                and character.age >= character.character_def.life_stages["teen"]
            ):
                character.gameobject.remove_component(Child)
                character.gameobject.add_component(Teen())

                # event = BecomeAdolescentEvent(
                #     timestamp=date_time.to_iso_str(),
                #     character_id=character.gameobject.id,
                #     character_name=str(character.name),
                # )
                # character.gameobject.handle_event(event)

            elif (
                character.gameobject.has_component(Teen)
                and character.age
                >= character.character_def.life_stages["young_adult"]
            ):
                character.gameobject.remove_component(Teen)
                character.gameobject.add_component(YoungAdult())
                character.gameobject.add_component(Adult())

                # event = BecomeYoungAdultEvent(
                #     timestamp=date_time.to_iso_str(),
                #     character_id=character.gameobject.id,
                #     character_name=str(character.name),
                # )
                # character.gameobject.handle_event(event)

            elif (
                character.gameobject.has_component(YoungAdult)
                and character.age >= character.character_def.life_stages["adult"]
            ):
                character.gameobject.remove_component(YoungAdult)

                # event = BecomeAdultEvent(
                #     timestamp=date_time.to_iso_str(),
                #     character_id=character.gameobject.id,
                #     character_name=str(character.name),
                # )
                # character.gameobject.handle_event(event)

            elif (
                character.gameobject.has_component(Adult)
                and character.age >= character.character_def.life_stages["elder"]
            ):
                character.gameobject.add_component(Elder())

                # event = BecomeElderEvent(
                #     timestamp=date_time.to_iso_str(),
                #     character_id=character.gameobject.id,
                #     character_name=str(character.name),
                # )
                # character.gameobject.handle_event(event)

            if (
                character.age >= character.character_def.lifespan
                and engine.rng.random() < 0.8
            ):
                print(f"{str(character.name)} has died")
                # character.gameobject.handle_event(
                #     DeathEvent(
                #         timestamp=date_time.to_iso_str(),
                #         character_name=str(character.name),
                #         character_id=character.gameobject.id,
                #     )
                # )
                self.world.delete_gameobject(character.gameobject.id)
