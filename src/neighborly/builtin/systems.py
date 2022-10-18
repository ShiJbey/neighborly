from __future__ import annotations

import itertools
import logging
import math
from abc import abstractmethod
from typing import List, Optional, Set, Tuple, cast

from neighborly.builtin.components import (
    Active,
    Adult,
    Age,
    CanAge,
    Child,
    CurrentLocation,
    Dating,
    Elder,
    LifeStages,
    LocationAliases,
    Married,
    OpenToPublic,
    Pregnant,
    Teen,
    YoungAdult,
)
from neighborly.builtin.events import depart_event
from neighborly.builtin.helpers import (
    choose_random_character_archetype,
    demolish_building,
    generate_child_character,
    generate_young_adult_character,
    move_residence,
    move_to_location,
)
from neighborly.core.archetypes import (
    BusinessArchetype,
    BusinessArchetypeLibrary,
    ResidenceArchetype,
    ResidenceArchetypeLibrary,
)
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    OccupationTypeLibrary,
    OpenForBusiness,
    PendingOpening,
    Unemployed,
    start_job,
)
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.ecs import GameObject, SystemBase
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent, LifeEventLog, Role
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import (
    Relationship,
    RelationshipGraph,
    RelationshipTag,
)
from neighborly.core.residence import Residence, Resident
from neighborly.core.routine import Routine
from neighborly.core.time import (
    DAYS_PER_YEAR,
    HOURS_PER_DAY,
    HOURS_PER_YEAR,
    SimDateTime,
    TimeDelta,
    Weekday,
)
from neighborly.core.town import LandGrid, Town

logger = logging.getLogger(__name__)


class System(SystemBase):
    """
    System is a more fully-featured System abstraction that
    handles common calculations like calculating the elapsed
    time between calls.
    """

    __slots__ = "_interval", "_last_run", "_elapsed_time", "_next_run"

    def __init__(
        self,
        interval: Optional[TimeDelta] = None,
    ) -> None:
        super().__init__()
        self._last_run: SimDateTime = SimDateTime()
        self._interval: TimeDelta = interval if interval else TimeDelta()
        self._next_run: SimDateTime = SimDateTime() + self._interval
        self._elapsed_time: TimeDelta = TimeDelta()

    @property
    def elapsed_time(self) -> TimeDelta:
        """Returns the amount of simulation time since the last update"""
        return self._elapsed_time

    def process(self, *args, **kwargs) -> None:
        """Handles internal bookkeeping before running the system"""
        date = self.world.get_resource(SimDateTime)

        if date >= self._next_run:
            self._last_run = date.copy()
            self._elapsed_time = date - self._last_run
            self._next_run = date + self._interval
            self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs) -> None:
        raise NotImplementedError


class RoutineSystem(SystemBase):
    """
    GameCharacters with Routine components move to locations designated by their
    routines. If they do not have a routine entry, then they move to a location
    that is open to the public.
    """

    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for _, (character, routine, _) in self.world.get_components(
            GameCharacter, Routine, Active
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)
            location_aliases = character.gameobject.try_component(LocationAliases)

            routine_entry = routine.get_entry(date.weekday, date.hour)

            if (
                routine_entry
                and isinstance(routine_entry.location, str)
                and location_aliases
            ):
                move_to_location(
                    self.world,
                    character.gameobject,
                    location_aliases.aliases[routine_entry.location],
                )

            elif routine_entry:
                move_to_location(
                    self.world, character.gameobject, routine_entry.location
                )

            else:
                potential_locations: List[int] = list(
                    map(
                        lambda res: res[0],
                        self.world.get_components(Location, OpenToPublic),
                    )
                )

                if potential_locations:
                    location = engine.rng.choice(potential_locations)
                    move_to_location(self.world, character.gameobject, location)


