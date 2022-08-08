from __future__ import annotations

import itertools
import logging
from typing import List, Optional, Set, cast

from neighborly.builtin.helpers import (
    generate_child_character,
    generate_young_adult_character,
    get_locations,
    move_residence,
    move_to_location,
)
from neighborly.builtin.statuses import (
    Adult,
    BusinessOwner,
    Child,
    Dating,
    Deceased,
    Elder,
    InRelationship,
    InTheWorkforce,
    Married,
    Pregnant,
    Teen,
    Unemployed,
    YoungAdult,
)
from neighborly.core.business import (
    Business,
    BusinessArchetype,
    BusinessArchetypeLibrary,
    BusinessStatus,
    Occupation,
    OccupationTypeLibrary,
)
from neighborly.core.character import (
    CharacterArchetype,
    CharacterArchetypeLibrary,
    CharacterName,
    GameCharacter,
)
from neighborly.core.ecs import GameObject, ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventRole, LifeEvent, LifeEventLog
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipTag,
)
from neighborly.core.residence import (
    Residence,
    ResidenceArchetype,
    ResidenceArchetypeLibrary,
)
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import Routine
from neighborly.core.time import DAYS_PER_YEAR, HOURS_PER_YEAR, SimDateTime, TimeDelta
from neighborly.core.town import LandGrid, Town

logger = logging.getLogger(__name__)


class RoutineSystem(ISystem):
    """
    Moves characters based on their Routine component
    characters with routines move to positions
    """

    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for _, (character, routine) in self.world.get_components(
            GameCharacter, Routine
        ):
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
        assert days_per_year > 0, "Days per year must be greater than 0"

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


class FindBusinessOwnerSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1][0], self.world.get_components(GameCharacter, Unemployed))
        )

        engine = self.world.get_resource(NeighborlyEngine)
        event_log = self.world.get_resource(LifeEventLog)
        date = self.world.get_resource(SimDateTime)

        for _, business in self.world.get_component(Business):
            if not business.needs_owner():
                continue

            if len(unemployed_characters) == 0:
                break

            character = engine.rng.choice(unemployed_characters)
            character.gameobject.add_component(
                BusinessOwner(business.gameobject.id, business.name)
            )
            character.gameobject.remove_component(Unemployed)
            character.gameobject.add_component(
                Occupation(
                    OccupationTypeLibrary.get(business.owner_type),
                    business.gameobject.id,
                )
            )
            business.owner = character.gameobject.id
            unemployed_characters.remove(character)

            event_log.record_event(
                LifeEvent(
                    name="BecameBusinessOwner",
                    timestamp=date.to_iso_str(),
                    roles=[
                        EventRole("Business", business.gameobject.id),
                        EventRole("Owner", character.gameobject.id),
                    ],
                    position=business.owner_type,
                )
            )


class UnemploymentSystem(ISystem):
    """
    Handles updating the amount of time that a character
    has been unemployed. If a character has been unemployed
    for longer than a specified amount of time, they will
    depart from the simulation.

    Attributes
    ----------
    days_to_departure: int
        The number of days a character is allowed to be
        unemployed before they choose to depart from
        the simulation
    """

    __slots__ = "days_to_departure"

    def __init__(self, days_to_departure: int = 30) -> None:
        super().__init__()
        self.days_to_departure: int = days_to_departure

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        for _, unemployed in self.world.get_component(Unemployed):
            # Convert delta time from hours to days
            unemployed.duration_days += date.delta_time / 24

            # Trigger the DepartAction and cast this character
            # as the departee
            if unemployed.duration_days >= self.days_to_departure:
                pass  # TODO: Add DepartAction constructor and execute


class RelationshipStatusSystem(ISystem):
    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)

        for _, marriage in self.world.get_component(Married):
            # Convert delta time from hours to days
            marriage.duration_years += date.delta_time / HOURS_PER_YEAR

        for _, dating in self.world.get_component(Dating):
            # Convert delta time from hours to days
            dating.duration_years += date.delta_time / HOURS_PER_YEAR

        for _, relationship in self.world.get_component(InRelationship):
            # Convert delta time from hours to days
            relationship.duration_years += date.delta_time / HOURS_PER_YEAR


class FindEmployeesSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        unemployed_characters: List[GameCharacter] = list(
            map(lambda x: x[1][0], self.world.get_components(GameCharacter, Unemployed))
        )

        engine = self.world.get_resource(NeighborlyEngine)
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        for _, business in self.world.get_component(Business):
            open_positions = business.get_open_positions()

            for position in open_positions:
                if len(unemployed_characters) == 0:
                    break
                character = engine.rng.choice(unemployed_characters)
                character.gameobject.remove_component(Unemployed)

                business.add_employee(character.gameobject.id, position)
                character.gameobject.add_component(
                    Occupation(
                        OccupationTypeLibrary.get(position),
                        business.gameobject.id,
                    )
                )
                unemployed_characters.remove(character)

                event_log.record_event(
                    LifeEvent(
                        "HiredAtBusiness",
                        date.to_iso_str(),
                        roles=[
                            EventRole("Business", business.gameobject.id),
                            EventRole("Employee", character.gameobject.id),
                        ],
                        position=position,
                    )
                )


