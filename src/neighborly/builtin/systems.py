from __future__ import annotations

import itertools
import logging
import math
from typing import Callable, List, Optional, Protocol, Set, Tuple, Type, cast

from neighborly.builtin.events import depart_event
from neighborly.builtin.helpers import (
    generate_child_character,
    generate_young_adult_character,
    get_locations,
    move_residence,
    move_to_location,
)
from neighborly.builtin.statuses import (
    Adult,
    Child,
    Dating,
    Deceased,
    Elder,
    InRelationship,
    Married,
    Pregnant,
    Present,
    Teen,
    YoungAdult,
)
from neighborly.core.archetypes import (
    BusinessArchetype,
    BusinessArchetypeLibrary,
    CharacterArchetype,
    CharacterArchetypeLibrary,
    ResidenceArchetype,
    ResidenceArchetypeLibrary,
)
from neighborly.core.building import Building
from neighborly.core.business import (
    Business,
    BusinessStatus,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    OccupationTypeLibrary,
    OpenForBusiness,
    PendingOpening,
    Unemployed,
    WorkHistory,
    start_job,
)
from neighborly.core.character import CharacterName, GameCharacter
from neighborly.core.ecs import Component, GameObject, ISystem, World
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
from neighborly.core.rng import DefaultRNG
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


class RoutineSystem(ISystem):
    """
    Moves characters based on their Routine component
    characters with routines move to positions
    """

    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        engine = self.world.get_resource(NeighborlyEngine)

        for _, (character, routine, _) in self.world.get_components(
            GameCharacter, Routine, Present
        ):
            character = cast(GameCharacter, character)
            routine = cast(Routine, routine)

            routine_entries = routine.get_entries(date.weekday, date.hour)

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
        rel_graph = self.world.get_resource(RelationshipGraph)
        for gid, (unemployed, _) in self.world.get_components(Unemployed, Present):
            # Convert delta time from hours to days
            unemployed.duration_days += date.delta_time / 24

            # Trigger the DepartAction and cast this character
            # as the departee
            if unemployed.duration_days >= self.days_to_departure:
                spouses = rel_graph.get_all_relationships_with_tags(
                    gid, RelationshipTag.Spouse
                )
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


class RelationshipStatusSystem(ISystem):
    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)

        for _, (marriage, _) in self.world.get_components(Married, Present):
            # Convert delta time from hours to days
            marriage.duration_years += date.delta_time / HOURS_PER_YEAR

        for _, (dating, _) in self.world.get_components(Dating, Present):
            # Convert delta time from hours to days
            dating.duration_years += date.delta_time / HOURS_PER_YEAR

        for _, (relationship, _) in self.world.get_components(InRelationship, Present):
            # Convert delta time from hours to days
            relationship.duration_years += date.delta_time / HOURS_PER_YEAR


class FindEmployeesSystem(ISystem):
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


class SocializeSystem(ISystem):
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
                location.characters_present, 2
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


class BuildResidenceSystem(ISystem):
    __slots__ = "chance_of_build", "interval", "next_trigger"

    def __init__(
        self, chance_of_build: float = 0.5, interval: Optional[TimeDelta] = None
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
        residence.add_component(Building(building_type="residential"))


class BuildBusinessSystem(ISystem):
    __slots__ = "chance_of_build", "interval", "next_trigger"

    def __init__(
        self, chance_of_build: float = 0.5, interval: Optional[TimeDelta] = None
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

        # Give the business a building
        business.add_component(Building(building_type="commercial"))
        business.add_component(PendingOpening())


class SpawnResidentSystem(ISystem):
    """Adds new characters to the simulation"""

    __slots__ = "chance_spawn", "chance_married", "max_kids", "interval", "next_trigger"

    def __init__(
        self,
        chance_spawn: float = 0.5,
        chance_married: float = 0.5,
        max_kids: int = 3,
        interval: Optional[TimeDelta] = None,
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

        for _, (residence, _) in self.world.get_components(Residence, Building):
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
            character.add_component(Present())
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
                character.add_component(Present())
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
                character.add_component(Present())
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
                        Role("resident", r.id)
                        for r in [character, spouse, *children]
                        if r is not None
                    ],
                )
            )


