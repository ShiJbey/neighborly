import random
from collections import defaultdict
from typing import DefaultDict, List, Type

from neighborly.command import SpawnCharacter
from neighborly.components.business import (
    Business,
    Occupation,
    OccupationLibrary,
    OpenForBusiness,
    ServiceLibrary,
    Unemployed,
)
from neighborly.components.character import (
    AgingConfig,
    CanGetPregnant,
    ChildOf,
    Dating,
    Family,
    GameCharacter,
    LifeStage,
    LifeStageType,
    Married,
    ParentOf,
    Pregnant,
    SiblingOf,
)
from neighborly.components.items import ItemLibrary
from neighborly.components.residence import Residence, Resident
from neighborly.components.shared import (
    Age,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Lifespan,
    Location,
    Name,
)
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    CharacterSpawnTable,
    ResidenceSpawnTable,
)
from neighborly.config import NeighborlyConfig
from neighborly.core.ai.brain import AIBrain, Goals
from neighborly.core.ecs import Active, GameObject, ISystem, SystemGroup, World
from neighborly.core.life_event import RandomLifeEvent, RandomLifeEventLibrary
from neighborly.core.relationship import (
    Friendship,
    IncrementCounter,
    InteractionScore,
    Relationship,
    RelationshipFacet,
    RelationshipManager,
    Romance,
    add_relationship,
    add_relationship_status,
    evaluate_social_rules,
    get_relationship,
    get_relationships_with_statuses,
    has_relationship,
    lerp,
)
from neighborly.core.settlement import Settlement
from neighborly.core.status import add_status, has_status, remove_status
from neighborly.core.time import SimDateTime
from neighborly.events import (
    BecameAcquaintancesEvent,
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    BirthEvent,
    GetPregnantEvent,
    HaveChildEvent,
    SettlementCreatedEvent,
)
from neighborly.goals import (
    BreakUp,
    DepartSimulation,
    Die,
    FindEmployment,
    FindOwnPlace,
    FindRomance,
    GetDivorced,
    GetMarried,
    Retire,
)
from neighborly.utils.common import (
    add_character_to_settlement,
    get_child_prefab,
    is_employed,
    set_frequented_locations,
    set_residence,
    shutdown_business,
)
from neighborly.utils.query import is_single


############################################
#              SYSTEM GROUPS               #
############################################


class InitializationSystemGroup(SystemGroup):
    """A group of systems that run once at the beginning of the simulation.

    Any content initialization systems or initial world building systems should
    belong to this group.
    """

    def on_update(self, world: World) -> None:
        # Run all child systems first before deactivating
        super().on_update(world)
        self.set_active(False)


class EarlyUpdateSystemGroup(SystemGroup):
    """The early phase of the update loop."""

    pass


class UpdateSystemGroup(SystemGroup):
    """The main phase of the update loop."""

    pass


class LateUpdateSystemGroup(SystemGroup):
    """The late phase of the update loop."""

    pass


class RelationshipUpdateSystemGroup(SystemGroup):
    """System group for updating relationship components.

    If there are components that should grow or decay over time, their systems
    should be added to this group.
    """

    pass


class StatusUpdateSystemGroup(SystemGroup):
    """System group for updating status components."""

    pass


class GoalSuggestionSystemGroup(SystemGroup):
    """System group for suggesting Goals to characters"""

    pass


class DataCollectionSystemGroup(SystemGroup):
    """System group for collecting data.

    Any system that collects data during the course of the simulation should
    belong to this group.
    """

    pass


############################################
#        SYSTEMS ACTIVE BY DEFAULT         #
############################################