class LinearTimeSystem(SystemBase):
    """
    Advances simulation time using a linear time increment

    Attributes
    ----------
    increment: TimeDelta
        How much should time be progressed each simulation step
    """

    __slots__ = "increment"

    def __init__(self, increment: TimeDelta) -> None:
        super().__init__()
        self.increment: TimeDelta = increment

    def process(self, *args, **kwargs) -> None:
        """Advance time"""
        current_date = self.world.get_resource(SimDateTime)
        current_date += self.increment


class DynamicLoDTimeSystem(SystemBase):
    """
    Updates the current date/time in the simulation
    using a variable level-of-detail (LOD) where a subset
    of the days during a year receive more simulation
    ticks.

    Attributes
    ----------
    _low_lod_time_increment: TimeDelta
       The amount to increment time by during low LOD phases
    _high_lod_time_increment: TimeDelta
       The amount to increment time by during high LOD phases
    _days_per_year: int
        How many high LoD days to simulate per year
    _high_lod_days_for_year: Set[int]
        Ordinal dates of days in the current year that will be simulated in higher LOD
    _current_year: int
        The current year in the simulation
    """

    __slots__ = (
        "_low_lod_time_increment",
        "_high_lod_time_increment",
        "days_per_year",
        "_high_lod_days_for_year",
        "_current_year",
    )

    def __init__(
        self,
        days_per_year: int,
        low_lod_time_increment: Optional[TimeDelta] = None,
        high_lod_time_increment: Optional[TimeDelta] = None,
    ) -> None:
        super().__init__()
        self._low_lod_time_increment: TimeDelta = (
            low_lod_time_increment if low_lod_time_increment else TimeDelta(hours=24)
        )
        self._high_lod_time_increment: TimeDelta = (
            high_lod_time_increment if high_lod_time_increment else TimeDelta(hours=6)
        )
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
            current_date += self._high_lod_time_increment
        else:
            # Increment by one whole day (Low LoD)
            current_date += self._low_lod_time_increment


class FindBusinessOwnerSystem(SystemBase):
    def process(self, *args, **kwargs) -> None:
        event_log = self.world.get_resource(LifeEventLog)
        date = self.world.get_resource(SimDateTime)

        for _, (business, _, _) in self.world.get_components(
            Business, PendingOpening, Building
        ):
            business = cast(Business, business)

            if not business.needs_owner():
                # This business is free to hire employees and does not need to hire an
                # owner first
                business.gameobject.add_component(OpenForBusiness())
                business.gameobject.remove_component(PendingOpening)
                continue

            result = OccupationTypeLibrary.get(business.owner_type).fill_role(
                self.world, business
            )

            if result:
                candidate, occupation = result

                start_job(
                    business,
                    candidate.get_component(GameCharacter),
                    occupation,
                    is_owner=True,
                )

                event_log.record_event(
                    LifeEvent(
                        name="BecameBusinessOwner",
                        timestamp=date.to_iso_str(),
                        roles=[
                            Role("Business", business.gameobject.id),
                            Role("Owner", candidate.id),
                        ],
                        position=business.owner_type,
                    )
                )


