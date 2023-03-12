import dataclasses
import random
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, DefaultDict, List, Optional, Type

import neighborly.events
from neighborly.actions import StartBusinessAction
from neighborly.components.business import (
    Business,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
    Unemployed,
)
from neighborly.components.character import (
    Adolescent,
    Adult,
    CanAge,
    Child,
    ChildOf,
    Dating,
    Departed,
    GameCharacter,
    MarriageConfig,
    Married,
    ParentOf,
    Pregnant,
    ReproductionConfig,
    Senior,
    SiblingOf,
    YoungAdult,
)
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    Active,
    Age,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
)
from neighborly.components.spawn_table import CharacterSpawnTable, ResidenceSpawnTable
from neighborly.config import NeighborlyConfig
from neighborly.content_management import LifeEventLibrary, OccupationTypeLibrary
from neighborly.core.ai.brain import AIComponent
from neighborly.core.ai.movement import MovementAI
from neighborly.core.ai.socializing import SocialAI
from neighborly.core.ecs import GameObject, ISystem
from neighborly.core.ecs.ecs import SystemGroup
from neighborly.core.event import AllEvents, EventBuffer, EventHistory
from neighborly.core.life_event import ActionableLifeEvent, LifeEventBuffer
from neighborly.core.relationship import (
    Friendship,
    IncrementCounter,
    InteractionScore,
    Relationship,
    RelationshipFacet,
    Romance,
    lerp,
)
from neighborly.core.roles import RoleList
from neighborly.core.settlement import Settlement
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime, TimeDelta
from neighborly.utils.common import (
    add_character_to_settlement,
    add_residence_to_settlement,
    check_share_residence,
    get_child_prefab,
    get_life_stage,
    set_character_age,
    set_frequented_locations,
    set_location,
    set_residence,
    spawn_character,
    spawn_residence,
    start_job,
)
from neighborly.utils.relationships import (
    add_relationship,
    add_relationship_status,
    evaluate_social_rules,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
)
from neighborly.utils.statuses import add_status, has_status, remove_status


class InitializationSystemGroup(SystemGroup):
    """A group of systems that runs"""

    group_name = "initialization"
    priority = 99999

    def process(self, *args: Any, **kwargs: Any) -> None:
        super().process(*args, **kwargs)
        self.world.remove_system(type(self))


class EarlyCharacterUpdateSystemGroup(SystemGroup):
    """The first phase of character updates"""

    group_name = "early-character-update"
    sys_group = "character-update"
    priority = 99999


class EarlyUpdateSystemGroup(SystemGroup):
    """The phase of character updates"""

    group_name = "early-update"


class CharacterUpdateSystemGroup(SystemGroup):
    """The phase of character updates"""

    group_name = "character-update"


class LateCharacterUpdateSystemGroup(SystemGroup):
    """The last phase of character updates"""

    group_name = "late-character-update"
    sys_group = "character-update"
    priority = -99999


class BusinessUpdateSystemGroup(SystemGroup):
    """The phase of character updates"""

    group_name = "business-update"


class CoreSystemsSystemGroup(SystemGroup):
    group_name = "core"


class RelationshipUpdateSystemGroup(SystemGroup):
    group_name = "relationship-update"


class StatusUpdateSystemGroup(SystemGroup):
    group_name = "status-update"


class EventListenersSystemGroup(SystemGroup):
    group_name = "event-listeners"


class DataCollectionSystemGroup(SystemGroup):
    sys_group = "core"
    priority = -99998
    group_name = "data-collection"


class CleanUpSystemGroup(SystemGroup):
    """Group of systems that clean-up residual data before the next step"""

    group_name = "clean-up"
    priority = -99999


class System(ISystem, ABC):
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
        self._next_run: SimDateTime = SimDateTime(1, 1, 1)
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