class SocializeSystem(ISystem):
    """
    Every timestep, characters interact with other characters
    at the same location. Characters meeting for the first time
    form relationships based on the compatibility of their
    personal values.
    """

    @staticmethod
    def get_compatibility(character_a: GameObject, character_b: GameObject) -> float:
        """Return value [-1.0, 1.0] representing the compatibility of two characters"""
        return PersonalValues.compatibility(
            character_a.get_component(PersonalValues),
            character_b.get_component(PersonalValues),
        )

    def process(self, *args, **kwargs) -> None:

        engine = self.world.get_resource(NeighborlyEngine)
        rel_graph = self.world.get_resource(RelationshipGraph)

        for _, location in self.world.get_component(Location):
            for character_id, other_character_id in itertools.combinations(
                location.characters_present, 2
            ):
                assert character_id != other_character_id
                character = self.world.get_gameobject(character_id)
                other_character = self.world.get_gameobject(other_character_id)

                if (
                    character.get_component(GameCharacter).age < 3
                    or other_character.get_component(GameCharacter).age < 3
                ):
                    continue

                chance_of_interaction: float = 0.7

                if engine.rng.random() >= chance_of_interaction:
                    continue

                compatibility: float = SocializeSystem.get_compatibility(
                    character, other_character
                )

                # This should be replaced with something more intelligent that allows
                # for other decision-making systems to decide how to interact
                friendship_score = (
                    engine.rng.uniform(0, 2) * (1 + compatibility) - 1.0
                ) * 10
                romance_score = (
                    engine.rng.uniform(0, 2) * (1 + compatibility) - 1.0
                ) * 10

                if not rel_graph.has_connection(character_id, other_character_id):
                    rel_graph.add_relationship(
                        Relationship(
                            character_id,
                            other_character_id,
                            compatibility=compatibility,
                        )
                    )

                rel_graph.get_connection(
                    character_id, other_character_id
                ).increment_romance(romance_score)
                rel_graph.get_connection(
                    character_id, other_character_id
                ).increment_friendship(friendship_score)

                if not rel_graph.has_connection(other_character_id, character_id):
                    rel_graph.add_relationship(
                        Relationship(
                            other_character_id,
                            character_id,
                            compatibility=compatibility,
                        ),
                    )
                rel_graph.get_connection(
                    other_character_id, character_id
                ).increment_romance(romance_score)
                rel_graph.get_connection(
                    other_character_id, character_id
                ).increment_friendship(friendship_score)


class BuildResidenceSystem(ISystem):
    __slots__ = "chance_of_build", "interval", "next_trigger"

    def __init__(
        self, chance_of_build: float = 0.5, interval: TimeDelta = None
    ) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build
        self.interval: TimeDelta = interval if interval else TimeDelta()
        self.next_trigger: SimDateTime = SimDateTime()

    def choose_random_archetype(
        self, engine: NeighborlyEngine
    ) -> Optional[ResidenceArchetype]:
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
        date = self.world.get_resource(SimDateTime)

        if date < self.next_trigger:
            return
        else:
            self.next_trigger = date.copy() + self.interval

        land_grid = self.world.get_resource(LandGrid)
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

        # Reserve the space
        land_grid.reserve_space(lot, residence.id)

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))

        event_log.record_event(
            LifeEvent(
                "NewResidenceBuilt",
                date.to_iso_str(),
                roles=[EventRole("Residence", residence.id)],
            )
        )


class BuildBusinessSystem(ISystem):
    __slots__ = "chance_of_build", "interval", "next_trigger"

    def __init__(
        self, chance_of_build: float = 0.5, interval: TimeDelta = None
    ) -> None:
        super().__init__()
        self.chance_of_build: float = chance_of_build
        self.interval: TimeDelta = interval if interval else TimeDelta()
        self.next_trigger: SimDateTime = SimDateTime()

    def choose_random_eligible_business(
        self, engine: NeighborlyEngine
    ) -> Optional[BusinessArchetype]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        town = self.world.get_resource(Town)
        date = self.world.get_resource(SimDateTime)

        archetype_choices: List[BusinessArchetype] = []
        archetype_weights: List[int] = []

        for archetype in BusinessArchetypeLibrary.get_all():
            if (
                archetype.instances < archetype.max_instances
                and town.population >= archetype.min_population
                and archetype.year_available <= date.year < archetype.year_obsolete
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
        date = self.world.get_resource(SimDateTime)

        if date < self.next_trigger:
            return
        else:
            self.next_trigger = date.copy() + self.interval

        land_grid = self.world.get_resource(LandGrid)
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
                roles=[EventRole("Business", business.id)],
            )
        )