class TimeSystem(ISystem):
    """Advances the current date of the simulation."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)
        current_date.increment(years=1)


class RandomLifeEventSystem(ISystem):
    """Attempts to execute non-optional life events

    Life events triggered by this system do not pass through the character AI. You can
    consider these events as the simulation making an authoritative decision that
    something is going to happen, checking the preconditions, and finally making it so.

    It is the simplest form of narrative content creation in the simulation since you
    do not need to worry about characters approving of life event before they are
    allowed to take place.
    """

    def on_update(self, world: World) -> None:
        """Simulate LifeEvents for characters"""
        rng = world.resource_manager.get_resource(random.Random)
        event_library = world.resource_manager.get_resource(RandomLifeEventLibrary)

        total_population = len(world.get_components((GameCharacter, Active)))

        if len(event_library) == 0:
            return

        event_type: Type[RandomLifeEvent]
        for _ in range(total_population // 2):
            event_type = event_library.pick_one(rng)
            if event := event_type.instantiate(world):
                if rng.random() < event.get_probability():
                    event.dispatch()


class MeetNewPeopleSystem(ISystem):
    """Characters meet new people based on places they frequent"""

    def on_update(self, world: World) -> None:
        for gid, (_, _, frequented_locations) in world.get_components(
            (GameCharacter, Active, FrequentedLocations)
        ):
            character = world.gameobject_manager.get_gameobject(gid)

            candidate_scores: DefaultDict[GameObject, int] = defaultdict(int)

            for loc in frequented_locations:
                for other in loc.get_component(FrequentedBy):
                    if other != character and not has_relationship(character, other):
                        candidate_scores[other] += 1

            if candidate_scores:
                rng = world.resource_manager.get_resource(random.Random)

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

                event = BecameAcquaintancesEvent(
                    world,
                    world.resource_manager.get_resource(SimDateTime).copy(),
                    character,
                    acquaintance,
                )

                event.dispatch()


class IncrementAgeSystem(ISystem):
    """Increases the age of all active GameObjects with Age components."""

    def on_update(self, world: World) -> None:
        for _, (age, _) in world.get_components((Age, Active)):
            age.value += 1


class UpdateLifeStageSystem(ISystem):
    """Change the life stage of a character based on it's age an life stage config."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, (aging_config, age, _) in world.get_components(
            (AgingConfig, Age, Active)
        ):
            character = world.gameobject_manager.get_gameobject(guid)

            if not character.has_component(LifeStage):
                character.add_component(LifeStage())

            life_stage = character.get_component(LifeStage)

            if (
                age.value >= aging_config.senior_age
                and life_stage.life_stage != LifeStageType.Senior
            ):
                life_stage.life_stage = LifeStageType.Senior
                event = BecomeSeniorEvent(world, current_date, character)
                world.event_manager.dispatch_event(event)

            elif (
                age.value >= aging_config.adult_age
                and life_stage.life_stage != LifeStageType.Adult
            ):
                life_stage.life_stage = LifeStageType.Adult
                event = BecomeAdultEvent(world, current_date, character)
                world.event_manager.dispatch_event(event)

            elif (
                age.value >= aging_config.young_adult_age
                and life_stage.life_stage != LifeStageType.YoungAdult
            ):
                life_stage.life_stage = LifeStageType.YoungAdult
                event = BecomeYoungAdultEvent(world, current_date, character)
                world.event_manager.dispatch_event(event)

            elif (
                age.value >= aging_config.adolescent_age
                and life_stage.life_stage != LifeStageType.Adolescent
            ):
                event = BecomeAdolescentEvent(world, current_date, character)
                world.event_manager.dispatch_event(event)
                life_stage.life_stage = LifeStageType.Adolescent

            else:
                life_stage.life_stage = LifeStageType.Child


