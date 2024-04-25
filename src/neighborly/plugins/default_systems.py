"""Default systems to include into a simulation.

"""

import random
from typing import cast

from neighborly.components.business import Business, BusinessStatus, Occupation
from neighborly.components.character import Character, LifeStage, Pregnant, Sex
from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.ecs import Active, System, World
from neighborly.events.defaults import LeaveJobEvent
from neighborly.helpers.action import get_action_success_probability, get_action_utility
from neighborly.helpers.business import add_employee, close_business
from neighborly.helpers.character import move_into_residence
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import get_relationships_with_traits
from neighborly.libraries import JobRoleLibrary
from neighborly.life_event import LifeEvent
from neighborly.plugins.actions import (
    BecomeBusinessOwner,
    BreakUp,
    Divorce,
    FireEmployee,
    FormCrush,
    GetMarried,
    GetPregnant,
    PromoteEmployee,
    Retire,
    StartDating,
)
from neighborly.simulation import Simulation
from neighborly.systems import UpdateSystems


class FindJobSystem(System):
    """Unemployed characters try to find work."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        library = world.resources.get_resource(JobRoleLibrary)

        active_businesses = [
            business
            for _, (business, _) in world.get_components((Business, Active))
            if business.status == BusinessStatus.OPEN
        ]

        rng.shuffle(active_businesses)

        for _, (character_comp, _) in world.get_components((Character, Active)):
            character = character_comp.gameobject

            if character.has_component(Occupation):
                return None

            for business in active_businesses:
                open_positions = business.get_open_positions()

                for role_id in open_positions:
                    job_role = library.get_role(role_id)

                    if job_role.check_requirements(character):
                        add_employee(business.gameobject, character, job_role)


class FiredFromJobSystem(System):
    """Occasionally fire an employee or two."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (business, _) in world.get_components((Business, Active)):
            if business.status != BusinessStatus.OPEN:
                continue

            business_owner = business.owner

            if business_owner is None:
                continue

            # Evaluate firing each employee
            for employee, _ in business.employees.items():

                action = FireEmployee(business_owner, employee)

                utility_score = get_action_utility(action)

                if rng.random() < utility_score:

                    probability_success = get_action_success_probability(action)

                    if rng.random() < probability_success:
                        action.on_success()
                    else:
                        action.on_failure()