class SpawnResidentSystem(ISystem):
    """Adds new characters to the simulation"""

    __slots__ = "chance_spawn", "chance_married", "max_kids", "interval", "next_trigger"

    def __init__(
        self,
        chance_spawn: float = 0.5,
        chance_married: float = 0.5,
        max_kids: int = 3,
        interval: TimeDelta = None,
    ) -> None:
        super().__init__()
        self.chance_spawn: float = chance_spawn
        self.chance_married: float = chance_married
        self.max_kids: int = max_kids
        self.interval: TimeDelta = interval if interval else TimeDelta()
        self.next_trigger: SimDateTime = SimDateTime()

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

        date = self.world.get_resource(SimDateTime)

        if date < self.next_trigger:
            return
        else:
            self.next_trigger = date.copy() + self.interval

        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)
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
                spouse.get_component(
                    GameCharacter
                ).name.surname = character.get_component(GameCharacter).name.surname
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
                        partner_name=str(spouse.get_component(GameCharacter).name),
                    )
                )

                spouse.add_component(
                    Married(
                        partner_id=character.id,
                        partner_name=str(character.get_component(GameCharacter).name),
                    )
                )

                # character to spouse
                rel_graph.add_relationship(
                    Relationship(
                        character.id,
                        spouse.id,
                        base_friendship=30,
                        base_romance=50,
                        tags=(
                            RelationshipTag.Friend
                            | RelationshipTag.Spouse
                            | RelationshipTag.SignificantOther
                        ),
                    )
                )

                # spouse to character
                rel_graph.add_relationship(
                    Relationship(
                        spouse.id,
                        character.id,
                        base_friendship=30,
                        base_romance=50,
                        tags=(
                            RelationshipTag.Friend
                            | RelationshipTag.Spouse
                            | RelationshipTag.SignificantOther
                        ),
                    )
                )

            # Note: Characters can spawn as single parents with kids
            num_kids = engine.rng.randint(0, self.max_kids)
            children: List[GameObject] = []
            for _ in range(num_kids):
                child = generate_child_character(self.world, engine, archetype)
                child.get_component(
                    GameCharacter
                ).name.surname = character.get_component(GameCharacter).name.surname
                town.population += 1

                move_residence(child.get_component(GameCharacter), residence)
                move_to_location(
                    self.world,
                    child.get_component(GameCharacter),
                    residence.gameobject.get_component(Location),
                )
                children.append(child)

                # child to character
                rel_graph.add_relationship(
                    Relationship(
                        child.id,
                        character.id,
                        base_friendship=20,
                        tags=RelationshipTag.Parent,
                    )
                )

                # character to child
                rel_graph.add_relationship(
                    Relationship(
                        character.id,
                        child.id,
                        base_friendship=20,
                        tags=RelationshipTag.Child,
                    )
                )

                if spouse:
                    # child to spouse
                    rel_graph.add_relationship(
                        Relationship(
                            child.id,
                            spouse.id,
                            base_friendship=20,
                            tags=RelationshipTag.Parent,
                        )
                    )

                    # spouse to child
                    rel_graph.add_relationship(
                        Relationship(
                            spouse.id,
                            child.id,
                            base_friendship=20,
                            tags=RelationshipTag.Child,
                        )
                    )

                for sibling in children:
                    # child to sibling
                    rel_graph.add_relationship(
                        Relationship(
                            child.id,
                            sibling.id,
                            base_friendship=20,
                            tags=RelationshipTag.Sibling,
                        )
                    )

                    # sibling to child
                    rel_graph.add_relationship(
                        Relationship(
                            sibling.id,
                            child.id,
                            base_friendship=20,
                            tags=RelationshipTag.Sibling,
                        )
                    )

            # Record a life event
            event_logger.record_event(
                LifeEvent(
                    name="MoveIntoTown",
                    timestamp=date.to_iso_str(),
                    roles=[
                        EventRole("resident", r.id)
                        for r in [character, spouse, *children]
                        if r is not None
                    ],
                )
            )


class BusinessUpdateSystem(ISystem):
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
                    business.gameobject.archive()

                # Attempt to hire characters for open job positions
                for position in business.get_open_positions():
                    OccupationTypeLibrary.get(position)


