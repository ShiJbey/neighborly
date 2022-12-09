from __future__ import annotations

import logging
import random
from abc import abstractmethod
from typing import Any, List, Optional, Set, Tuple, cast

from neighborly.components.business import (
    Business,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
)
from neighborly.components.character import (
    CanAge,
    CharacterAgingConfig,
    GameCharacter,
    LifeStage,
    LifeStageValue,
)
from neighborly.components.relationship import Relationships
from neighborly.components.residence import Residence, Vacant
from neighborly.components.shared import Active, Age, Building, OpenToPublic, Position2D
from neighborly.core.ai import MovementAI, SocialAI
from neighborly.core.ecs import GameObject, ISystem
from neighborly.core.event import Event, EventLog, EventRole
from neighborly.core.query import QueryBuilder
from neighborly.core.settlement import Settlement
from neighborly.core.status import Status, has_status, remove_status
from neighborly.core.time import (
    DAYS_PER_YEAR,
    HOURS_PER_YEAR,
    SimDateTime,
    TimeDelta,
    Weekday,
)
from neighborly.engine import (
    IBusinessArchetype,
    LifeEvents,
    NeighborlyEngine,
    choose_random_character_archetype,
)
from neighborly.events import MoveIntoTownEvent, StartBusinessEvent, StartJobEvent
from neighborly.statuses.character import Unemployed
from neighborly.utils.business import fill_open_position, start_job
from neighborly.utils.common import set_location, set_residence

logger = logging.getLogger(__name__)


class System(ISystem):
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
        super(ISystem, self).__init__()
        self._last_run: Optional[SimDateTime] = None
        self._interval: TimeDelta = interval if interval else TimeDelta()
        self._next_run: SimDateTime = SimDateTime() + self._interval
        self._elapsed_time: TimeDelta = TimeDelta()

    @property
    def elapsed_time(self) -> TimeDelta:
        """Returns the amount of simulation time since the last update"""
        return self._elapsed_time

    def process(self, *args: Any, **kwargs: Any) -> None:
        """Handles internal bookkeeping before running the system"""
        date = self.world.get_resource(SimDateTime)

        if date >= self._next_run:
            if self._last_run is None:
                self._elapsed_time = TimeDelta()
            else:
                self._elapsed_time = date - self._last_run
            self._last_run = date.copy()
            self._next_run = date + self._interval
            self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> None:
        raise NotImplementedError


class LifeEventSystem(System):
    """
    LifeEventSimulator handles firing LifeEvents for characters
    and performing entity behaviors
    """

    def __init__(self, interval: Optional[TimeDelta] = None) -> None:
        super().__init__(interval=interval)

    def run(self, *args: Any, **kwarg: Any) -> None:
        """Simulate LifeEvents for characters"""
        settlement = self.world.get_resource(Settlement)
        rng = self.world.get_resource(NeighborlyEngine).rng

        # Perform number of events equal to 10% of the population

        for life_event in rng.choices(
            LifeEvents.get_all(), k=(int(settlement.population / 2))
        ):
            success = life_event.try_execute_event(self.world)
            if success:
                self.world.clear_command_queue()


class MovementAISystem(System):
    """Updates the MovementAI components attached to characters"""

    def run(self, *args: Any, **kwargs: Any) -> None:
        for gid, (movement_ai, _) in self.world.get_components(MovementAI, Active):
            movement_ai = cast(MovementAI, movement_ai)
            next_location = movement_ai.get_next_location(self.world)
            if next_location is not None:
                set_location(self.world, self.world.get_gameobject(gid), next_location)


class SocialAISystem(System):
    """Characters performs social actions"""

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (social_ai, _) in self.world.get_components(SocialAI, Active):
            social_ai = cast(SocialAI, social_ai)
            action_instance = social_ai.get_next_action(self.world)
            if action_instance is not None:
                action_instance.execute(self.world)


class EventSystem(ISystem):
    def process(self, *args: Any, **kwargs: Any) -> None:
        event_log = self.world.get_resource(EventLog)
        event_log.process_event_queue(self.world)