class JobPromotionSystem(System):
    """Occasionally promote characters to higher positions at their jobs."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        for _, (business, _) in world.get_components((Business, Active)):
            if business.status != BusinessStatus.OPEN:
                continue

            business_owner = business.owner

            if business_owner is None:
                continue

            potential_promotions: list[PromoteEmployee] = []
            potential_promotion_scores: list[float] = []

            # Evaluate promoting each employee
            for employee, current_role in business.employees.items():

                current_job_level = current_role.job_level

                open_positions = business.get_open_positions()

                for role_id in open_positions:
                    role = job_role_library.get_role(role_id)

                    if current_job_level >= role.job_level:
                        continue

                    action = PromoteEmployee(business_owner, employee, role)
                    utility = get_action_utility(action)

                    if utility > 0:
                        potential_promotions.append(action)
                        potential_promotion_scores.append(utility)

            if not potential_promotions:
                continue

            action = rng.choices(potential_promotions, potential_promotion_scores, k=1)[
                0
            ]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class BecomeBusinessOwnerSystem(System):
    """Characters have a chance of becoming a business owner."""

    def on_update(self, world: World) -> None:

        rng = world.resource_manager.get_resource(random.Random)

        pending_businesses = [
            business
            for _, (business, _) in world.get_components((Business, Active))
            if business.status == BusinessStatus.PENDING
        ]

        for _, (character, _) in world.get_components((Character, Active)):

            actions: list[BecomeBusinessOwner] = []
            action_utilities: list[float] = []

            for business in pending_businesses:
                if business.owner is not None:
                    continue

                owner_role = business.owner_role

                if not owner_role.requirements:
                    action = BecomeBusinessOwner(
                        character.gameobject, business.gameobject
                    )
                    utility_score = get_action_utility(action)

                    if utility_score > 0:
                        actions.append(action)
                        action_utilities.append(utility_score)

                else:
                    if owner_role.check_requirements(character.gameobject):
                        action = BecomeBusinessOwner(
                            character.gameobject, business.gameobject
                        )
                        utility_score = get_action_utility(action)

                        if utility_score > 0:
                            actions.append(action)
                            action_utilities.append(utility_score)

            if not actions:
                continue

            chosen_action = rng.choices(actions, action_utilities, k=1)[0]

            utility_score = get_action_utility(chosen_action)

            if rng.random() < utility_score:

                probability_success = get_action_success_probability(chosen_action)

                if rng.random() < probability_success:
                    pending_businesses.remove(
                        chosen_action.business.get_component(Business)
                    )
                    chosen_action.on_success()
                else:
                    chosen_action.on_failure()

    def handle_owner_leaving(self, event: LifeEvent) -> None:
        """Event listener placed on the business owners to track when they leave."""

        leave_job_event = cast(LeaveJobEvent, event)
        close_business(leave_job_event.business)


class CharacterDatingSystem(System):
    """Characters have a chance of dating their crush."""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):

            relationships = get_relationships_with_traits(character.gameobject, "crush")

            potential_romances: list[StartDating] = []
            potential_romance_scores: list[float] = []

            for relationship in relationships:
                partner = relationship.get_component(Relationship).target

                if partner.is_active is False:
                    continue

                action = StartDating(character.gameobject, partner)
                utility = get_action_utility(action)

                if utility > 0:
                    potential_romances.append(action)
                    potential_romance_scores.append(utility)

            if not potential_romances:
                continue

            action = rng.choices(potential_romances, potential_romance_scores, k=1)[0]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class CharacterMarriageSystem(System):
    """Characters have a chance to get married"""

    def on_update(self, world: World) -> None:
        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):

            relationships = get_relationships_with_traits(
                character.gameobject, "dating"
            )

            potential_marriages: list[GetMarried] = []
            potential_marriage_scores: list[float] = []

            for relationship in relationships:
                partner = relationship.get_component(Relationship).target

                if partner.is_active is False:
                    continue

                action = GetMarried(character.gameobject, partner)
                utility = get_action_utility(action)

                if utility > 0:
                    potential_marriages.append(action)
                    potential_marriage_scores.append(utility)

            if not potential_marriages:
                continue

            action = rng.choices(potential_marriages, potential_marriage_scores, k=1)[0]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class CharacterDivorceSystem(System):
    """Characters in marriages may choose to divorce their spouse."""

    def on_update(self, world: World) -> None:

        rng = world.resource_manager.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):

            marriages = get_relationships_with_traits(character.gameobject, "spouse")

            potential_divorces: list[Divorce] = []
            potential_divorce_scores: list[float] = []

            for relationship in marriages:
                partner = relationship.get_component(Relationship).target

                if partner.is_active is False:
                    continue

                action = Divorce(character.gameobject, partner)
                utility = get_action_utility(action)

                if utility > 0:
                    potential_divorces.append(action)
                    potential_divorce_scores.append(utility)

            if not potential_divorces:
                continue

            action = rng.choices(potential_divorces, potential_divorce_scores, k=1)[0]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class DatingBreakUpSystem(System):
    """Characters in dating relationships may choose to break-up with their partner."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):

            dating_relationships = get_relationships_with_traits(
                character.gameobject, "dating"
            )

            potential_break_ups: list[BreakUp] = []
            potential_break_up_scores: list[float] = []

            if dating_relationships:
                relationship = rng.choice(dating_relationships)

                if relationship.is_active is False:
                    return None

                action = BreakUp(
                    character.gameobject,
                    relationship.get_component(Relationship).target,
                )
                utility = get_action_utility(action)

                if utility > 0:
                    potential_break_ups.append(action)
                    potential_break_up_scores.append(utility)

            if not potential_break_ups:
                continue

            action = rng.choices(potential_break_ups, potential_break_up_scores, k=1)[0]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class PregnancySystem(System):
    """Female characters in marriages have a chance of getting pregnant."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, _) in world.get_components((Character, Active)):
            if character.sex != Sex.FEMALE:
                continue

            if character.gameobject.has_component(Pregnant):
                continue

            marriages = get_relationships_with_traits(character.gameobject, "spouse")

            potential_pregnancies: list[GetPregnant] = []
            potential_pregnancy_scores: list[float] = []

            for relationship in marriages:
                partner = relationship.get_component(Relationship).target

                if partner.get_component(Character).sex != Sex.MALE:
                    continue

                if partner.is_active is False:
                    continue

                action = GetPregnant(character.gameobject, partner)
                utility = get_action_utility(action)

                if utility > 0:
                    potential_pregnancies.append(action)
                    potential_pregnancy_scores.append(utility)

            if not potential_pregnancies:
                continue

            action = rng.choices(
                potential_pregnancies, potential_pregnancy_scores, k=1
            )[0]

            probability_success = get_action_success_probability(action)

            if rng.random() < probability_success:
                action.on_success()
            else:
                action.on_failure()


class RetirementSystem(System):
    """Senior characters working a job can consider if they want to retire."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, _, _) in world.get_components(
            (Character, Occupation, Active)
        ):
            if character.life_stage < LifeStage.SENIOR:
                continue

            action = Retire(character.gameobject)

            utility_score = get_action_utility(action)

            if rng.random() < utility_score:

                probability_success = get_action_success_probability(action)

                if rng.random() < probability_success:
                    action.on_success()
                else:
                    action.on_failure()