class CharacterAgingSystem(ISystem):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles character deaths.

    Notes
    -----
    This system runs every time step
    """

    def process(self, *args, **kwargs) -> None:
        date_time = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)
        event_log = self.world.get_resource(LifeEventLog)

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
                event_log.record_event(
                    LifeEvent(
                        name="BecomeTeen",
                        timestamp=date_time.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(Teen)
                and character.age >= character.character_def.life_stages["young_adult"]
            ):
                character.gameobject.remove_component(Teen)
                character.gameobject.add_component(YoungAdult())
                character.gameobject.add_component(Adult())

                if not character.gameobject.has_component(Occupation):
                    character.gameobject.add_component(Unemployed())

                event_log.record_event(
                    LifeEvent(
                        name="BecomeYoungAdult",
                        timestamp=date_time.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(YoungAdult)
                and character.age >= character.character_def.life_stages["adult"]
            ):
                character.gameobject.remove_component(YoungAdult)
                event_log.record_event(
                    LifeEvent(
                        name="BecomeAdult",
                        timestamp=date_time.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(Adult)
                and not character.gameobject.has_component(Elder)
                and character.age >= character.character_def.life_stages["elder"]
            ):
                character.gameobject.add_component(Elder())
                event_log.record_event(
                    LifeEvent(
                        name="BecomeElder",
                        timestamp=date_time.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    )
                )

            if (
                character.age >= character.character_def.lifespan
                and engine.rng.random() < 0.8
            ):
                character.gameobject.add_component(Deceased())
                event_log.record_event(
                    LifeEvent(
                        name="Death",
                        timestamp=date_time.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    )
                )

                # Archive GameObject instead of removing it
                character.gameobject.archive()
                # self.world.delete_gameobject(character.gameobject.id)


class PregnancySystem(ISystem):
    """
    Pregnancy system is responsible for managing ChildBirth events.
    It checks if the current date is after pregnant characters'
    due dates, and triggers childbirths if it is.
    """

    def process(self, *args, **kwargs):
        current_date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)

        for _, (character, pregnancy) in self.world.get_components(
            GameCharacter, Pregnant
        ):
            if current_date > pregnancy.due_date:
                continue

            baby = self.world.spawn_archetype(character.gameobject.archetype)

            baby.get_component(GameCharacter).age = (
                current_date - pregnancy.due_date
            ).hours / HOURS_PER_YEAR

            baby.get_component(GameCharacter).name = CharacterName(
                baby.get_component(GameCharacter).name.firstname, character.name.surname
            )

            move_to_location(
                self.world,
                baby.get_component(GameCharacter),
                self.world.get_gameobject(character.location).get_component(Location),
            )

            # Birthing parent to child
            rel_graph.add_relationship(
                Relationship(
                    character.gameobject.id,
                    baby.id,
                    tags=RelationshipTag.Child,
                )
            )

            # Child to birthing parent
            rel_graph.add_relationship(
                Relationship(
                    baby.id,
                    character.gameobject.id,
                    tags=RelationshipTag.Parent,
                ),
            )

            # Other parent to child
            rel_graph.add_relationship(
                Relationship(
                    pregnancy.partner_id,
                    baby.id,
                    tags=RelationshipTag.Child,
                )
            )

            # Child to other parent
            rel_graph.add_relationship(
                Relationship(
                    baby.id,
                    pregnancy.partner_id,
                    tags=RelationshipTag.Parent,
                ),
            )

            # Create relationships with children of birthing parent
            for rel in rel_graph.get_all_relationships_with_tags(
                character.gameobject.id, RelationshipTag.Child
            ):
                if rel.target == baby.id:
                    continue
                # Baby to sibling
                rel_graph.add_relationship(
                    Relationship(baby.id, rel.target, tags=RelationshipTag.Sibling)
                )
                # Sibling to baby
                rel_graph.add_relationship(
                    Relationship(rel.target, baby.id, tags=RelationshipTag.Sibling)
                )

            # Create relationships with children of other parent
            for rel in rel_graph.get_all_relationships_with_tags(
                pregnancy.partner_id, RelationshipTag.Child
            ):
                if rel.target == baby.id:
                    continue
                # Baby to sibling
                rel_graph.add_relationship(
                    Relationship(baby.id, rel.target, tags=RelationshipTag.Sibling)
                )
                # Sibling to baby
                rel_graph.add_relationship(
                    Relationship(rel.target, baby.id, tags=RelationshipTag.Sibling)
                )

            # Pregnancy event dates are retconned to be the actual date that the
            # child was due.
            event_logger.record_event(
                LifeEvent(
                    name="ChildBirth",
                    timestamp=pregnancy.due_date.to_iso_str(),
                    roles=[
                        EventRole("Parent", character.gameobject.id),
                        EventRole("Parent", pregnancy.partner_id),
                        EventRole("Child", baby.id),
                    ],
                )
            )

            character.gameobject.remove_component(Pregnant)
            character.gameobject.remove_component(InTheWorkforce)
            character.gameobject.remove_component(Occupation)

            # TODO: Birthing parent should also leave their job