class UnemploymentSystem(SystemBase):
    """
    Handles updating the amount of time that a entity
    has been unemployed. If a entity has been unemployed
    for longer than a specified amount of time, they will
    depart from the simulation.

    Attributes
    ----------
    days_to_departure: int
        The number of days a entity is allowed to be
        unemployed before they choose to depart from
        the simulation
    """

    __slots__ = "days_to_departure"

    def __init__(self, days_to_departure: int = 30) -> None:
        super().__init__()
        self.days_to_departure: int = days_to_departure

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        for gid, (unemployed, _) in self.world.get_components(Unemployed, Active):
            # Convert delta time from hours to days
            unemployed.duration_days += date.delta_time / 24

            # Trigger the DepartAction and cast this entity
            # as the departee
            if unemployed.duration_days >= self.days_to_departure:
                spouses = rel_graph.get_all_relationships_with_tags(
                    gid, RelationshipTag.Spouse
                )

                # Do not depart if one or more of the entity's spouses has a job
                if any(
                    [
                        self.world.get_gameobject(rel.target).has_component(Occupation)
                        for rel in spouses
                    ]
                ):
                    continue

                else:
                    depart = depart_event()

                    residence = self.world.get_gameobject(
                        unemployed.gameobject.get_component(Resident).residence
                    ).get_component(Residence)

                    depart.try_execute_event(
                        self.world, Character=unemployed.gameobject
                    )

                    # Have all spouses depart
                    # Allows for polygamy
                    spouses = rel_graph.get_all_relationships_with_tags(
                        unemployed.gameobject.id, RelationshipTag.Spouse
                    )
                    for rel in spouses:
                        spouse = self.world.get_gameobject(rel.target)
                        depart.try_execute_event(self.world, Character=spouse)

                    # Have all children living in the same house depart
                    children = rel_graph.get_all_relationships_with_tags(
                        unemployed.gameobject.id, RelationshipTag.Child
                    )
                    for rel in children:
                        child = self.world.get_gameobject(rel.target)
                        if (
                            child.id in residence.residents
                            and child.id not in residence.owners
                        ):
                            depart.try_execute_event(self.world, Character=child)


class RelationshipStatusSystem(SystemBase):
    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)

        for _, (marriage, _) in self.world.get_components(Married, Active):
            # Convert delta time from hours to days
            marriage = cast(Married, marriage)
            marriage.duration_years += date.delta_time / HOURS_PER_YEAR

        for _, (dating, _) in self.world.get_components(Dating, Active):
            # Convert delta time from hours to days
            dating = cast(Dating, dating)
            dating.duration_years += date.delta_time / HOURS_PER_YEAR


class FindEmployeesSystem(SystemBase):
    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        for _, (business, _, _) in self.world.get_components(
            Business, OpenForBusiness, Building
        ):
            open_positions = business.get_open_positions()

            for position in open_positions:
                result = OccupationTypeLibrary.get(position).fill_role(
                    self.world, business
                )

                if result:
                    candidate, occupation = result

                    start_job(
                        business, candidate.get_component(GameCharacter), occupation
                    )

                    event_log.record_event(
                        LifeEvent(
                            "HiredAtBusiness",
                            date.to_iso_str(),
                            roles=[
                                Role("Business", business.gameobject.id),
                                Role("Employee", candidate.id),
                            ],
                            position=position,
                        )
                    )