class UnemployedStatusSystem(ISystem):
    """Provides unemployed characters with a goal to find employment."""

    __slots__ = "years_to_find_a_job"

    years_to_find_a_job: int
    """The number of year characters can look for a job before considering departure."""

    def __init__(self, years_to_find_a_job: int = 5) -> None:
        super().__init__()
        self.years_to_find_a_job = years_to_find_a_job

    def on_update(self, world: World) -> None:
        current_year: int = world.resource_manager.get_resource(SimDateTime).year
        for guid, (unemployed, _) in world.get_components((Unemployed, Active)):
            character = world.gameobject_manager.get_gameobject(guid)

            years_unemployed = current_year - unemployed.created.year

            # Keep trying to find a job
            goal = FindEmployment(character)
            priority = goal.get_utility()[character]
            character.get_component(Goals).push_goal(priority, goal)

            # Start thinking about leaving the settlement
            if years_unemployed > self.years_to_find_a_job:
                spousal_relationships = get_relationships_with_statuses(
                    character, Married
                )

                # They should depart if they have no spouse(s)
                if len(spousal_relationships) == 0:
                    goal = DepartSimulation(character)
                    priority = goal.get_utility()[character]
                    character.get_component(Goals).push_goal(priority, goal)

                # Depart if non of their spouses has a job either
                if not any(
                    [
                        is_employed(rel.get_component(Relationship).target)
                        for rel in spousal_relationships
                    ]
                ):
                    goal = DepartSimulation(character)
                    priority = goal.get_utility()[character]
                    character.get_component(Goals).push_goal(priority, goal)


class ChildBirthSystem(ISystem):
    """Handles child births for pregnant characters."""

    def on_update(self, world: World) -> None:
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, pregnant in world.get_component(Pregnant):
            pregnant_character = world.gameobject_manager.get_gameobject(guid)

            if current_date.year <= pregnant.created.year:
                continue

            other_parent = pregnant.partner

            child_prefab = get_child_prefab(pregnant_character, other_parent)

            assert child_prefab is not None

            baby = (
                SpawnCharacter(
                    child_prefab,
                    last_name=pregnant_character.get_component(GameCharacter).last_name,
                )
                .execute(world)
                .get_result()
            )

            settlement = pregnant_character.get_component(CurrentSettlement).settlement
            add_character_to_settlement(baby, settlement)

            set_residence(
                baby,
                pregnant_character.get_component(Resident).residence,
            )

            # Birthing parent to child
            add_relationship(pregnant_character, baby)
            add_relationship_status(pregnant_character, baby, ParentOf())
            add_relationship_status(pregnant_character, baby, Family())

            # Child to birthing parent
            add_relationship(baby, pregnant_character)
            add_relationship_status(baby, pregnant_character, ChildOf())
            add_relationship_status(baby, pregnant_character, Family())

            # Other parent to child
            add_relationship(other_parent, baby)
            add_relationship_status(other_parent, baby, ParentOf())
            add_relationship_status(other_parent, baby, Family())

            # Child to other parent
            add_relationship(baby, other_parent)
            add_relationship_status(baby, other_parent, ChildOf())
            add_relationship_status(baby, other_parent, Family())

            # Create relationships with children of birthing parent
            for relationship in get_relationships_with_statuses(
                pregnant_character, ParentOf
            ):
                rel = relationship.get_component(Relationship)

                if rel.target == baby:
                    continue

                sibling = rel.target

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
                if rel.target == baby:
                    continue

                sibling = rel.target

                # Baby to sibling
                add_relationship(baby, sibling)
                add_relationship_status(baby, sibling, SiblingOf())
                add_relationship_status(baby, sibling, Family())

                # Sibling to baby
                add_relationship(sibling, baby)
                add_relationship_status(sibling, baby, SiblingOf())
                add_relationship_status(sibling, baby, Family())

            remove_status(pregnant_character, Pregnant)

            # Pregnancy event dates are retro-fit to be the actual date that the
            # child was due.
            have_child_event = HaveChildEvent(
                world, current_date, pregnant_character, other_parent, baby
            )
            birth_event = BirthEvent(world, current_date, baby)

            world.event_manager.dispatch_event(have_child_event)
            world.event_manager.dispatch_event(birth_event)