class TimeSystem(ISystem):
    """Advances the current date of the simulation"""

    # The time system should be the last system to run every step. There's always the
    # possibility that a system may need to record the current date. So, we don't want
    # the date changing before all other systems have run.
    sys_group = "root"
    priority = -99999

    def process(self, *args: Any, **kwargs: Any) -> None:
        # Get time increment from the simulation configuration
        # this may be slow, but it is the cleanest configuration thus far
        increment = self.world.get_resource(NeighborlyConfig).time_increment
        current_date = self.world.get_resource(SimDateTime)
        current_date.increment(
            years=increment.years,
            months=increment.months,
            days=increment.days,
            hours=increment.hours,
        )


class LifeEventSystem(System):
    """Attempts to execute non-optional life events

    Life events triggered by this system do not pass through the character AI. You can
    consider these events as the simulation making an authoritative decision that
    something is going to happen, checking the preconditions, and finally making it so.

    It is the simplest form of narrative content creation in the simulation since you
    do not need to worry about characters approving of life event before they are
    allowed to take place.
    """

    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Simulate LifeEvents for characters"""
        life_event_lib = self.world.get_resource(LifeEventLibrary)
        life_event_buffer = self.world.get_resource(LifeEventBuffer)

        all_event_types = life_event_lib.get_all()

        total_population = len(self.world.get_components((GameCharacter, Active)))

        if len(all_event_types) == 0:
            return

        event_type: Type[ActionableLifeEvent]
        for _ in range(total_population // 10):
            event_type = random.choice(all_event_types)
            if event := event_type.instantiate(self.world, RoleList()):
                life_event_buffer.append(event)
                event.execute()


class MeetNewPeopleSystem(ISystem):
    """Characters meet new people based on places they frequent"""

    sys_group = "character-update"

    def process(self, *args: Any, **kwargs: Any):
        for gid, (_, _, frequented_locations) in self.world.get_components(
            (GameCharacter, Active, FrequentedLocations)
        ):
            character = self.world.get_gameobject(gid)

            candidate_scores: DefaultDict[GameObject, int] = defaultdict(int)

            for loc_id in frequented_locations.locations:
                for other_id in self.world.get_gameobject(loc_id).get_component(
                    FrequentedBy
                ):
                    other = self.world.get_gameobject(other_id)
                    if other_id != character.uid and not has_relationship(
                        character, other
                    ):
                        candidate_scores[other] += 1

            if candidate_scores:
                rng = self.world.get_resource(random.Random)

                acquaintance = rng.choices(
                    list(candidate_scores.keys()),
                    weights=list(candidate_scores.values()),
                    k=1,
                )[0]

                add_relationship(character, acquaintance)
                add_relationship(acquaintance, character)

                # Calculate interaction scores
                get_relationship(character, acquaintance).get_component(
                    InteractionScore
                ).increment(candidate_scores[acquaintance])

                get_relationship(acquaintance, character).get_component(
                    InteractionScore
                ).increment(candidate_scores[acquaintance])


class FindEmployeesSystem(ISystem):
    """Finds employees to work open positions at businesses"""

    sys_group = "core"

    def process(self, *args: Any, **kwargs: Any) -> None:
        occupation_types = self.world.get_resource(OccupationTypeLibrary)
        rng = self.world.get_resource(random.Random)

        for guid, (business, _) in self.world.get_components(
            (Business, OpenForBusiness)
        ):
            open_positions = business.get_open_positions()

            for occupation_name in open_positions:
                occupation_type = occupation_types.get(occupation_name)

                candidates = [
                    self.world.get_gameobject(g)
                    for g, _ in self.world.get_components(
                        (InTheWorkforce, Active, Unemployed)
                    )
                ]

                candidates = [
                    c for c in candidates if occupation_type.passes_preconditions(c)
                ]

                if not candidates:
                    continue

                candidate = rng.choice(candidates)

                start_job(candidate, self.world.get_gameobject(guid), occupation_name)


class StartBusinessSystem(System):
    """Build a new business building at a random free space on the land grid."""

    sys_group = "core"

    def __init__(self):
        super().__init__(interval=TimeDelta(months=1))

    def run(self, *args: Any, **kwargs: Any) -> None:
        date = self.world.get_resource(SimDateTime)
        for g, _ in self.world.get_components((InTheWorkforce, Active, Unemployed)):
            character = self.world.get_gameobject(g)
            action = StartBusinessAction(date, character)
            character.get_component(AIComponent).append_action(action)


@dataclasses.dataclass
class GeneratedFamily:
    adults: List[GameObject] = dataclasses.field(default_factory=list)
    children: List[GameObject] = dataclasses.field(default_factory=list)


class SpawnFamilySystem(System):
    """Spawns new families in settlements

    This system runs every 6 months and spawns families into new or existing residences.

    Note
    ----
    This system depends on the "new_families_per_year" setting in the simulation
    config. You can see how this setting is accessed in the run method below.
    """

    sys_group = "core"

    def __init__(self) -> None:
        super().__init__(interval=TimeDelta(months=6))

    def _get_vacant_residences(self) -> List[GameObject]:
        return [
            self.world.get_gameobject(gid)
            for gid, _ in self.world.get_components(
                (Residence, Active, Vacant, CurrentSettlement)
            )
        ]

    def _try_build_residence(self, settlement: GameObject) -> Optional[GameObject]:
        land_map = settlement.get_component(Settlement).land_map
        vacancies = land_map.get_vacant_lots()
        spawn_table = settlement.get_component(ResidenceSpawnTable)
        rng = self.world.get_resource(random.Random)

        # Return early if there is nowhere to build
        if len(vacancies) == 0:
            return None

        # Don't build more housing if 60% of the land is used for residential buildings
        if len(vacancies) / float(land_map.get_total_lots()) < 0.4:
            return None

        # Pick a random lot from those available
        lot = rng.choice(vacancies)

        prefab = spawn_table.choose_random(rng)

        residence = spawn_residence(self.world, prefab)

        add_residence_to_settlement(
            residence,
            settlement=self.world.get_gameobject(settlement.uid),
            lot_id=lot,
        )

        return residence

    @staticmethod
    def _try_get_spouse_prefab(
        rng: random.Random,
        marriage_config: MarriageConfig,
        spawn_table: CharacterSpawnTable,
    ) -> Optional[str]:
        if rng.random() < marriage_config.chance_spawn_with_spouse:
            # Create another character to be their spouse
            potential_spouse_prefabs = spawn_table.get_matching_prefabs(
                *marriage_config.spouse_prefabs
            )

            if potential_spouse_prefabs:
                return rng.choice(potential_spouse_prefabs)

        return None

    def _spawn_family(self, spawn_table: CharacterSpawnTable) -> GeneratedFamily:
        rng = self.world.get_resource(random.Random)
        prefab = spawn_table.choose_random(rng)

        # Track all the characters generated
        generated_characters = GeneratedFamily()

        # Create a new entity using the archetype
        character = spawn_character(self.world, prefab, life_stage=YoungAdult)

        generated_characters.adults.append(character)

        spouse_prefab: Optional[str] = None
        spouse: Optional[GameObject] = None

        if marriage_config := character.try_component(MarriageConfig):
            spouse_prefab = self._try_get_spouse_prefab(
                rng, marriage_config, spawn_table
            )

        if spouse_prefab:
            spouse = spawn_character(
                self.world,
                spouse_prefab,
                last_name=character.get_component(GameCharacter).last_name,
                life_stage=Adult,
            )

            generated_characters.adults.append(spouse)

            # Configure relationship from character to spouse
            add_relationship(character, spouse)
            add_relationship_status(character, spouse, Married())
            add_relationship_status(character, spouse, Married())
            get_relationship(character, spouse).get_component(Romance).increment(45)
            get_relationship(character, spouse).get_component(Friendship).increment(30)
            get_relationship(character, spouse).get_component(
                InteractionScore
            ).increment(1)

            # Configure relationship from spouse to character
            add_relationship(spouse, character)
            add_relationship_status(spouse, character, Married())
            get_relationship(spouse, character).get_component(Romance).increment(45)
            get_relationship(spouse, character).get_component(Friendship).increment(30)
            get_relationship(spouse, character).get_component(
                InteractionScore
            ).increment(1)

        num_kids: int = 0
        children: List[GameObject] = []
        potential_child_prefabs: List[str] = []

        if reproduction_config := character.get_component(ReproductionConfig):
            num_kids = rng.randint(0, reproduction_config.max_children_at_spawn)

            potential_child_prefabs = spawn_table.get_matching_prefabs(
                *reproduction_config.child_prefabs
            )

        if potential_child_prefabs:
            chosen_child_prefabs = rng.sample(potential_child_prefabs, num_kids)

            for child_prefab in chosen_child_prefabs:
                child = spawn_character(
                    self.world,
                    child_prefab,
                    last_name=character.get_component(GameCharacter).last_name,
                    life_stage=Child,
                )
                generated_characters.children.append(child)
                children.append(child)

                # Relationship of child to character
                add_relationship(child, character)
                add_relationship_status(child, character, ChildOf())
                get_relationship(child, character).get_component(Friendship).increment(
                    20
                )
                get_relationship(child, character).get_component(
                    InteractionScore
                ).increment(1)

                # Relationship of character to child
                add_relationship(character, child)
                add_relationship_status(character, child, ParentOf())
                get_relationship(character, child).get_component(Friendship).increment(
                    20
                )
                get_relationship(character, child).get_component(
                    InteractionScore
                ).increment(1)

                if spouse:
                    # Relationship of child to spouse
                    add_relationship(child, spouse)
                    add_relationship_status(child, spouse, ChildOf())
                    get_relationship(child, spouse).get_component(Friendship).increment(
                        20
                    )
                    get_relationship(child, spouse).get_component(
                        InteractionScore
                    ).increment(1)

                    # Relationship of spouse to child
                    add_relationship(spouse, child)
                    add_relationship_status(spouse, child, ParentOf())
                    get_relationship(spouse, child).get_component(Friendship).increment(
                        20
                    )
                    get_relationship(spouse, child).get_component(
                        InteractionScore
                    ).increment(1)

                for sibling in children:
                    # Relationship of child to sibling
                    add_relationship(child, sibling)
                    add_relationship_status(child, sibling, SiblingOf())
                    get_relationship(child, sibling).get_component(
                        Friendship
                    ).increment(20)
                    get_relationship(child, sibling).get_component(
                        InteractionScore
                    ).increment(1)

                    # Relationship of sibling to child
                    add_relationship(sibling, child)
                    add_relationship_status(sibling, child, SiblingOf())
                    get_relationship(sibling, child).get_component(
                        Friendship
                    ).increment(20)
                    get_relationship(sibling, child).get_component(
                        InteractionScore
                    ).increment(1)

        return generated_characters

    def run(self, *args: Any, **kwargs: Any) -> None:
        families_per_year: int = self.world.get_resource(NeighborlyConfig).settings.get(
            "new_families_per_year", 10
        )
        families_to_spawn = families_per_year // 2

        rng = self.world.get_resource(random.Random)
        event_buffer = self.world.get_resource(LifeEventBuffer)
        date = self.world.get_resource(SimDateTime)

        # Spawn families in each settlement
        for guid, (settlement, character_spawn_table) in self.world.get_components(
            (Settlement, CharacterSpawnTable)
        ):
            settlement_entity = self.world.get_gameobject(guid)

            for _ in range(families_to_spawn):
                # Try to find a vacant residence
                vacant_residences = self._get_vacant_residences()
                if vacant_residences:
                    residence = rng.choice(vacant_residences)
                else:
                    # Try to create a new house
                    residence = self._try_build_residence(settlement_entity)
                    if residence is None:
                        break

                family = self._spawn_family(character_spawn_table)

                for adult in family.adults:
                    add_character_to_settlement(adult, settlement.gameobject)
                    set_residence(adult, residence, True)

                for child in family.children:
                    add_character_to_settlement(child, settlement.gameobject)
                    set_residence(child, residence, False)

                # Record a life event
                event_buffer.append(
                    neighborly.events.MoveResidenceEvent(
                        date, residence, *[*family.adults, *family.children]
                    )
                )


class OccupationUpdateSystem(System):
    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, occupation in self.world.get_component(Occupation):
            # Increment the amount of time that a character has held this occupation
            occupation.set_years_held(
                occupation.years_held
                + (float(self.elapsed_time.total_days) / DAYS_PER_YEAR)
            )


class CharacterAgingSystem(System):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles entity deaths.

    Notes
    -----
    This system runs every time step
    """

    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        event_log = self.world.get_resource(LifeEventBuffer)

        age_increment = float(self.elapsed_time.total_days) / DAYS_PER_YEAR

        for guid, (_, age, _, _) in self.world.get_components(
            (GameCharacter, Age, CanAge, Active)
        ):
            character = self.world.get_gameobject(guid)

            life_stage_value_before = get_life_stage(character).value()
            set_character_age(character, age.value + age_increment)
            life_stage_after = get_life_stage(character)

            life_stage_changed = life_stage_value_before != life_stage_after.value()

            if life_stage_changed is False:
                continue

            if life_stage_after == Adolescent:
                event_log.append(
                    neighborly.events.BecomeAdolescentEvent(current_date, character)
                )

            elif life_stage_after == YoungAdult:
                event_log.append(
                    neighborly.events.BecomeYoungAdultEvent(current_date, character)
                )

            elif life_stage_after == Adult:
                event_log.append(
                    neighborly.events.BecomeAdultEvent(current_date, character)
                )

            elif life_stage_after == Senior:
                event_log.append(
                    neighborly.events.BecomeSeniorEvent(current_date, character)
                )


