import random
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, DefaultDict, Optional, Type

from neighborly.components.business import Occupation, Unemployed
from neighborly.components.character import (
    CanAge,
    ChildOf,
    Family,
    GameCharacter,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
    Pregnant,
    SiblingOf,
)
from neighborly.components.residence import Resident
from neighborly.components.routine import ROUTINE_PRIORITY_BOOSTS, Routine
from neighborly.components.shared import (
    Age,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
)
from neighborly.config import NeighborlyConfig
from neighborly.core.ai.brain import AIBrain, Goals
from neighborly.core.ecs import Active, GameObject, ISystem, SystemGroup
from neighborly.core.life_event import RandomLifeEvent, AllEvents, RandomLifeEvents
from neighborly.core.relationship import (
    Friendship,
    IncrementCounter,
    InteractionScore,
    Relationship,
    RelationshipFacet,
    Romance,
    add_relationship,
    add_relationship_status,
    evaluate_social_rules,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
    lerp,
)
from neighborly.core.roles import RoleList
from neighborly.core.status import remove_status
from neighborly.core.time import DAYS_PER_YEAR, SimDateTime, TimeDelta
from neighborly.events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    GiveBirthEvent,
)
from neighborly.plugins.defaults.actions import DepartSimulation, FindEmployment
from neighborly.utils.common import (
    add_character_to_settlement,
    get_child_prefab,
    set_character_age,
    set_frequented_locations,
    set_residence,
    spawn_character,
)


class InitializationSystemGroup(SystemGroup):
    """A group of systems that run once at the beginning of the simulation"""

    group_name = "initialization"
    priority = 99999

    def process(self, *args: Any, **kwargs: Any) -> None:
        super().process(*args, **kwargs)
        self.world.remove_system(type(self))


class EarlyUpdateSystemGroup(SystemGroup):
    """The early phase of the update loop"""

    group_name = "early-update"


class UpdateSystemGroup(SystemGroup):
    """The middle phase of the update loop"""

    group_name = "update"


class LateUpdateSystemGroup(SystemGroup):
    """The late phase of the update loop"""

    group_name = "late-update"


class RelationshipUpdateSystemGroup(SystemGroup):
    group_name = "relationship-update"
    sys_group = "early-update"


class StatusUpdateSystemGroup(SystemGroup):
    group_name = "status-update"
    sys_group = "early-update"


class GoalSuggestionSystemGroup(SystemGroup):
    group_name = "goal-suggestion"
    sys_group = "early-update"


class DataCollectionSystemGroup(SystemGroup):
    sys_group = "early-update"
    group_name = "data-collection"


class System(ISystem, ABC):
    """
    System is a more fully-featured System abstraction that
    handles common calculations like calculating the elapsed
    time between calls.
    """

    sys_group = "update"

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
    sys_group = "late-update"
    priority = -999999

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