class RelationshipUpdateSystem(ISystem):
    """Increases the elapsed time for all statuses by one month"""

    def on_update(self, world: World) -> None:
        for rel_id, (relationship, _) in world.get_components((Relationship, Active)):
            rel_entity = world.gameobject_manager.get_gameobject(rel_id)

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
    """Updates the friendship score from one character to another."""

    def on_update(self, world: World) -> None:
        k = world.resource_manager.get_resource(NeighborlyConfig).settings.get(
            "relationship_growth_constant", 2
        )
        for _, (friendship, interaction_score, _) in world.get_components(
            (Friendship, InteractionScore, Active)
        ):
            # We increment as a function of their current interaction score
            #
            friendship.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-k, k, friendship.get_normalized_value())
                )
            )


class RomanceStatSystem(ISystem):
    def on_update(self, world: World) -> None:
        k = world.resource_manager.get_resource(NeighborlyConfig).settings.get(
            "relationship_growth_constant", 2
        )
        for _, (romance, interaction_score, _) in world.get_components(
            (Romance, InteractionScore, Active)
        ):
            romance.increment(
                round(
                    max(0, interaction_score.get_value())
                    * lerp(-k, k, romance.get_normalized_value())
                )
            )


class EvaluateSocialRulesSystem(ISystem):
    """Evaluates social rules against existing relationships

    This system reevaluates social rules on characters' relationships and updates the
    active modifiers. This system exists because we may need to update relationships to
    reflect new components or relationship statuses that were not present during the
    last social rule evaluation.
    """

    def on_update(self, world: World) -> None:
        for guid, relationship_comp in world.get_component(Relationship):
            relationship = world.gameobject_manager.get_gameobject(guid)
            subject = relationship_comp.owner
            target = relationship_comp.target

            # Do not update relationships if any of the character involved are
            # not active in the simulation
            if not subject.has_component(Active) or not target.has_component(Active):
                continue

            evaluate_social_rules(relationship, subject, target)


class UpdateFrequentedLocationSystem(ISystem):
    """Characters update the locations that they frequent

    This system runs on a regular interval to allow characters to update the locations
    that they frequent to reflect their current status and the state of the settlement.
    It allows characters to choose new places to frequent that maybe didn't exist prior.
    """

    def on_update(self, world: World) -> None:
        # Frequented locations are sampled from the current settlement
        # that the character belongs to
        for guid, (_, current_settlement, _) in world.get_components(
            (FrequentedLocations, CurrentSettlement, Active)
        ):
            character = world.gameobject_manager.get_gameobject(guid)

            # Sample from available locations
            set_frequented_locations(
                character,
                current_settlement.settlement,
            )

            # Add residence
            if resident := character.try_component(Resident):
                residence = resident.residence
                if frequented_by := residence.try_component(FrequentedBy):
                    frequented_by.add(character)
                    character.get_component(FrequentedLocations).add(residence)

            # Add Job location
            if occupation := character.try_component(Occupation):
                business = occupation.business
                if frequented_by := business.try_component(FrequentedBy):
                    frequented_by.add(character)
                    character.get_component(FrequentedLocations).add(business)


class AIActionSystem(ISystem):
    """AIs execute actions.

    This system loops through all the AIComponents and has them attempt to execute
    actions that have been suggested to them by other systems. This system should run
    later in the update phase to allow other systems to suggest actions, but it should
    run before the late-update phase to allow event listeners to respond to events
    generated by actions.
    """

    UTILITY_THRESHOLD: float = 0.3

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        for _, (_, goals, _) in world.get_components((AIBrain, Goals, Active)):
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


class DieOfOldAgeSystem(ISystem):
    """Things probabilistically die when they get close to their lifespan."""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for guid, (age, lifespan, _) in world.get_components((Age, Lifespan, Active)):
            probability_of_death = (
                age.value / (lifespan.value + 10.0)
                if age.value >= lifespan.value - 15
                else 0
            )

            if rng.random() < probability_of_death:
                Die(world.gameobject_manager.get_gameobject(guid)).evaluate()