class LifeEventBufferSystem(ISystem):
    sys_group = "event-listeners"
    priority = 9999

    def process(self, *args: Any, **kwargs: Any) -> None:
        life_event_buffer = self.world.get_resource(LifeEventBuffer)
        event_buffer = self.world.get_resource(EventBuffer)
        for event in life_event_buffer.iter_events():
            for role in event.iter_roles():
                if history := role.gameobject.try_component(EventHistory):
                    history.append(event)
            event_buffer.append(event)
        life_event_buffer.clear()


class EventSystem(ISystem):
    sys_group = "clean-up"
    priority = -9999

    def process(self, *args: Any, **kwargs: Any) -> None:
        event_log = self.world.get_resource(EventBuffer)
        all_events = self.world.get_resource(AllEvents)
        for event in event_log.iter_events():
            all_events.append(event)
        event_log.clear()


class UnemployedStatusSystem(System):
    sys_group = "status-update"
    years_to_find_a_job: float = 5.0

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        for guid, unemployed in self.world.get_component(Unemployed):
            character = self.world.get_gameobject(guid)
            years_unemployed = (
                float((current_date - unemployed.created).total_days) / DAYS_PER_YEAR
            )

            if years_unemployed >= self.years_to_find_a_job:
                spouses = get_relationships_with_statuses(character, Married)

                # Do not depart if one or more of the entity's spouses has a job
                if any(
                    [
                        self.world.get_gameobject(
                            rel.get_component(Relationship).target
                        ).has_component(Occupation)
                        for rel in spouses
                    ]
                ):
                    continue

                else:
                    characters_to_depart: List[GameObject] = [character]

                    # Have all spouses depart
                    # Allows for polygamy
                    for relationship in spouses:
                        rel = relationship.get_component(Relationship)
                        spouse = self.world.get_gameobject(rel.target)
                        if spouse.has_component(Active):
                            characters_to_depart.append(spouse)

                    # Have all children living in the same house depart
                    children = get_relationships_with_statuses(character, ParentOf)
                    for relationship in children:
                        rel = relationship.get_component(Relationship)
                        child = self.world.get_gameobject(rel.target)
                        if child.has_component(Active) and check_share_residence(
                            character, child
                        ):
                            characters_to_depart.append(child)

                    for c in characters_to_depart:
                        add_status(c, Departed())
                        remove_status(c, Active)

                    remove_status(character, Unemployed)

                    event = neighborly.events.DepartEvent(
                        self.world.get_resource(SimDateTime),
                        characters_to_depart,
                        "unemployment",
                    )

                    self.world.get_resource(LifeEventBuffer).append(event)


