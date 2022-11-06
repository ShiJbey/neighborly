from __future__ import annotations

import itertools
import logging
from typing import List, Optional, Protocol, Set, Tuple, cast

from neighborly.builtin.components import (
    Active,
    Adult,
    Age,
    CanAge,
    Child,
    CurrentLocation,
    Deceased,
    Departed,
    Elder,
    LifeStages,
    LocationAliases,
    Name,
    OpenToPublic,
    Pregnant,
    Retired,
    Teen,
    Vacant,
    YoungAdult,
)
from neighborly.builtin.events import depart_event
from neighborly.builtin.helpers import (
    add_residence_owner,
    choose_random_character_archetype,
    demolish_building,
    generate_child,
    layoff_employee,
    move_out_of_residence,
    move_residence,
    move_to_location,
    remove_residence_owner,
)
from neighborly.core.archetypes import (
    BusinessArchetypes,
    IBusinessArchetype,
    IResidenceArchetype,
    ResidenceArchetypes,
)
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    OccupationTypes,
    OpenForBusiness,
    PendingOpening,
    Unemployed,
    end_job,
    start_job,
)
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.ecs import GameObject, ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEvent, LifeEventLog, Role
from neighborly.core.location import Location
from neighborly.core.personal_values import PersonalValues
from neighborly.core.position import Position2D
from neighborly.core.relationship import Relationship, RelationshipGraph
from neighborly.core.residence import Residence, Resident
from neighborly.core.routine import Routine
from neighborly.core.system import System
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


class RoutineSystem(ISystem):
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


class LinearTimeSystem(ISystem):
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
        current_date.increment(hours=self.increment.total_hours)


class DynamicLoDTimeSystem(ISystem):
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