class GoOutOfBusinessSystem(ISystem):
    @staticmethod
    def calculate_probability_of_closing(business: GameObject) -> float:
        """Calculate the probability of a business randomly going out of business."""
        lifespan = business.get_component(Lifespan).value
        current_date = business.world.resource_manager.get_resource(SimDateTime)

        years_in_business: int = (
            current_date.year - business.get_component(OpenForBusiness).created.year
        )

        return (years_in_business / (lifespan + 10)) ** 2

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        for guid, _ in world.get_components((Business, OpenForBusiness, Active)):
            business = world.gameobject_manager.get_gameobject(guid)
            probability_of_closing = (
                GoOutOfBusinessSystem.calculate_probability_of_closing(business)
            )
            if rng.random() < probability_of_closing:
                shutdown_business(business)


class PregnancySystem(ISystem):
    """Some characters may get pregnant when in romantic relationships."""

    @staticmethod
    def get_probability_of_pregnancy(character: GameObject) -> float:
        """Calculate probability of a character getting pregnant."""
        num_children = len(get_relationships_with_statuses(character, ParentOf))
        return 1.0 - (num_children / 5.0)

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)
        current_date = world.resource_manager.get_resource(SimDateTime)

        for guid, _ in world.get_components((CanGetPregnant, Active)):
            character = world.gameobject_manager.get_gameobject(guid)

            if not character.has_component(Pregnant):
                continue

            potential_partners: List[GameObject] = []

            # Try to find a romantic partner
            for other_character, relationship in character.get_component(
                RelationshipManager
            ).outgoing.items():
                if not other_character.has_component(Active):
                    continue

                if not (
                    has_status(relationship, Dating)
                    or has_status(relationship, Married)
                ):
                    continue

                potential_partners.append(other_character)

            if potential_partners:
                chosen_partner = rng.choice(potential_partners)

                if rng.random() < PregnancySystem.get_probability_of_pregnancy(
                    character
                ):
                    add_status(
                        character,
                        Pregnant(partner=chosen_partner),
                    )

                    event = GetPregnantEvent(
                        world, current_date, character, chosen_partner
                    )

                    event.dispatch()