class PregnantStatusSystem(System):
    sys_group = "status-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)

        for guid, pregnant in self.world.get_component(Pregnant):
            character = self.world.get_gameobject(guid)

            if pregnant.due_date <= current_date:
                continue

            other_parent = self.world.get_gameobject(pregnant.partner_id)

            child_prefab = get_child_prefab(character, other_parent)

            assert child_prefab is not None

            baby = spawn_character(
                self.world,
                child_prefab,
                last_name=character.get_component(GameCharacter).last_name,
            )

            settlement = self.world.get_gameobject(
                character.get_component(CurrentSettlement).settlement
            )
            add_character_to_settlement(baby, settlement)

            set_residence(
                baby,
                self.world.get_gameobject(character.get_component(Resident).residence),
            )

            # Birthing parent to child
            add_relationship(character, baby)
            add_relationship_status(character, baby, ParentOf())

            # Child to birthing parent
            add_relationship(baby, character)
            add_relationship_status(baby, character, ChildOf())

            # Other parent to child
            add_relationship(other_parent, baby)
            add_relationship_status(other_parent, baby, ParentOf())

            # Child to other parent
            add_relationship(baby, other_parent)
            add_relationship_status(baby, other_parent, ChildOf())

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_statuses(character, ParentOf):
                rel = relationship.get_component(Relationship)

                if rel.target == baby.uid:
                    continue

                sibling = self.world.get_gameobject(rel.target)

                # Baby to sibling
                add_relationship(baby, sibling)
                add_relationship_status(baby, sibling, SiblingOf())

                # Sibling to baby
                add_relationship(sibling, baby)
                add_relationship_status(sibling, baby, SiblingOf())

            # Create relationships with children of other parent
            for relationship in get_relationships_with_statuses(other_parent, ParentOf):
                rel = relationship.get_component(Relationship)
                if rel.target == baby.uid:
                    continue

                sibling = self.world.get_gameobject(rel.target)

                # Baby to sibling
                add_relationship(baby, sibling)
                add_relationship_status(baby, sibling, SiblingOf())

                # Sibling to baby
                add_relationship(sibling, baby)
                add_relationship_status(sibling, baby, SiblingOf())

            remove_status(character, Pregnant)

            # Pregnancy event dates are retro-fit to be the actual date that the
            # child was due.
            self.world.get_resource(LifeEventBuffer).append(
                neighborly.events.GiveBirthEvent(
                    current_date, character, other_parent, baby
                )
            )

            self.world.get_resource(LifeEventBuffer).append(
                neighborly.events.BirthEvent(current_date, baby)
            )