class RandomLifeEventSystem(System):
    """Attempts to execute non-optional life events

    Life events triggered by this system do not pass through the character AI. You can
    consider these events as the simulation making an authoritative decision that
    something is going to happen, checking the preconditions, and finally making it so.

    It is the simplest form of narrative content creation in the simulation since you
    do not need to worry about characters approving of life event before they are
    allowed to take place.
    """

    sys_group = "update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        """Simulate LifeEvents for characters"""
        rng = self.world.get_resource(random.Random)

        total_population = len(self.world.get_components((GameCharacter, Active)))

        if RandomLifeEvents.get_size() == 0:
            return

        event_type: Type[RandomLifeEvent]
        for _ in range(total_population // 10):
            event_type = RandomLifeEvents.pick_one(rng)
            if event := event_type.instantiate(self.world, RoleList()):
                if rng.random() < event.get_probability():
                    event.execute()


class MeetNewPeopleSystem(ISystem):
    """Characters meet new people based on places they frequent"""

    sys_group = "update"

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


class CharacterAgingSystem(System):
    """
    Updates the ages of characters, adds/removes life
    stage components (Adult, Child, Elder, ...), and
    handles entity deaths.

    Notes
    -----
    This system runs every time step
    """

    sys_group = "update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        all_events = self.world.get_resource(AllEvents)

        age_increment = float(self.elapsed_time.total_days) / DAYS_PER_YEAR

        for guid, (_, life_stage, age, _, _) in self.world.get_components(
            (GameCharacter, LifeStage, Age, CanAge, Active)
        ):
            character = self.world.get_gameobject(guid)

            life_stage_value_before = int(life_stage)
            set_character_age(character, age.value + age_increment)
            life_stage_after = int(life_stage)

            life_stage_changed = life_stage_value_before != life_stage_after

            if life_stage_changed is False:
                continue

            if life_stage_after == LifeStageType.Adolescent:
                event = BecomeAdolescentEvent(current_date, character)
                character.fire_event(event)
                all_events.append(event)

            elif life_stage_after == LifeStageType.YoungAdult:
                event = BecomeYoungAdultEvent(current_date, character)
                character.fire_event(event)
                all_events.append(event)

            elif life_stage_after == LifeStageType.Adult:
                event = BecomeAdultEvent(current_date, character)
                character.fire_event(event)
                all_events.append(event)

            elif life_stage_after == LifeStageType.Senior:
                event = BecomeSeniorEvent(current_date, character)
                character.fire_event(event)
                all_events.append(event)


class UnemployedStatusSystem(System):
    sys_group = "status-update"
    years_to_find_a_job: float = 5.0

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        for guid, (unemployed, _) in self.world.get_components((Unemployed, Active)):
            character = self.world.get_gameobject(guid)
            years_unemployed = (
                float((current_date - unemployed.created).total_days) / DAYS_PER_YEAR
            )

            if years_unemployed < self.years_to_find_a_job:
                goal = FindEmployment(character)
                priority = goal.get_utility()[character]
                character.get_component(Goals).push_goal(priority, goal)

            else:
                spouses = get_relationships_with_statuses(character, Married)

                # Do not depart if one or more of the entity's spouses has a job
                if not any(
                    [
                        self.world.get_gameobject(
                            rel.get_component(Relationship).target
                        ).has_component(Occupation)
                        for rel in spouses
                    ]
                ):
                    goal = DepartSimulation(character)
                    priority = goal.get_utility()[character]
                    character.get_component(Goals).push_goal(priority, goal)


class PregnantStatusSystem(System):
    sys_group = "status-update"

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)

        for guid, pregnant in self.world.get_component(Pregnant):
            character = self.world.get_gameobject(guid)

            if current_date <= pregnant.due_date:
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
            add_relationship_status(character, baby, Family())

            # Child to birthing parent
            add_relationship(baby, character)
            add_relationship_status(baby, character, ChildOf())
            add_relationship_status(baby, character, Family())

            # Other parent to child
            add_relationship(other_parent, baby)
            add_relationship_status(other_parent, baby, ParentOf())
            add_relationship_status(other_parent, baby, Family())

            # Child to other parent
            add_relationship(baby, other_parent)
            add_relationship_status(baby, other_parent, ChildOf())
            add_relationship_status(baby, other_parent, Family())

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_statuses(character, ParentOf):
                rel = relationship.get_component(Relationship)

                if rel.target == baby.uid:
                    continue

                sibling = self.world.get_gameobject(rel.target)

                # Baby to sibling
                add_relationship(baby, sibling)
                add_relationship_status(baby, sibling, SiblingOf())
                add_relationship_status(baby, sibling, Family())

                # Sibling to baby
                add_relationship(sibling, baby)
                add_relationship_status(sibling, baby, SiblingOf())
                add_relationship_status(sibling, baby, Family())

            # Create relationships with children of other parent
            for relationship in get_relationships_with_statuses(other_parent, ParentOf):
                rel = relationship.get_component(Relationship)
                if rel.target == baby.uid:
                    continue

                sibling = self.world.get_gameobject(rel.target)

                # Baby to sibling
                add_relationship(baby, sibling)
                add_relationship_status(baby, sibling, SiblingOf())
                add_relationship_status(baby, sibling, Family())

                # Sibling to baby
                add_relationship(sibling, baby)
                add_relationship_status(sibling, baby, SiblingOf())
                add_relationship_status(sibling, baby, Family())

            remove_status(character, Pregnant)

            # Pregnancy event dates are retro-fit to be the actual date that the
            # child was due.
            child_born_event = GiveBirthEvent(
                current_date, character, other_parent, baby
            )
            birth_event = BirthEvent(current_date, baby)

            character.fire_event(child_born_event)
            other_parent.fire_event(child_born_event)
            baby.fire_event(birth_event)

            self.world.get_resource(AllEvents).append(child_born_event)
            self.world.get_resource(AllEvents).append(birth_event)


class RelationshipUpdateSystem(ISystem):
    """Increases the elapsed time for all statuses by one month"""

    sys_group = "relationship-update"

    def process(self, *args: Any, **kwargs: Any):
        for rel_id, (relationship, _) in self.world.get_components(
            (Relationship, Active)
        ):
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


class FriendshipStatSystem(ISystem):
    sys_group = "relationship-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        k = self.world.get_resource(NeighborlyConfig).settings.get(
            "relationship_growth_constant", 2
        )
        for _, (friendship, interaction_score, _) in self.world.get_components(
            (Friendship, InteractionScore, Active)
        ):
            friendship.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-k, k, friendship.get_normalized_value())
                )
            )


class RomanceStatSystem(ISystem):
    sys_group = "relationship-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        k = self.world.get_resource(NeighborlyConfig).settings.get(
            "relationship_growth_constant", 2
        )
        for _, (romance, interaction_score, _) in self.world.get_components(
            (Romance, InteractionScore, Active)
        ):
            romance.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-k, k, romance.get_normalized_value())
                )
            )


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
    It allows characters to choose new places to frequent that maybe didn't exist prior.
    """

    sys_group = "early-update"

    def __init__(self):
        super().__init__(interval=TimeDelta(months=3))

    def run(self, *args: Any, **kwargs: Any) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        for guid, (_, current_settlement, _) in self.world.get_components(
            (FrequentedLocations, CurrentSettlement, Active)
        ):
            character = self.world.get_gameobject(guid)

            # Sample from available locations
            set_frequented_locations(
                character,
                self.world.get_gameobject(current_settlement.settlement),
            )

            # Add residence
            if resident := character.try_component(Resident):
                residence = self.world.get_gameobject(resident.residence)
                if frequented_by := residence.try_component(FrequentedBy):
                    frequented_by.add(guid)
                    character.get_component(FrequentedLocations).locations.add(
                        residence.uid
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
    """AIs execute actions.

    This system loops through all the AIComponents and has them attempt to execute
    actions that have been suggested to them by other systems. This system should run
    later in the update phase to allow other systems to suggest actions, but it should
    run before the late-update phase to allow event listeners to respond to events
    generated by actions.
    """

    sys_group = "update"

    UTILITY_THRESHOLD: float = 0.3

    def run(self, *args: Any, **kwargs: Any) -> None:
        rng = self.world.get_resource(random.Random)
        for _, (_, goals, _) in self.world.get_components((AIBrain, Goals, Active)):
            # GameObjects may have become deactivated by the actions of
            # another that ran before them in this loop. We need to ensure
            # that inactive GameObjects are not pursuing goals
            if goals.gameobject.has_component(Active) is False:
                continue

            if not goals.has_options():
                goals.clear_goals()
                continue

            goal = goals.pick_one(rng)

            if (
                not goal.is_complete()
                and goal.get_utility()[goals.gameobject] >= self.UTILITY_THRESHOLD
            ):
                goal.take_action()

            goals.clear_goals()


class AIRoutineSystem(System):
    """Adds additional goals to character AI based on a routine."""

    sys_group = "goal-suggestion"

    def run(self, *args: Any, **kwargs: Any) -> None:
        current_date = self.world.get_resource(SimDateTime)
        for guid, (goals, routine) in self.world.get_components((Goals, Routine)):
            routine_entry = routine.get_entry_for_time(
                current_date.weekday, current_date.hour
            )
            gameobject = self.world.get_gameobject(guid)
            if routine_entry is not None:
                g = routine_entry.goal
                g_priority = g.get_utility()[gameobject]
                goals.push_goal(
                    g_priority + ROUTINE_PRIORITY_BOOSTS[routine_entry.priority], g
                )