class BusinessUpdateSystem(ISystem):
    __slots__ = "_last_update"

    def __init__(self) -> None:
        super().__init__()
        self._last_update: SimDateTime = SimDateTime()

    @staticmethod
    def is_within_operating_hours(current_hour: int, hours: Tuple[int, int]) -> bool:
        """Return True if the given hour is within the hours 24-hour time interval"""
        start, end = hours
        if start <= end:
            return start <= current_hour <= end
        else:
            # The time interval overflows to the next day
            return current_hour <= end or current_hour >= start

    def process(self, *args, **kwargs) -> None:
        date = self.world.get_resource(SimDateTime)
        rng = self.world.get_resource(NeighborlyEngine).rng
        land_grid = self.world.get_resource(LandGrid)

        elapsed_hours = (date - self._last_update).total_hours
        self._last_update = date.copy()

        years_in_business_increment = float(elapsed_hours) / HOURS_PER_YEAR

        for _, (business, _) in self.world.get_components(Business, Building):
            business = cast(Business, business)
            if business.status == BusinessStatus.OpenForBusiness:
                # Increment the age of the business
                business.increment_years_in_business(years_in_business_increment)

                # Check if this business is going to close
                if rng.random() < 0.3:
                    # Go Out of business
                    business.set_business_status(BusinessStatus.ClosedForBusiness)
                    business.owner = None
                    for employee in business.get_employees():
                        business.remove_employee(employee)
                        self.world.get_gameobject(employee).remove_component(Occupation)
                    business_position = business.gameobject.get_component(Position2D)
                    land_grid.free_space(
                        (int(business_position.x), int(business_position.y))
                    )
                    business.gameobject.archive()

                # Open/Close based on operating hours
                business.is_open = business.operating_hours.get(
                    Weekday[date.weekday_str]
                )