class MarriedStatusSystem(System):
    sys_group = "status-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, married in self.world.get_component(Married):
            married.years += self.elapsed_time.total_days / DAYS_PER_YEAR


class DatingStatusSystem(System):
    sys_group = "status-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, dating in self.world.get_component(Dating):
            dating.years += self.elapsed_time.total_days / DAYS_PER_YEAR


class RelationshipUpdateSystem(System):
    """Increases the elapsed time for all statuses by one month"""

    sys_group = "relationship-update"

    def run(self, *args: Any, **kwargs: Any):
        for rel_id, relationship in self.world.get_component(Relationship):
            rel_entity = self.world.get_gameobject(rel_id)

            # Accumulate modifiers
            modifier_acc: DefaultDict[
                Type[RelationshipFacet], IncrementCounter
            ] = defaultdict(IncrementCounter)
            for modifier in relationship.iter_modifiers():
                for stat_type, value in modifier.values.items():
                    modifier_acc[stat_type] += value

            # Apply modifiers
            for comp in rel_entity.get_components():
                if isinstance(comp, RelationshipFacet):
                    comp.set_modifier(modifier_acc[type(comp)])


class FriendshipStatSystem(System):
    sys_group = "relationship-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (friendship, interaction_score) in self.world.get_components(
            (Friendship, InteractionScore)
        ):
            friendship.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-3, 3, friendship.get_normalized_value())
                )
            )