class FindBusinessOwnerSystem(ISystem):
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

            result = OccupationTypes.get(business.owner_type).fill_role(
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


class UnemploymentSystem(ISystem):
    """
    Handles updating the amount of time that an entity
    has been unemployed. If an entity has been unemployed
    for longer than a specified amount of time, they will
    depart from the simulation.

    Attributes
    ----------
    days_to_departure: int
        The number of days an entity is allowed to be
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
                spouses = rel_graph.get_all_relationships_with_tags(gid, "Spouse")

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
                        unemployed.gameobject.id, "Spouse"
                    )
                    for rel in spouses:
                        spouse = self.world.get_gameobject(rel.target)
                        depart.try_execute_event(self.world, Character=spouse)

                    # Have all children living in the same house depart
                    children = rel_graph.get_all_relationships_with_tags(
                        unemployed.gameobject.id, "Child"
                    )
                    for rel in children:
                        child = self.world.get_gameobject(rel.target)
                        if (
                            child.id in residence.residents
                            and child.id not in residence.owners
                        ):
                            depart.try_execute_event(self.world, Character=child)


class FindEmployeesSystem(ISystem):
    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        for _, (business, _, _, _) in self.world.get_components(
            Business, OpenForBusiness, Building, Active
        ):
            open_positions = business.get_open_positions()

            for position in open_positions:
                result = OccupationTypes.get(position).fill_role(self.world, business)

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


class Action:
    """
    Actions are interactions that characters can have with other characters

    """


class CompatibilityFn(Protocol):
    """
    Callable that returns a tuple containing the platonic and romantic
    compatibilities of two characters respectively
    """

    def __call__(
        self, world: World, subject_id: int, target_id: int
    ) -> Optional[Tuple[int, int]]:
        raise NotImplementedError


class SocializeSystem(ISystem):
    """
    Every timestep, characters interact with other characters
    at the same location. Characters meeting for the first time
    form relationships based on the compatibility of their
    personal values.
    """

    _compatibility_fns: List[CompatibilityFn] = []
    _social_actions: List[Action] = []

    __slots__ = "chance_of_interaction"

    def __init__(self, chance_of_interaction: float = 0.7) -> None:
        super().__init__()
        self.chance_of_interaction: float = chance_of_interaction

    @classmethod
    def add_compatibility_check(cls, fn: CompatibilityFn) -> None:
        """
        Add a function that modifies the platonic and romantic compatibility of two
        characters
        """
        cls._compatibility_fns.append(fn)

    @classmethod
    def add_social_action(cls, action: Action) -> None:
        """
        Add an action that a character can perform while at a location
        """
        cls._social_actions.append(action)

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

                if (
                    character.gameobject.try_component(Age).value < 3
                    or character.gameobject.try_component(Age).value < 3
                ):
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

                if character.gameobject.has_component(Child):
                    romance_score = 0.0
                elif (
                    rel_graph.get_connection(character_id, other_character_id).has_tag(
                        "Parent"
                    )
                    or rel_graph.get_connection(
                        other_character_id, character_id
                    ).has_tag("Parent")
                    or rel_graph.get_connection(
                        character_id, other_character_id
                    ).has_tag("Sibling")
                    or rel_graph.get_connection(
                        other_character_id, character_id
                    ).has_tag("Sibling")
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
                        )
                    )

                rel_graph.get_connection(
                    character_id, other_character_id
                ).romance.increase(int(romance_score))
                rel_graph.get_connection(
                    character_id, other_character_id
                ).friendship.increase(friendship_score)

                if not rel_graph.has_connection(other_character_id, character_id):
                    rel_graph.add_relationship(
                        Relationship(
                            other_character_id,
                            character_id,
                        ),
                    )
                rel_graph.get_connection(
                    other_character_id, character_id
                ).romance.increase(int(romance_score))
                rel_graph.get_connection(
                    other_character_id, character_id
                ).friendship.increase(friendship_score)


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
    ) -> Optional[IResidenceArchetype]:
        archetype_choices: List[IResidenceArchetype] = []
        archetype_weights: List[int] = []
        for archetype in ResidenceArchetypes.get_all():
            archetype_choices.append(archetype)
            archetype_weights.append(archetype.get_spawn_frequency())

        if archetype_choices:
            # Choose an archetype at random
            archetype: IResidenceArchetype = engine.rng.choices(
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

        vacancies = land_grid.get_vacancies()

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(len(land_grid)) < 0.4:
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(vacancies)

        archetype = self.choose_random_archetype(engine)

        if archetype is None:
            return None

        # Construct a random residence archetype
        residence = archetype.create(self.world)

        # Reserve the space
        land_grid[lot] = residence.id

        # Set the position of the residence
        residence.add_component(Position2D(lot[0], lot[1]))
        residence.add_component(Building(building_type="residential"))
        residence.add_component(Active())
        residence.add_component(Vacant())
        logger.debug(f"Built residential building ({residence.id})")


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
    ) -> Optional[IBusinessArchetype]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """
        town = self.world.get_resource(Town)
        date = self.world.get_resource(SimDateTime)

        archetype_choices: List[IBusinessArchetype] = []
        archetype_weights: List[int] = []

        for archetype in BusinessArchetypes.get_all():
            if (
                archetype.get_instances() < archetype.get_max_instances()
                and town.population >= archetype.get_min_population()
                and (
                    archetype.get_year_available()
                    <= date.year
                    < archetype.get_year_obsolete()
                )
            ):
                archetype_choices.append(archetype)
                archetype_weights.append(archetype.get_spawn_frequency())

        if archetype_choices:
            # Choose an archetype at random
            archetype: IBusinessArchetype = engine.rng.choices(
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
        business = archetype.create(self.world)

        # Reserve the space
        land_grid[lot] = business.id

        # Set the position of the residence
        business.get_component(Position2D).x = lot[0]
        business.get_component(Position2D).y = lot[1]

        # Give the business a building
        business.add_component(Building(building_type="commercial"))
        business.add_component(PendingOpening())
        business.add_component(Active())
        logger.debug(
            "Built new business({}) {}".format(
                business.id, str(business.get_component(Name))
            )
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

        for _, (residence, _, _, _) in self.world.get_components(
            Residence, Building, Active, Vacant
        ):
            # Return early if the random-roll is not sufficient
            if engine.rng.random() > self.chance_spawn:
                return

            archetype = choose_random_character_archetype(engine)

            # There are no archetypes available to spawn
            if archetype is None:
                return

            # Create a new entity using the archetype
            character = archetype.create(self.world, life_stage="young_adult")

            add_residence_owner(character, residence.gameobject)
            move_residence(character, residence.gameobject)
            move_to_location(self.world, character, residence.gameobject.id)
            town.increment_population()

            spouse: Optional[GameObject] = None
            # Potentially generate a spouse for this entity
            if engine.rng.random() < archetype.get_chance_spawn_with_spouse():
                # Create another character
                spouse = archetype.create(self.world, life_stage="young_adult")

                # Match the last names since they are supposed to be married
                spouse.get_component(CharacterName).surname = character.get_component(
                    CharacterName
                ).surname

                # Move them into the home with the first character
                add_residence_owner(spouse, residence.gameobject)
                move_residence(spouse, residence.gameobject)
                move_to_location(self.world, spouse, residence.gameobject.id)
                town.increment_population()

                # Configure relationship from character to spouse
                rel_graph.get_relationship(
                    character.id,
                    spouse.id,
                ).add_tag("Married")
                rel_graph.get_relationship(
                    character.id,
                    spouse.id,
                ).romance.increase(45)
                rel_graph.get_relationship(
                    character.id,
                    spouse.id,
                ).friendship.increase(30)

                # Configure relationship from spouse to character
                rel_graph.get_relationship(
                    spouse.id,
                    character.id,
                ).add_tag("Married")
                rel_graph.get_relationship(
                    spouse.id,
                    character.id,
                ).romance.increase(45)
                rel_graph.get_relationship(
                    spouse.id,
                    character.id,
                ).friendship.increase(30)

            # Note: Characters can spawn as single parents with kids
            num_kids = engine.rng.randint(0, archetype.get_max_children_at_spawn())
            children: List[GameObject] = []
            for _ in range(num_kids):
                child = archetype.create(self.world, life_stage="child")

                # Match the last names since they are supposed to be married
                spouse.get_component(CharacterName).surname = character.get_component(
                    CharacterName
                ).surname

                # Move them into the home with the first character
                move_residence(child, residence.gameobject)
                move_to_location(self.world, child, residence.gameobject.id)
                town.increment_population()

                children.append(child)

                # Relationship of child to character
                rel_graph.get_relationship(
                    child.id,
                    character.id,
                ).add_tag("Parent")
                rel_graph.get_relationship(
                    child.id,
                    character.id,
                ).friendship.increase(20)

                # Relationship of character to child
                rel_graph.get_relationship(
                    character.id,
                    child.id,
                ).add_tag("Child")
                rel_graph.get_relationship(
                    character.id,
                    child.id,
                ).friendship.increase(20)

                if spouse:
                    # Relationship of child to spouse
                    rel_graph.get_relationship(
                        child.id,
                        spouse.id,
                    ).add_tag("Parent")
                    rel_graph.get_relationship(
                        child.id,
                        spouse.id,
                    ).friendship.increase(20)

                    # Relationship of spouse to child
                    rel_graph.get_relationship(
                        spouse.id,
                        child.id,
                    ).add_tag("Child")
                    rel_graph.get_relationship(
                        spouse.id,
                        child.id,
                    ).friendship.increase(20)

                for sibling in children:
                    # Relationship of child to sibling
                    rel_graph.get_relationship(
                        child.id,
                        sibling.id,
                    ).add_tag("Sibling")
                    rel_graph.get_relationship(
                        child.id,
                        sibling.id,
                    ).friendship.increase(20)

                    # Relationship of sibling to child
                    rel_graph.get_relationship(
                        sibling.id,
                        child.id,
                    ).add_tag("Sibling")
                    rel_graph.get_relationship(
                        sibling.id,
                        child.id,
                    ).friendship.increase(20)

            # Record a life event
            event_logger.record_event(
                LifeEvent(
                    name="MoveIntoTown",
                    timestamp=date.to_iso_str(),
                    roles=[
                        Role("Residence", residence.gameobject.id),
                        *[
                            Role("Resident", r.id)
                            for r in [character, spouse, *children]
                            if r is not None
                        ],
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

        for _, (business, _, _) in self.world.get_components(
            Business, Building, OpenForBusiness
        ):
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
            age.value += age_increment

            if (
                character.gameobject.has_component(Child)
                and age.value >= life_stages.stages["teen"]
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
                and age.value >= life_stages.stages["young_adult"]
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
                and age.value >= life_stages.stages["adult"]
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
                and age.value >= life_stages.stages["elder"]
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


class PregnancySystem(ISystem):
    """
    Pregnancy system is responsible for managing ChildBirth events.
    It checks if the current date is after a pregnant entity's
    due date, and triggers a childbirth if it is.
    """

    def process(self, *args, **kwargs):
        current_date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)
        town = self.world.get_resource(Town)

        for _, (character, pregnancy, _) in self.world.get_components(
            GameCharacter, Pregnant, Active
        ):

            # Cast for the type-checker
            character = cast(GameCharacter, character)
            pregnancy = cast(Pregnant, pregnancy)

            birthing_parent_name = character.gameobject.get_component(CharacterName)

            if current_date >= pregnancy.due_date:
                continue

            baby = generate_child(
                self.world,
                character.gameobject,
                self.world.get_gameobject(pregnancy.partner_id),
            )

            town.increment_population()

            baby.get_component(Age).value = (
                current_date - pregnancy.due_date
            ).hours / HOURS_PER_YEAR

            baby.get_component(CharacterName).surname = birthing_parent_name.surname

            if character.gameobject.has_component(CurrentLocation):

                current_location = character.gameobject.get_component(CurrentLocation)

                move_to_location(
                    self.world,
                    baby,
                    current_location.location,
                )

                baby.add_component(LocationAliases())

                move_residence(
                    baby,
                    self.world.get_gameobject(
                        character.gameobject.get_component(Resident).residence
                    ),
                )

            # Birthing parent to child
            rel_graph.get_relationship(character.gameobject.id, baby.id).add_tag(
                "Child"
            )

            # Child to birthing parent
            rel_graph.get_relationship(baby.id, character.gameobject.id).add_tag(
                "Parent"
            )

            # Other parent to child
            rel_graph.get_relationship(
                pregnancy.partner_id,
                baby.id,
            ).add_tag("Child")

            # Child to other parent
            rel_graph.get_relationship(
                baby.id,
                pregnancy.partner_id,
            ).add_tag("Parent")

            # Create relationships with children of birthing parent
            for rel in rel_graph.get_all_relationships_with_tags(
                character.gameobject.id, Child
            ):
                if rel.target == baby.id:
                    continue
                # Baby to sibling
                rel_graph.get_relationship(baby.id, rel.target).add_tag("Sibling")
                # Sibling to baby
                rel_graph.get_relationship(rel.target, baby.id).add_tag("Sibling")

            # Create relationships with children of other parent
            for rel in rel_graph.get_all_relationships_with_tags(
                pregnancy.partner_id, Child
            ):
                if rel.target == baby.id:
                    continue
                # Baby to sibling
                rel_graph.get_relationship(baby.id, rel.target).add_tag("Sibling")

                # Sibling to baby
                rel_graph.get_relationship(rel.target, baby.id).add_tag("Sibling")

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

    def __init__(self, days_before_demolishing: int = 60) -> None:
        super().__init__()
        self.days_before_demolishing: int = days_before_demolishing

    def run(self, *args, **kwargs):
        for gid, pending_opening in self.world.get_component(PendingOpening):
            pending_opening.duration += self.elapsed_time.total_hours / HOURS_PER_DAY

            if pending_opening.duration >= self.days_before_demolishing:
                pending_opening.gameobject.remove_component(PendingOpening)
                pending_opening.gameobject.add_component(ClosedForBusiness())
                logger.debug(
                    "{} has closed for business after never finding an owner.".format(
                        str(pending_opening.gameobject.get_component(Name))
                    )
                )


class OpenForBusinessSystem(System):
    """
    Tracks how long a business has been active
    """

    def run(self, *args, **kwargs):
        for _, (open_for_business, age, _) in self.world.get_components(
            OpenForBusiness, Age, Active
        ):
            # Increment the amount of time that the business has been open
            age.value += self.elapsed_time.total_hours / HOURS_PER_DAY


class ClosedForBusinessSystem(ISystem):
    """
    This system is responsible for removing Businesses from play that are marked as
    ClosedForBusiness. It removes the building from play, keeps the GameObject for
    sifting purposes, and displaces the characters within the building.
    """

    def process(self, *args, **kwargs):
        for gid, (out_of_business, location, business, _) in self.world.get_components(
            ClosedForBusiness, Location, Business, Active
        ):
            # Send all the entities here somewhere else
            for entity_id in location.entities:
                entity = self.world.get_gameobject(entity_id)

                if entity.has_component(GameCharacter):
                    # Send all the characters that are present back to their homes
                    move_to_location(
                        self.world,
                        entity,
                        None,
                    )
                else:
                    # Delete everything that is not a character
                    # assume that it will get lost in the demolition
                    self.world.delete_gameobject(entity_id)

            # Fire all the employees and owner
            for employee_id in business.get_employees():
                layoff_employee(business, self.world.get_gameobject(employee_id))

            # Free up the space on the board
            demolish_building(out_of_business.gameobject)

            business.gameobject.remove_component(Active)


class RemoveDeceasedFromResidences(ISystem):
    def process(self, *args, **kwargs):
        for gid, (deceased, resident) in self.world.get_components(Deceased, Resident):
            residence = self.world.get_gameobject(resident.residence)
            move_out_of_residence(resident.gameobject, residence)
            if residence.get_component(Residence).is_owner(gid):
                remove_residence_owner(deceased.gameobject, residence)


class RemoveDeceasedFromOccupation(ISystem):
    def process(self, *args, **kwargs):
        for gid, (deceased, occupation) in self.world.get_components(
            Deceased, Occupation
        ):
            business = self.world.get_gameobject(occupation.business).get_component(
                Business
            )

            end_job(business, deceased.gameobject, occupation)


class RemoveDepartedFromResidences(ISystem):
    def process(self, *args, **kwargs):
        for gid, (departed, resident) in self.world.get_components(Departed, Resident):
            residence = self.world.get_gameobject(resident.residence)
            move_out_of_residence(resident.gameobject, residence)
            if residence.get_component(Residence).is_owner(gid):
                remove_residence_owner(departed.gameobject, residence)


class RemoveDepartedFromOccupation(ISystem):
    def process(self, *args, **kwargs):
        for gid, (departed, occupation) in self.world.get_components(
            Departed, Occupation
        ):
            business = self.world.get_gameobject(occupation.business).get_component(
                Business
            )
            end_job(business, departed.gameobject, occupation)


class RemoveRetiredFromOccupation(ISystem):
    def process(self, *args, **kwargs):
        for gid, (departed, occupation) in self.world.get_components(
            Retired, Occupation
        ):
            business = self.world.get_gameobject(occupation.business).get_component(
                Business
            )
            end_job(business, departed.gameobject, occupation)