class DatingBreakUpSystem(ISystem):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = BreakUp(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class MarriageSystem(ISystem):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Dating, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = GetMarried(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class EndMarriageSystem(ISystem):
    def on_update(self, world: World) -> None:
        for _, (relationship, _, _) in world.get_components(
            (Relationship, Married, Active)
        ):
            owner = relationship.owner
            target = relationship.target
            goal = GetDivorced(owner, target)
            utility = goal.get_utility().get(owner, 0)
            if utility > 0:
                owner.get_component(Goals).push_goal(utility, goal)


class FindRomanceSystem(ISystem):
    """
    Handles the dating/breakup loop

    This system is responsible for supplying characters with the goal to start dating or
    the goal to break up if they are already in a romantic relationship.
    """

    def on_update(self, world: World) -> None:
        for guid, (goals, _, life_stage) in world.get_components(
            (Goals, Active, LifeStage)
        ):
            character = world.gameobject_manager.get_gameobject(guid)
            if (
                is_single(character)
                and life_stage.life_stage >= LifeStageType.Adolescent
            ):
                goal = FindRomance(character)
                utility = goal.get_utility().get(character, 0)
                if utility > 0:
                    goals.push_goal(utility, goal)


class FindOwnPlaceSystem(ISystem):
    """
    This system looks for young-adult to adult-aged characters who don't own their own
    residence and encourages them to find their own residence or leave the simulation
    """

    def on_update(self, world: World) -> None:
        for guid, (_, _, life_stage, resident, goals) in world.get_components(
            (GameCharacter, Active, LifeStage, Resident, Goals)
        ):
            if (
                life_stage.life_stage == LifeStageType.Adult
                or life_stage.life_stage == LifeStageType.YoungAdult
            ):
                residence = resident.residence.get_component(Residence)
                character = world.gameobject_manager.get_gameobject(guid)
                if not residence.is_owner(character):
                    goal = FindOwnPlace(character)
                    utility = goal.get_utility()[character]
                    goals.push_goal(utility, goal)


class RetirementSystem(ISystem):
    """
    Encourages senior residents to retire from their jobs
    """

    def on_update(self, world: World) -> None:
        for guid, (_, _, life_stage, _, goals) in world.get_components(
            (GameCharacter, Active, LifeStage, Occupation, Goals)
        ):
            if life_stage.life_stage == LifeStageType.Senior:
                character = world.gameobject_manager.get_gameobject(guid)
                goal = Retire(character)
                utility = goal.get_utility()[character]
                goals.push_goal(utility, goal)


############################################
#          INITIALIZATION SYSTEMS          #
############################################


class InitializeServicesSystem(ISystem):
    """Creates Service Type GameObjects and update the library with references."""

    def on_update(self, world: World) -> None:
        service_library = world.resource_manager.get_resource(ServiceLibrary)

        for prefab_name in service_library.services_to_instantiate:
            service_obj = world.gameobject_manager.instantiate_prefab(prefab_name)
            service_obj.name = prefab_name
            service_library.add(service_obj)


class InitializeOccupationTypesSystem(ISystem):
    """Creates Occupation Type GameObjects and updates the library with references."""

    def on_update(self, world: World) -> None:
        occupation_library = world.resource_manager.get_resource(OccupationLibrary)

        for prefab_name in occupation_library.occupations_to_instantiate:
            occupation_type_obj = world.gameobject_manager.instantiate_prefab(
                prefab_name
            )
            occupation_type_obj.name = prefab_name
            occupation_library.add(occupation_type_obj)


class InitializeItemTypeSystem(ISystem):
    """Creates Item Type GameObjects and updates the library with references."""

    def on_update(self, world: World) -> None:
        item_library = world.resource_manager.get_resource(ItemLibrary)

        for prefab_name in item_library.items_to_instantiate:
            item_type_obj = world.gameobject_manager.instantiate_prefab(prefab_name)
            item_type_obj.name = prefab_name
            item_library.add(item_type_obj)


class InitializeSettlementSystem(ISystem):
    """Initializes a single settlement in the world."""

    def on_update(self, world: World) -> None:
        sim_config = world.resource_manager.get_resource(NeighborlyConfig)
        name_pattern = sim_config.settings.get("settlement_name", "#settlement_name#")
        width, length = sim_config.settings.get("settlement_size", (5, 5))
        character_spawn_entries = sim_config.settings.get("character_spawn_table", [])
        residence_spawn_entries = sim_config.settings.get("residence_spawn_table", [])
        business_spawn_entries = sim_config.settings.get("business_spawn_table", [])

        settlement = world.gameobject_manager.spawn_gameobject(
            components=[
                world.gameobject_manager.create_component(Name, value=name_pattern),
                world.gameobject_manager.create_component(
                    Settlement, length=length, width=width
                ),
                world.gameobject_manager.create_component(Location),
                world.gameobject_manager.create_component(Age),
                world.gameobject_manager.create_component(
                    CharacterSpawnTable, entries=character_spawn_entries
                ),
                world.gameobject_manager.create_component(
                    ResidenceSpawnTable, entries=residence_spawn_entries
                ),
                world.gameobject_manager.create_component(
                    BusinessSpawnTable, entries=business_spawn_entries
                ),
            ]
        )

        settlement.name = settlement.get_component(Name).value

        event = SettlementCreatedEvent(
            world=world,
            date=world.resource_manager.get_resource(SimDateTime).copy(),
            settlement=settlement,
        )

        world.event_manager.dispatch_event(event)