class AdultsFindOwnResidenceSystem(System):
    """Adult characters who do not own their residence will attempt to find a new one.

    This system is mainly used for ensuring that children leave the residence when they
    become adults.
    """

    def on_update(self, world: World) -> None:
        for _, (character, resident, _) in world.get_components(
            (Character, Resident, Active)
        ):
            if character.life_stage < LifeStage.YOUNG_ADULT:
                continue

            owns_home = resident.residence.get_component(ResidentialUnit).is_owner(
                character.gameobject
            )

            if owns_home is False:
                vacant_housing = world.get_components((ResidentialUnit, Vacant))

                if vacant_housing:
                    _, (residence, _) = vacant_housing[0]
                    move_into_residence(
                        character.gameobject, residence.gameobject, is_owner=True
                    )


class CrushFormationSystem(System):
    """Every timestep there is a possibility that a character might form a new crush.

    This system is intended to assist with romantic depth within the simulation. It adds
    an additional layer of nuance to relationships since characters might form crushes
    on characters that they are not currently in a romantic relationship with.
    """

    def on_update(self, world: World) -> None:
        # 1) Loop through all the active characters
        # 2) Get their outgoing relationships
        # 3) Find the person that they have the highest romantic attraction to
        # 4) Run a probability check
        # 5) If successful, add a crush trait to the relationship and remove any
        #    existing crushes.

        rng = world.resources.get_resource(random.Random)

        for _, (_, relationships, _) in world.get_components(
            (Character, Relationships, Active)
        ):
            potential_crushes = sorted(
                [
                    (target, get_stat(rel, "romance").value)
                    for target, rel in relationships.outgoing.items()
                    if rel.get_component(Relationship).target.has_component(Character)
                ],
                key=lambda entry: entry[1],
            )

            if len(potential_crushes) == 0:
                continue

            # The person they are most attracted to is the last one in the sorted list
            crush = potential_crushes[-1][0]
            character = relationships.gameobject

            action = FormCrush(character, crush)

            utility_score = get_action_utility(action)

            if rng.random() < utility_score:

                probability_success = get_action_success_probability(action)

                if rng.random() < probability_success:
                    action.on_success()
                else:
                    action.on_failure()


def load_plugin(sim: Simulation) -> None:
    """Load systems into the simulation."""

    sim.world.systems.add_system(FindJobSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(FiredFromJobSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(JobPromotionSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(
        BecomeBusinessOwnerSystem(), system_group=UpdateSystems
    )
    sim.world.systems.add_system(CharacterDatingSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(CharacterMarriageSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(CharacterDivorceSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(DatingBreakUpSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(PregnancySystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(RetirementSystem(), system_group=UpdateSystems)
    sim.world.systems.add_system(
        AdultsFindOwnResidenceSystem(), system_group=UpdateSystems
    )
    sim.world.systems.add_system(CrushFormationSystem(), system_group=UpdateSystems)