class RomanceStatSystem(System):
    sys_group = "relationship-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (romance, interaction_score) in self.world.get_components(
            (Romance, InteractionScore)
        ):
            romance.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-3, 3, romance.get_normalized_value())
                )
            )


class OnJoinSettlementSystem(ISystem):
    """Listens for events indicating a character has joined a settlement"""

    sys_group = "event-listeners"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for event in self.world.get_resource(EventBuffer).iter_events_of_type(
            neighborly.events.JoinSettlementEvent
        ):
            # Add young-adult or older characters to the workforce
            if (
                has_status(event.character, Active)
                and get_life_stage(event.character) >= YoungAdult
            ):
                add_status(event.character, InTheWorkforce())
                if not event.character.has_component(Occupation):
                    add_status(event.character, Unemployed())


class AddYoungAdultToWorkforceSystem(ISystem):
    """Adds new young-adult characters to the workforce"""

    sys_group = "event-listeners"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for event in self.world.get_resource(EventBuffer).iter_events_of_type(
            neighborly.events.BecomeYoungAdultEvent
        ):
            add_status(event.character, InTheWorkforce())

            if not event.character.has_component(Occupation):
                add_status(event.character, Unemployed())


class PrintEventBufferSystem(ISystem):
    """Logs events that have happened during the last timestep"""

    sys_group = "clean-up"
    priority = -9998

    def process(self, *args: Any, **kwargs: Any) -> None:
        for event in self.world.get_resource(EventBuffer).iter_events():
            print(str(event))