class SocializeSystem(SystemBase):
    """
    Every timestep, characters interact with other characters
    at the same location. Characters meeting for the first time
    form relationships based on the compatibility of their
    personal values.
    """

    __slots__ = "chance_of_interaction"

    def __init__(self, chance_of_interaction: float = 0.7) -> None:
        super().__init__()
        self.chance_of_interaction: float = chance_of_interaction

    @staticmethod
    def get_compatibility(character_a: GameObject, character_b: GameObject) -> float:
        """Return value [-1.0, 1.0] representing the compatibility of two characters"""
        return PersonalValues.compatibility(
            character_a.get_component(PersonalValues),
            character_b.get_component(PersonalValues),
        )

    @staticmethod
    def job_level_difference_romance_debuff(
        character_a: GameObject, character_b: GameObject
    ) -> float:
        """
        This makes people with job-level differences less likely to develop romantic feelings
        for one another (missing source)
        """
        character_a_job = character_a.try_component(Occupation)
        character_b_job = character_b.try_component(Occupation)
        character_a_level = character_a_job.level if character_a_job else 0
        character_b_level = character_b_job.level if character_b_job else 0

        return max(
            0.05, 1 - (abs(math.sqrt(character_a_level) - math.sqrt(character_b_level)))
        )

    @staticmethod
    def age_difference_romance_debuff(
        character_a: GameObject, character_b: GameObject
    ) -> float:
        """How does age difference affect developing romantic feelings
        People with larger age gaps are less likely to develop romantic feelings
        (missing source)
        """
        character_a_age = character_a.get_component(GameCharacter).age
        character_b_age = character_b.get_component(GameCharacter).age
        return max(
            0.01,
            1 - (abs(math.sqrt(character_a_age) - math.sqrt(character_b_age)) / 1.5),
        )

    @staticmethod
    def age_difference_friendship_debuff(
        character_a: GameObject, character_b: GameObject
    ) -> float:
        """
        This makes people with large age differences more indifferent about potentially
        becoming friends or enemies
        """
        character_a_age = character_a.get_component(GameCharacter).age
        character_b_age = character_b.get_component(GameCharacter).age
        return max(
            0.05,
            1 - (abs(math.sqrt(character_a_age) - math.sqrt(character_b_age)) / 4.5),
        )

    @staticmethod
    def job_level_difference_friendship_debuff(
        character_a: GameObject, character_b: GameObject
    ) -> float:
        """This makes people with job-level differences more indifferent about potentially
        becoming friends or enemies
        """

        character_a_job = character_a.try_component(Occupation)
        character_b_job = character_b.try_component(Occupation)
        character_a_level = character_a_job.level if character_a_job else 0
        character_b_level = character_b_job.level if character_b_job else 0

        return max(
            0.05, 1 - (abs(math.sqrt(character_a_level) - math.sqrt(character_b_level)))
        )

    def process(self, *args, **kwargs) -> None:

        engine = self.world.get_resource(NeighborlyEngine)
        rel_graph = self.world.get_resource(RelationshipGraph)

        for _, location in self.world.get_component(Location):
            for character_id, other_character_id in itertools.combinations(
                location.entities, 2
            ):
                assert character_id != other_character_id
                character = self.world.get_gameobject(character_id).get_component(
                    GameCharacter
                )
                other_character = self.world.get_gameobject(
                    other_character_id
                ).get_component(GameCharacter)

                if character.age < 3 or other_character.age < 3:
                    continue

                if engine.rng.random() >= self.chance_of_interaction:
                    continue

                if not rel_graph.has_connection(
                    character.gameobject.id, other_character.gameobject.id
                ):
                    rel_graph.add_relationship(
                        Relationship(
                            character.gameobject.id, other_character.gameobject.id
                        )
                    )

                if not rel_graph.has_connection(
                    other_character.gameobject.id, character.gameobject.id
                ):
                    rel_graph.add_relationship(
                        Relationship(
                            other_character.gameobject.id, character.gameobject.id
                        )
                    )

                compatibility: float = SocializeSystem.get_compatibility(
                    character.gameobject, other_character.gameobject
                )

                # This should be replaced with something more intelligent that allows
                # for other decision-making systems to decide how to interact
                friendship_score = engine.rng.randrange(-1, 1)
                if (friendship_score < 0 and compatibility < 0) or (
                    friendship_score > 0 and compatibility > 0
                ):
                    # negative social interaction should be buffed by negative compatibility
                    friendship_score *= 1 + abs(compatibility)
                else:
                    # debuff the score if compatibility and friendship score signs differ
                    friendship_score *= 1 - abs(compatibility)

                friendship_score += (
                    SocializeSystem.job_level_difference_friendship_debuff(
                        character.gameobject, other_character.gameobject
                    )
                )
                friendship_score += SocializeSystem.age_difference_friendship_debuff(
                    character.gameobject, other_character.gameobject
                )

                if (
                    character.age < character.character_def.life_stages["teen"]
                    or other_character.age
                    < other_character.character_def.life_stages["teen"]
                ):
                    romance_score = 0.0
                elif (
                    rel_graph.get_connection(character_id, other_character_id).has_tags(
                        RelationshipTag.Parent
                    )
                    or rel_graph.get_connection(
                        other_character_id, character_id
                    ).has_tags(RelationshipTag.Parent)
                    or rel_graph.get_connection(
                        character_id, other_character_id
                    ).has_tags(RelationshipTag.Sibling)
                    or rel_graph.get_connection(
                        other_character_id, character_id
                    ).has_tags(RelationshipTag.Sibling)
                ):
                    romance_score = 0.0
                else:
                    romance_score = engine.rng.random() * compatibility
                    romance_score += (
                        SocializeSystem.job_level_difference_romance_debuff(
                            character.gameobject, other_character.gameobject
                        )
                    )
                    romance_score += SocializeSystem.age_difference_romance_debuff(
                        character.gameobject, other_character.gameobject
                    )

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