class CharacterAgingSystem(ISystem):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles character deaths.

    Notes
    -----
    This system runs every time step
    """

    __slots__ = "_last_update"

    def __init__(self) -> None:
        super().__init__()
        self._last_update: SimDateTime = SimDateTime()

    def process(self, *args, **kwargs) -> None:
        current_date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventLog)

        elapsed_hours = (current_date - self._last_update).total_hours
        self._last_update = current_date.copy()

        age_increment = float(elapsed_hours) / HOURS_PER_YEAR

        for _, (character, _) in self.world.get_components(GameCharacter, Present):
            character = cast(GameCharacter, character)

            character.age += age_increment

            if (
                character.gameobject.has_component(Child)
                and character.age >= character.character_def.life_stages["teen"]
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
                and character.age >= character.character_def.life_stages["young_adult"]
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
                and character.age >= character.character_def.life_stages["adult"]
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
                and character.age >= character.character_def.life_stages["elder"]
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
    It checks if the current date is after pregnant characters'
    due dates, and triggers childbirths if it is.
    """

    def process(self, *args, **kwargs):
        current_date = self.world.get_resource(SimDateTime)
        rel_graph = self.world.get_resource(RelationshipGraph)
        event_logger = self.world.get_resource(LifeEventLog)

        for _, (character, pregnancy, _) in self.world.get_components(
            GameCharacter, Pregnant, Present
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

            if character.location is not None:
                move_to_location(
                    self.world,
                    baby.get_component(GameCharacter),
                    self.world.get_gameobject(character.location).get_component(
                        Location
                    ),
                )

                move_residence(
                    baby.get_component(GameCharacter),
                    self.world.get_gameobject(
                        character.location_aliases["home"]
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
            # character.gameobject.remove_component(InTheWorkforce)

            # if character.gameobject.has_component(Occupation):
            #     character.gameobject.remove_component(Occupation)

            # TODO: Birthing parent should also leave their job


class PendingOpeningSystem(ISystem):

    __slots__ = "days_before_demolishing", "last_update"

    def __init__(self, days_before_demolishing: int = 30) -> None:
        super().__init__()
        self.days_before_demolishing: int = days_before_demolishing
        self.last_update: SimDateTime = SimDateTime()

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        elapsed_hours = (date - self.last_update).total_hours
        self.last_update = date.copy()

        for _, pending_opening in self.world.get_component(PendingOpening):
            pending_opening.duration += elapsed_hours / HOURS_PER_DAY

            if pending_opening.duration >= self.days_before_demolishing:
                demolish_building(pending_opening.gameobject)


class OpenForBusinessSystem(ISystem):

    __slots__ = "last_update"

    def __init__(self, days_before_demolishing: int = 30) -> None:
        super().__init__()
        self.days_before_demolishing: int = days_before_demolishing
        self.last_update: SimDateTime = SimDateTime()

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        elapsed_hours = (date - self.last_update).total_hours
        self.last_update = date.copy()

        rng = self.world.get_resource(NeighborlyEngine).rng

        for _, (business, open_for_business) in self.world.get_components(
            Business, OpenForBusiness
        ):
            # Cast to help the type-checker
            business = cast(Business, business)
            open_for_business = cast(OpenForBusiness, open_for_business)

            # Increment the amount of time that the business has been open
            open_for_business.duration += elapsed_hours / HOURS_PER_DAY

            # Calculate probability of going out of business
            if rng.random() < 0.3:
                close_for_business(business)


class ClosedForBusinessSystem(ISystem):

    __slots__ = "days_before_demolishing", "last_update"

    def __init__(self, days_before_demolishing: int = 30) -> None:
        super().__init__()
        self.days_before_demolishing: int = days_before_demolishing
        self.last_update: SimDateTime = SimDateTime()

    def process(self, *args, **kwargs):
        date = self.world.get_resource(SimDateTime)
        elapsed_hours = (date - self.last_update).total_hours
        self.last_update = date.copy()
        for _, out_of_business in self.world.get_component(ClosedForBusiness):
            out_of_business.duration += elapsed_hours / HOURS_PER_DAY

            if out_of_business.duration >= self.days_before_demolishing:
                demolish_building(out_of_business.gameobject)


###############################
# HELPERS
###############################


def demolish_building(gameobject: GameObject) -> None:
    """Remove the building component and free the land grid space"""
    world = gameobject.world
    gameobject.remove_component(Building)
    position = gameobject.get_component(Position2D)
    land_grid = world.get_resource(LandGrid)
    land_grid.free_space((int(position.x), int(position.y)))


def close_for_business(business: Business) -> None:
    """Close a business and remove all employees and the owner"""
    world = business.gameobject.world

    business.gameobject.add_component(ClosedForBusiness())

    for employee in business.get_employees():
        layoff_employee(business, world.get_gameobject(employee))

    if business.owner_type is not None:
        layoff_employee(business, world.get_gameobject(business.owner))
        business.owner = None


def layoff_employee(business: Business, employee: GameObject) -> None:
    """Remove an employee"""
    world = business.gameobject.world
    date = world.get_resource(SimDateTime)
    business.remove_employee(employee.id)

    occupation = employee.get_component(Occupation)

    fired_event = LifeEvent(
        name="LaidOffFromJob",
        timestamp=date.to_date_str(),
        roles=[
            Role("Business", business.gameobject.id),
            Role("Character", employee.id),
        ],
    )

    world.get_resource(LifeEventLog).record_event(fired_event)

    employee.get_component(WorkHistory).add_entry(
        occupation_type=occupation.occupation_type,
        business=business.gameobject.id,
        start_date=occupation.start_date,
        end_date=date.copy(),
        reason_for_leaving=fired_event,
    )

    employee.remove_component(Occupation)