class StatusSystem(System):
    def run(self, *args: Any, **kwargs: Any) -> None:
        for gid, status_component in self.world.get_component(Status):
            status = self.world.get_gameobject(gid)

            if status_component.on_update:
                status_component.on_update(
                    self.world, status, self.elapsed_time.total_hours
                )

            if status_component.is_expired(self.world, status) is True:
                if status_component.on_expire:
                    status_component.on_expire(self.world, status)
                if status.parent:
                    remove_status(status.parent, status)
                    self.world.delete_gameobject(status.id)


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

    def process(self, *args: Any, **kwargs: Any) -> None:
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

    def process(self, *args: Any, **kwargs: Any):
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


class FindEmployeesSystem(ISystem):
    def process(self, *args: Any, **kwargs: Any) -> None:
        date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(EventLog)
        engine = self.world.get_resource(NeighborlyEngine)
        rng = self.world.get_resource(random.Random)

        for _, (business, _, _, _) in self.world.get_components(
            Business, OpenForBusiness, Building, Active
        ):
            business = cast(Business, business)
            open_positions = business.get_open_positions()

            for occupation_name in open_positions:
                occupation_type = engine.occupation_types.get(occupation_name)

                candidate_query = (
                    QueryBuilder(occupation_name)
                    .with_((InTheWorkforce, Active))
                    .filter_(
                        lambda world, *gameobjects: has_status(
                            gameobjects[0], Unemployed
                        )
                    )
                )

                if occupation_type.precondition:
                    candidate_query.filter_(occupation_type.precondition)

                candidate_list = candidate_query.build().execute(self.world)

                if not candidate_list:
                    continue

                candidate = self.world.get_gameobject(rng.choice(candidate_list)[0])

                occupation = Occupation(
                    occupation_type=occupation_name,
                    business=business.gameobject.id,
                    level=occupation_type.level,
                    start_date=self.world.get_resource(SimDateTime).copy(),
                )

                start_job(self.world, business, candidate, occupation)

                event_log.record_event(
                    StartJobEvent(
                        date,
                        business=business.gameobject,
                        character=candidate,
                        occupation=occupation_name,
                    )
                )


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

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Build a new residence when there is space"""
        settlement = self.world.get_resource(Settlement)
        engine = self.world.get_resource(NeighborlyEngine)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        vacancies = settlement.land_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(settlement.land_map.get_total_lots()) < 0.4:
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(vacancies)

        archetype = engine.residence_archetypes.choose_random_archetype(engine.rng)

        if archetype is None:
            return None

        # Construct a random residence archetype
        residence = archetype.create(self.world)

        # Reserve the space
        settlement.land_map.reserve_lot(lot, residence.id)

        # Set the position of the building
        position = settlement.land_map.get_lot_position(lot)
        residence.add_component(Position2D(position[0], position[1]))
        residence.add_component(Building(building_type="residential", lot=lot))
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
        settlement = self.world.get_resource(Settlement)
        date = self.world.get_resource(SimDateTime)

        archetype_choices: List[IBusinessArchetype] = []
        archetype_weights: List[int] = []

        for archetype in engine.business_archetypes.get_all():
            if (
                settlement.business_counts[archetype.get_name()]
                < archetype.get_max_instances()
                and settlement.population >= archetype.get_min_population()
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

    def find_business_owner(self, business: Business):
        """Find someone to run the new business"""
        engine = self.world.get_resource(NeighborlyEngine)
        rng = self.world.get_resource(random.Random)

        if business.owner_type is None:
            return None

        occupation_type = engine.occupation_types.get(business.owner_type)

        result = fill_open_position(self.world, occupation_type, business, rng)

        if result:
            candidate, occupation = result

            start_job(
                self.world,
                business,
                candidate,
                occupation,
                is_owner=True,
            )

            return candidate

        return None

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Build a new business when there is space"""
        settlement = self.world.get_resource(Settlement)
        engine = self.world.get_resource(NeighborlyEngine)
        event_log = self.world.get_resource(EventLog)

        # Return early if the random-roll is not sufficient
        if engine.rng.random() > self.chance_of_build:
            return

        vacancies = settlement.land_map.get_vacant_lots()

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return

        # Pick a random lot from those available
        lot = engine.rng.choice(vacancies)

        # Pick random eligible business archetype
        archetype = self.choose_random_eligible_business(engine)

        if archetype is None:
            return

        # Build a random business archetype
        business = archetype.create(self.world)

        # Attempt to find an owner
        if business.get_component(Business).needs_owner():
            owner = self.find_business_owner(business.get_component(Business))

            if owner is None:
                return

            event_log.record_event(
                StartBusinessEvent(
                    self.world.get_resource(SimDateTime),
                    owner,
                    business,
                    owner.get_component(Occupation).occupation_type,
                    business.name,
                )
            )

        # Reserve the space
        settlement.land_map.reserve_lot(lot, business.id)

        # Set the position of the building
        position = settlement.land_map.get_lot_position(lot)
        business.get_component(Position2D).x = position[0]
        business.get_component(Position2D).y = position[1]

        # Give the business a building
        business.add_component(Building(building_type="commercial", lot=lot))
        business.add_component(OpenForBusiness())
        business.add_component(Active())


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

    def run(self, *args: Any, **kwargs: Any) -> None:

        date = self.world.get_resource(SimDateTime)
        settlement = self.world.get_resource(Settlement)
        engine = self.world.get_resource(NeighborlyEngine)
        event_logger = self.world.get_resource(EventLog)

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

            # Track all the characters generated
            generated_characters: List[GameObject] = []

            # Create a new entity using the archetype
            character = archetype.create(self.world, life_stage="young_adult")
            generated_characters.append(character)

            set_residence(self.world, character, residence.gameobject, True)
            set_location(self.world, character, residence.gameobject.id)
            settlement.increment_population()

            spouse: Optional[GameObject] = None
            # Potentially generate a spouse for this entity
            if engine.rng.random() < archetype.get_chance_spawn_with_spouse():
                # Create another character
                spouse = archetype.create(self.world, life_stage="young_adult")
                generated_characters.append(spouse)

                # Match the last names since they are supposed to be married
                spouse.get_component(GameCharacter).last_name = character.get_component(
                    GameCharacter
                ).last_name

                # Move them into the home with the first character
                set_residence(self.world, spouse, residence.gameobject, True)
                set_location(self.world, spouse, residence.gameobject.id)
                settlement.increment_population()

                # Configure relationship from character to spouse
                character.get_component(Relationships).get(spouse.id).add_tags(
                    "Spouse", "Significant Other"
                )
                character.get_component(Relationships).get(spouse.id).romance.increase(
                    45
                )
                character.get_component(Relationships).get(
                    spouse.id
                ).friendship.increase(30)

                # Configure relationship from spouse to character
                spouse.get_component(Relationships).get(character.id).add_tags(
                    "Spouse", "Significant Other"
                )
                spouse.get_component(Relationships).get(character.id).romance.increase(
                    45
                )
                spouse.get_component(Relationships).get(
                    character.id
                ).friendship.increase(30)

            # Note: Characters can spawn as single parents with kids
            num_kids = engine.rng.randint(0, archetype.get_max_children_at_spawn())
            children: List[GameObject] = []
            for _ in range(num_kids):
                child = archetype.create(self.world, life_stage="child")
                generated_characters.append(child)

                # Match the last names since they are supposed to be married
                child.get_component(GameCharacter).last_name = character.get_component(
                    GameCharacter
                ).last_name

                # Move them into the home with the first character
                set_residence(self.world, child, residence.gameobject)
                set_location(self.world, child, residence.gameobject.id)
                settlement.increment_population()

                children.append(child)

                # Relationship of child to character
                child.get_component(Relationships).get(character.id).add_tags("Parent")
                child.get_component(Relationships).get(character.id).add_tags("Family")
                child.get_component(Relationships).get(
                    character.id
                ).friendship.increase(20)

                # Relationship of character to child
                character.get_component(Relationships).get(child.id).add_tags("Child")
                character.get_component(Relationships).get(child.id).add_tags("Family")
                character.get_component(Relationships).get(
                    child.id
                ).friendship.increase(20)

                if spouse:
                    # Relationship of child to spouse
                    child.get_component(Relationships).get(spouse.id).add_tags("Parent")
                    child.get_component(Relationships).get(spouse.id).add_tags("Family")
                    child.get_component(Relationships).get(
                        spouse.id
                    ).friendship.increase(20)

                    # Relationship of spouse to child
                    spouse.get_component(Relationships).get(child.id).add_tags("Child")
                    spouse.get_component(Relationships).get(child.id).add_tags("Family")
                    spouse.get_component(Relationships).get(
                        child.id
                    ).friendship.increase(20)

                for sibling in children:
                    # Relationship of child to sibling
                    child.get_component(Relationships).get(sibling.id).add_tags(
                        "Sibling"
                    )
                    child.get_component(Relationships).get(sibling.id).add_tags(
                        "Family"
                    )
                    child.get_component(Relationships).get(
                        sibling.id
                    ).friendship.increase(20)

                    # Relationship of sibling to child
                    sibling.get_component(Relationships).get(child.id).add_tags(
                        "Sibling"
                    )
                    sibling.get_component(Relationships).get(child.id).add_tags(
                        "Family"
                    )
                    sibling.get_component(Relationships).get(
                        child.id
                    ).friendship.increase(20)

            # Record a life event
            event_logger.record_event(
                MoveIntoTownEvent(date, residence.gameobject, *generated_characters)
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

    def run(self, *args: Any, **kwargs: Any) -> None:
        date = self.world.get_resource(SimDateTime)

        for _, (business, age, _, _) in self.world.get_components(
            Business, Age, Building, OpenForBusiness
        ):
            business = cast(Business, business)
            age = cast(Age, age)
            # Open/Close based on operating hours
            if business.operating_hours.get(Weekday[date.weekday_str]) is not None:
                business.gameobject.add_component(OpenToPublic())

            # Increment how long the business has been open for business
            age.value += self.elapsed_time.total_hours / HOURS_PER_YEAR


class CharacterAgingSystem(System):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles entity deaths.

    Notes
    -----
    This system runs every time step
    """

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(EventLog)

        age_increment = float(self.elapsed_time.total_hours) / HOURS_PER_YEAR

        for _, (character, age, life_stage, config, _, _) in self.world.get_components(
            GameCharacter, Age, LifeStage, CharacterAgingConfig, CanAge, Active
        ):
            config = cast(CharacterAgingConfig, config)
            life_stage = cast(LifeStage, life_stage)
            age = cast(Age, age)

            age.value += age_increment

            if (
                life_stage.stage == LifeStageValue.Child
                and age.value >= config.adolescent_age
            ):
                life_stage.stage = LifeStageValue.Adolescent
                event_log.record_event(
                    Event(
                        name="BecameAdolescent",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    ),
                )

            elif (
                life_stage.stage == LifeStageValue.Adolescent
                and age.value >= config.young_adult_age
            ):
                life_stage.stage = LifeStageValue.YoungAdult
                event_log.record_event(
                    Event(
                        name="BecomeYoungAdult",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    ),
                )

            elif (
                life_stage.stage == LifeStageValue.YoungAdult
                and age.value >= config.adult_age
            ):
                life_stage.stage = LifeStageValue.Adult
                event_log.record_event(
                    Event(
                        name="BecomeAdult",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    ),
                )

            elif (
                life_stage.stage == LifeStageValue.Adult
                and age.value >= config.senior_age
            ):
                life_stage.stage = LifeStageValue.Senior
                event_log.record_event(
                    Event(
                        name="BecomeSenior",
                        timestamp=current_date.to_iso_str(),
                        roles=[
                            EventRole("Character", character.gameobject.id),
                        ],
                    ),
                )