class BuildHousingSystem(System):
    """
    Builds housing archetypes on unoccupied spaces on the land grid

    Attributes
    ----------
    chance_of_build: float
        Probability that a new residential building will be built
        if there is space available
    """

    __slots__ = "chance_of_build"

    def __init__(
        self, chance_of_build: float = 0.5, interval: Optional[TimeDelta] = None
    ) -> None:
        super().__init__(interval=interval)
        self.chance_of_build: float = chance_of_build

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

    def run(self, *args, **kwargs) -> None:
        """Build a new residence when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        engine = self.world.get_resource(NeighborlyEngine)

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
        land_grid[lot] = residence.id

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))
        residence.add_component(Building(building_type="residential"))
        logger.debug(
            f"Built residential building at {str(residence.get_component(Position2D))}"
        )


class BuildBusinessSystem(System):
    """
    Build a new business building at a random free space on the land grid.

    Attributes
    ----------
    chance_of_build: float
        The probability that a new business may be built this timestep
    """

    __slots__ = "chance_of_build"

    def __init__(
        self, chance_of_build: float = 0.5, interval: Optional[TimeDelta] = None
    ) -> None:
        super().__init__(interval)
        self.chance_of_build: float = chance_of_build

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

    def run(self, *args, **kwargs) -> None:
        """Build a new business when there is space"""
        land_grid = self.world.get_resource(LandGrid)
        engine = self.world.get_resource(NeighborlyEngine)

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
        land_grid[lot] = business.id

        # Set the position of the residence
        business.get_component(Position2D).x = lot[0]
        business.get_component(Position2D).y = lot[1]

        # Give the business a building
        business.add_component(Building(building_type="commercial"))
        business.add_component(PendingOpening())
        logger.debug(
            f"Built commercial building at {str(business.get_component(Position2D))}"
        )


class SpawnResidentSystem(System):
    """Adds new characters to the simulation"""

    __slots__ = "chance_spawn"

    def __init__(
        self,
        chance_spawn: float = 0.5,
        interval: Optional[TimeDelta] = None,
    ) -> None:
        super().__init__(interval=interval)
        self.chance_spawn: float = chance_spawn

    def run(self, *args, **kwargs) -> None:

        date = self.world.get_resource(SimDateTime)
        town = self.world.get_resource(Town)
        engine = self.world.get_resource(NeighborlyEngine)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)

        for _, (residence, _) in self.world.get_components(Residence, Building):
            # Skip occupied residences
            if not residence.is_vacant():
                continue

            # Return early if the random-roll is not sufficient
            if engine.rng.random() > self.chance_spawn:
                return

            archetype = choose_random_character_archetype(engine)

            # There are no archetypes available to spawn
            if archetype is None:
                return

            # Create a new entity using the archetype
            character = generate_young_adult_character(self.world, engine, archetype)

            character.add_component(Active())
            residence.add_owner(character.id)
            town.increment_population()

            move_residence(character.get_component(GameCharacter), residence)
            move_to_location(self.world, character, residence.gameobject.id)

            spouse: Optional[GameObject] = None
            # Potentially generate a spouse for this entity
            if engine.rng.random() < archetype.chance_spawn_with_spouse:
                spouse = generate_young_adult_character(self.world, engine, archetype)
                spouse.get_component(
                    GameCharacter
                ).name.surname = character.get_component(GameCharacter).name.surname
                character.add_component(Active())
                residence.add_owner(spouse.id)
                town.increment_population()

                move_residence(spouse.get_component(GameCharacter), residence)
                move_to_location(
                    self.world,
                    spouse,
                    residence.gameobject.id,
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

                # entity to spouse
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

                # spouse to entity
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
            num_kids = engine.rng.randint(0, archetype.max_children_at_spawn)
            children: List[GameObject] = []
            for _ in range(num_kids):
                child = generate_child_character(self.world, engine, archetype)
                character.add_component(Active())
                child.get_component(
                    GameCharacter
                ).name.surname = character.get_component(GameCharacter).name.surname
                town.increment_population()

                move_residence(child.get_component(GameCharacter), residence)
                move_to_location(
                    self.world,
                    child.get_component(GameCharacter),
                    residence.gameobject.get_component(Location),
                )
                children.append(child)

                # child to entity
                rel_graph.add_relationship(
                    Relationship(
                        child.id,
                        character.id,
                        base_friendship=20,
                        tags=RelationshipTag.Parent,
                    )
                )

                # entity to child
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
                        Role("resident", r.id)
                        for r in [character, spouse, *children]
                        if r is not None
                    ],
                )
            )


class BusinessUpdateSystem(System):
    @staticmethod
    def is_within_operating_hours(current_hour: int, hours: Tuple[int, int]) -> bool:
        """Return True if the given hour is within the hours 24-hour time interval"""
        start, end = hours
        if start <= end:
            return start <= current_hour <= end
        else:
            # The time interval overflows to the next day
            return current_hour <= end or current_hour >= start

    def run(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        rng = self.world.get_resource(NeighborlyEngine).rng

        for _, (business, _, _) in self.world.get_components(
            Business, Building, OpenForBusiness
        ):
            # Check if this business is going to close
            if rng.random() < 0.3:
                # Go Out of business
                business.gameobject.add_component(ClosedForBusiness)
                business.gameobject.remove_component(OpenForBusiness)
                if business.gameobject.has_component(OpenToPublic):
                    business.gameobject.remove_component(OpenToPublic)

            # Open/Close based on operating hours
            if business.operating_hours.get(Weekday[date.weekday_str]) is not None:
                business.gameobject.add_component(OpenToPublic())


class CharacterAgingSystem(System):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles entity deaths.

    Notes
    -----
    This system runs every time step
    """

    def run(self, *args, **kwargs) -> None:
        current_date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        age_increment = float(self.elapsed_time.total_hours) / HOURS_PER_YEAR

        for _, (character, age, life_stages, _, _) in self.world.get_components(
            GameCharacter, Age, LifeStages, CanAge, Active
        ):
            age.age += age_increment

            if (
                character.gameobject.has_component(Child)
                and character.age >= life_stages.stages["teen"]
            ):
                character.gameobject.add_component(Teen())
                character.gameobject.remove_component(Child)
                event_log.record_event(
                    LifeEvent(
                        name="BecomeTeen",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            Role("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(Teen)
                and character.age >= life_stages.stages["young_adult"]
            ):
                character.gameobject.remove_component(Teen)
                character.gameobject.add_component(YoungAdult())
                character.gameobject.add_component(Adult())
                character.gameobject.add_component(InTheWorkforce())

                if not character.gameobject.has_component(Occupation):
                    character.gameobject.add_component(Unemployed())

                event_log.record_event(
                    LifeEvent(
                        name="BecomeYoungAdult",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            Role("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(YoungAdult)
                and character.age >= life_stages.stages["adult"]
            ):
                character.gameobject.remove_component(YoungAdult)
                event_log.record_event(
                    LifeEvent(
                        name="BecomeAdult",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            Role("Character", character.gameobject.id),
                        ],
                    )
                )

            elif (
                character.gameobject.has_component(Adult)
                and not character.gameobject.has_component(Elder)
                and character.age >= life_stages.stages["elder"]
            ):
                character.gameobject.add_component(Elder())
                event_log.record_event(
                    LifeEvent(
                        name="BecomeElder",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            Role("Character", character.gameobject.id),
                        ],
                    )
                )


class PregnancySystem(SystemBase):
    """
    Pregnancy system is responsible for managing ChildBirth events.
    It checks if the current date is after a pregnant entity's
    due date, and triggers a childbirth if it is.
    """

    def process(self, *args, **kwargs):
        current_date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)

        for _, (character, pregnancy, _) in self.world.get_components(
            GameCharacter, Pregnant, Active
        ):

            # Cast for the type-checker
            character = cast(GameCharacter, character)
            pregnancy = cast(Pregnant, pregnancy)

            if current_date >= pregnancy.due_date:
                continue

            assert character.gameobject.archetype is not None

            baby = self.world.spawn_archetype(character.gameobject.archetype)

            baby.get_component(GameCharacter).age = (
                current_date - pregnancy.due_date
            ).hours / HOURS_PER_YEAR

            baby.get_component(GameCharacter).name = CharacterName(
                baby.get_component(GameCharacter).name.firstname, character.name.surname
            )

            if character.gameobject.has_component(CurrentLocation):
                current_location = character.gameobject.get_component(CurrentLocation)
                move_to_location(
                    self.world,
                    baby.get_component(GameCharacter),
                    self.world.get_gameobject(current_location.location).get_component(
                        Location
                    ),
                )

                character.gameobject.add_component(LocationAliases())

                move_residence(
                    baby.get_component(GameCharacter),
                    self.world.get_gameobject(
                        character.gameobject.get_component(Resident).residence
                    ).get_component(Residence),
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
                        Role("Parent", character.gameobject.id),
                        Role("Parent", pregnancy.partner_id),
                        Role("Child", baby.id),
                    ],
                )
            )

            character.gameobject.remove_component(Pregnant)
            # entity.gameobject.remove_component(InTheWorkforce)

            # if entity.gameobject.has_component(Occupation):
            #     entity.gameobject.remove_component(Occupation)

            # TODO: Birthing parent should also leave their job