class EvaluateSocialRulesSystem(System):
    """Evaluates social rules against existing relationships

    This system reevaluates social rules on characters' relationships and updates the
    active modifiers. This system exists because we may need to update relationships to
    reflect new components or relationship statuses that were not present during the
    last social rule evaluation.
    """

    sys_group = "relationship-update"

    def __init__(self):
        super().__init__(interval=TimeDelta(months=4))

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, relationship_comp in self.world.get_component(Relationship):
            relationship = self.world.get_gameobject(guid)
            subject = self.world.get_gameobject(relationship_comp.owner)
            target = self.world.get_gameobject(relationship_comp.target)

            # Do not update relationships if any of the character involved are
            # not active in the simulation
            if not subject.has_component(Active) or not target.has_component(Active):
                continue

            evaluate_social_rules(relationship, subject, target)


class UpdateFrequentedLocationSystem(System):
    """Characters update the locations that they frequent

    This system runs on a regular interval to allow characters to update the locations
    that they frequent to reflect their current status and the state of the settlement.
    This system runs to allow characters to choose new places to frequent that maybe
    didn't exist before.
    """

    sys_group = "character-update"

    def __init__(self):
        super().__init__(interval=TimeDelta(months=3))

    def run(self, *args: Any, **kwargs: Any) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        for guid, (_, current_settlement) in self.world.get_components(
            (FrequentedLocations, CurrentSettlement)
        ):
            character = self.world.get_gameobject(guid)

            # Sample from available locations
            set_frequented_locations(
                character,
                self.world.get_gameobject(current_settlement.settlement),
            )

            # Add Job location
            if occupation := character.try_component(Occupation):
                business = self.world.get_gameobject(occupation.business)
                if frequented_by := business.try_component(FrequentedBy):
                    frequented_by.add(guid)
                    character.get_component(FrequentedLocations).locations.add(
                        business.uid
                    )


class AIActionSystem(System):
    """AI Components execute actions

    This system loops through all the AIComponents and has them attempt to execute
    actions that have been suggested to them by other systems. This system should run
    later in the update phase to allow other systems to suggest actions, but it should
    run before the late-update phase to allow event listeners to respond to events
    generated by actions.
    """

    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for guid, ai_component in self.world.get_component(AIComponent):
            gameobject = self.world.get_gameobject(guid)
            ai_component.execute_action(self.world, gameobject)


class MovementAISystem(System):
    """Updates the MovementAI components attached to characters"""

    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for gid, (movement_ai, _) in self.world.get_components((MovementAI, Active)):
            next_location = movement_ai.get_next_location(self.world)
            if next_location is not None:
                set_location(self.world.get_gameobject(gid), next_location)


class SocialAISystem(System):
    """Characters performs social actions"""

    sys_group = "character-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        for _, (social_ai, _) in self.world.get_components((SocialAI, Active)):
            action_instance = social_ai.get_next_action(self.world)
            if action_instance is not None:
                action_instance.execute()