class PendingOpeningSystem(System):
    """
    Tracks how long a business has been present in the town, but not
    officially open. If a business stays in the pending state for longer
    than a given amount of time, it will go out of business

    Attributes
    ----------
    days_before_demolishing: int
        The number of days that a business can be in the pending state before it is
        demolished.
    """

    __slots__ = "days_before_demolishing"

    def __init__(self, days_before_demolishing: int = 30) -> None:
        super().__init__()
        self.days_before_demolishing: int = days_before_demolishing

    def run(self, *args, **kwargs):
        for gid, pending_opening in self.world.get_component(PendingOpening):
            pending_opening.duration += self.elapsed_time.total_hours / HOURS_PER_DAY

            if pending_opening.duration >= self.days_before_demolishing:
                pending_opening.gameobject.remove_component(PendingOpening)
                pending_opening.gameobject.add_component(ClosedForBusiness())


class OpenForBusinessSystem(System):
    """
    Tracks how long a business has been active
    """

    def run(self, *args, **kwargs):
        for _, (open_for_business, age) in self.world.get_components(
            OpenForBusiness, Age
        ):
            # Increment the amount of time that the business has been open
            age.age += self.elapsed_time.total_hours / HOURS_PER_DAY


class ClosedForBusinessSystem(SystemBase):
    """
    This system is responsible for removing Businesses from play that are marked as
    ClosedForBusiness. It removes the building from play, keeps the GameObject for
    sifting purposes, and displaces the characters within the building.
    """

    def process(self, *args, **kwargs):
        for _, out_of_business in self.world.get_component(ClosedForBusiness):
            demolish_building(out_of_business.gameobject)
