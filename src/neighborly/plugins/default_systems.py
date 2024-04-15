"""Default systems to include into a simulation.

"""

import random
from typing import cast

from repraxis.query import DBQuery

from neighborly.components.business import (
    Business,
    BusinessStatus,
    Occupation,
    Unemployed,
)
from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import Relationship
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.datetime import SimDate
from neighborly.defs.base_types import JobRoleDef
from neighborly.ecs import Active, System, World
from neighborly.events.defaults import LeaveJobEvent
from neighborly.helpers.business import add_employee, close_business, fire_employee
from neighborly.helpers.character import (
    depart_settlement,
    move_into_residence,
    move_out_of_residence,
)
from neighborly.helpers.db_helpers import preprocess_query_string
from neighborly.helpers.location import add_frequented_location
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import (
    add_trait,
    get_relationships_with_traits,
    has_trait,
    remove_trait,
)
from neighborly.libraries import JobRoleLibrary
from neighborly.life_event import (
    LifeEvent,
    add_to_personal_history,
    dispatch_life_event,
)
from neighborly.plugins.default_events import (
    FiredFromJobEvent,
    JobPromotionEvent,
    StartBusinessEvent,
)


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
                    job_role = library.get_definition(role_id)

                    for rule in job_role.requirements:

                        query_lines = preprocess_query_string(rule)

                        result = DBQuery(query_lines).run(
                            character.world.rp_db,
                            bindings=[{"?character": character.uid}],
                        )

                        if result.success:
                            add_employee(business.gameobject, character, job_role)


class FiredFromJobSystem(System):
    """Occasionally fire an employee or two."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (_, occupation, _) in world.get_components(
            (Character, Occupation, Active)
        ):
            # Characters can't fire themselves
            if (
                occupation.business.get_component(Business).owner
                == occupation.gameobject
            ):
                continue

            # Lets just say there is a 20% chance a character gets fired.
            # TODO: Add considerations to modify this probability.
            if rng.random() < 0.2:
                fire_employee(occupation.business, occupation.gameobject)


class JobPromotionSystem(System):
    """Occasionally promote characters to higher positions at their jobs."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        for _, (_, occupation, _) in world.get_components(
            (Character, Occupation, Active)
        ):
            character = occupation.gameobject

            current_job_level = occupation.job_role.job_level
            business_data = occupation.business.get_component(Business)
            open_positions = business_data.get_open_positions()

            # Business owners can't promote themselves
            if business_data.owner == character:
                return None

            higher_positions: list[JobRoleDef] = []

            for role_id in open_positions:
                role = job_role_library.get_definition(role_id)

                if current_job_level >= role.job_level:
                    continue

                for rule in role.requirements:

                    query_lines = preprocess_query_string(rule)

                    result = DBQuery(query_lines).run(
                        world.rp_db, bindings=[{"?character": character.uid}]
                    )
                    if result.success:
                        higher_positions.append(role)
                        break

            if len(higher_positions) == 0:
                return None

            chosen_role = rng.choice(higher_positions)

            return JobPromotionEvent(
                character=character,
                business=business_data.gameobject,
                old_role=occupation.job_role,
                new_role=chosen_role,
            )


class StartBusinessSystem(System):
    """Characters have a chance of starting a business on a given timestep."""

    def on_update(self, world: World) -> None:

        rng = world.resource_manager.get_resource(random.Random)

        pending_businesses = [
            business
            for _, (business, _) in world.get_components((Business, Active))
            if business.status == BusinessStatus.PENDING
        ]

        for _, (character, _) in world.get_components((Character, Active)):

            # Only adults can start businesses
            if character.life_stage < LifeStage.ADOLESCENT:
                continue

            # Only unemployed characters can start businesses
            if character.gameobject.has_component(Occupation):
                continue

            eligible_businesses: list[tuple[Business, JobRoleDef]] = []

            for business in pending_businesses:
                if business.owner is not None:
                    continue

                owner_role = business.owner_role

                for rule in owner_role.requirements:
                    query_lines = preprocess_query_string(rule)
                    result = DBQuery(query_lines).run(
                        world.rp_db, bindings=[{"?character": character.gameobject.uid}]
                    )

                    if result.success:
                        eligible_businesses.append((business, owner_role))
                        break

            if not eligible_businesses:
                continue

            chosen_business, owner_role = rng.choice(eligible_businesses)

            character.gameobject.add_component(
                Occupation(
                    character.gameobject,
                    business=chosen_business.gameobject,
                    start_date=world.resources.get_resource(SimDate).copy(),
                    job_role=owner_role,
                )
            )

            add_frequented_location(character.gameobject, chosen_business.gameobject)

            chosen_business.set_owner(character.gameobject)

            chosen_business.status = BusinessStatus.OPEN

            if character.gameobject.has_component(Unemployed):
                character.gameobject.remove_component(Unemployed)

            start_business_event = StartBusinessEvent(
                character=character.gameobject,
                business=chosen_business.gameobject,
            )

            add_to_personal_history(character.gameobject, start_business_event)
            add_to_personal_history(chosen_business.gameobject, start_business_event)
            dispatch_life_event(world, start_business_event)

    def handle_owner_leaving(self, event: LifeEvent) -> None:
        """Event listener placed on the business owners to track when they leave."""

        leave_job_event = cast(LeaveJobEvent, event)
        close_business(leave_job_event.business)


class CharacterDatingSystem(System):

    def on_update(self, world: World) -> None:
        if character.get_component(Character).life_stage <= LifeStage.ADOLESCENT:
            return None

        if len(get_relationships_with_traits(character, "dating")) > 0:
            return None

        relationships = list(character.get_component(Relationships).outgoing.items())

        potential_partners: list[GameObject] = []
        partner_weights: list[float] = []

        for target, relationship in relationships:
            if target.get_component(Character).life_stage <= LifeStage.ADOLESCENT:
                continue

            if target.is_active is False:
                continue

            romance = get_stat(relationship, "romance").normalized

            if romance > 0:
                potential_partners.append(target)
                partner_weights.append(romance)

        if potential_partners:
            rng = character.world.resource_manager.get_resource(random.Random)

            chosen_partner = rng.choices(
                potential_partners, weights=partner_weights, k=1
            )[0]

            return StartDating(
                character=character,
                partner=chosen_partner,
            )

        add_trait(get_relationship(character_0, partner), "dating")
        add_trait(get_relationship(partner, character_0), "dating")

        return None


class CharacterMarriageSystem(System):

    def on_update(self, world: World) -> None:
        character_life_stage = character.get_component(Character).life_stage

        if character_life_stage < LifeStage.YOUNG_ADULT:
            return None

        if len(get_relationships_with_traits(character, "spouse")) > 0:
            return None

        dating_relationships = get_relationships_with_traits(character, "dating")

        rng = character.world.resource_manager.get_resource(random.Random)
        rng.shuffle(dating_relationships)

        for relationship in dating_relationships:
            partner = relationship.get_component(Relationship).target

            if partner.get_component(Character).life_stage < LifeStage.YOUNG_ADULT:
                continue

            if partner.is_active is False:
                continue

            return GetMarried(character=character, partner=partner)

        # Code executed on success
        character_0, character_1 = self.roles.get_all("character")

        remove_trait(get_relationship(character_0, character_1), "dating")
        remove_trait(get_relationship(character_1, character_0), "dating")

        add_trait(get_relationship(character_0, character_1), "spouse")
        add_trait(get_relationship(character_1, character_0), "spouse")

        # Update residences
        shared_residence = character_0.get_component(Resident).residence

        ChangeResidenceEvent(character_1, new_residence=shared_residence, is_owner=True)

        for rel in get_relationships_with_traits(character_1, "child", "live_together"):
            target = rel.get_component(Relationship).target
            ChangeResidenceEvent(target, new_residence=shared_residence)

        # Update step sibling relationships
        for rel_0 in get_relationships_with_traits(character_0, "child"):
            if not rel_0.is_active:
                continue

            child_0 = rel_0.get_component(Relationship).target

            for rel_1 in get_relationships_with_traits(character_1, "child"):
                if not rel_1.is_active:
                    continue

                child_1 = rel_1.get_component(Relationship).target

                add_trait(get_relationship(child_0, child_1), "step_sibling")
                add_trait(get_relationship(child_0, child_1), "sibling")
                add_trait(get_relationship(child_1, child_0), "step_sibling")
                add_trait(get_relationship(child_1, child_0), "sibling")

        # Update relationships parent/child relationships
        for rel in get_relationships_with_traits(character_0, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(character_1, child), "child"):
                    add_trait(get_relationship(character_1, child), "child")
                    add_trait(get_relationship(character_1, child), "step_child")
                    add_trait(get_relationship(child, character_1), "parent")
                    add_trait(get_relationship(child, character_1), "step_parent")

        for rel in get_relationships_with_traits(character_1, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(character_0, child), "child"):
                    add_trait(get_relationship(character_0, child), "child")
                    add_trait(get_relationship(character_0, child), "step_child")
                    add_trait(get_relationship(child, character_0), "parent")
                    add_trait(get_relationship(child, character_0), "step_parent")


class CharacterDivorceSystem(System):

    def on_update(self, world: World) -> None:
        spousal_relationships = get_relationships_with_traits(character, "spouse")

        rng = character.world.resource_manager.get_resource(random.Random)

        rng.shuffle(spousal_relationships)

        for relationship in spousal_relationships:
            if not relationship.has_component(Active):
                continue

            partner = relationship.get_component(Relationship).target

            if partner.is_active is False:
                continue

            return GetDivorced(character=character, ex_spouse=partner)

        # Code executed on success
        initiator = self.roles["character"]
        ex_spouse = self.roles["ex_spouse"]

        remove_trait(get_relationship(initiator, ex_spouse), "spouse")
        remove_trait(get_relationship(ex_spouse, initiator), "spouse")

        add_trait(get_relationship(initiator, ex_spouse), "ex_spouse")
        add_trait(get_relationship(ex_spouse, initiator), "ex_spouse")

        get_stat(get_relationship(ex_spouse, initiator), "romance").base_value -= 25

        # initiator finds new place to live or departs
        vacant_housing = initiator.world.get_components((ResidentialUnit, Vacant))

        if vacant_housing:
            _, (residence, _) = vacant_housing[0]
            ChangeResidenceEvent(
                initiator, new_residence=residence.gameobject, is_owner=True
            )

        else:
            ChangeResidenceEvent(initiator, new_residence=None)
            DepartSettlementEvent(initiator)


class DatingBreakUpSystem(System):

    def on_update(self, world: World) -> None:
        dating_relationships = get_relationships_with_traits(character, "dating")

        rng = character.world.resource_manager.get_resource(random.Random)

        if dating_relationships:
            relationship = rng.choice(dating_relationships)

            if relationship.is_active is False:
                return None

            return BreakUp(
                character=character,
                ex_partner=relationship.get_component(Relationship).target,
            )

        # Success Code
        initiator = self.roles["character"]
        ex_partner = self.roles["ex_partner"]

        remove_trait(get_relationship(initiator, ex_partner), "dating")
        remove_trait(get_relationship(ex_partner, initiator), "dating")

        add_trait(get_relationship(initiator, ex_partner), "ex_partner")
        add_trait(get_relationship(ex_partner, initiator), "ex_partner")

        get_stat(get_relationship(ex_partner, initiator), "romance").base_value -= 15


class PregnancySystem(System):

    def on_update(self, world: World) -> None:
        marriages = get_relationships_with_traits(character, "spouse")

        for relationship in marriages:
            partner = relationship.get_component(Relationship).target

            if partner.get_component(Character).sex != Sex.MALE:
                continue

            if partner.is_active is False:
                continue

            return PregnancyEvent(character=character, partner=partner)

        due_date = self.world.resource_manager.get_resource(SimDate).copy()
        due_date.increment(months=9)

        character.add_component(Pregnant(character, partner=partner, due_date=due_date))


class RetirementSystem(System):
    """Senior characters working a job can consider if they want to retire."""

    def on_update(self, world: World) -> None:

        rng = world.resources.get_resource(random.Random)

        for _, (character, occupation, _) in world.get_components(
            (Character, Occupation, Active)
        ):

            if character.life_stage < LifeStage.SENIOR:
                continue

            if rng.random() > 0.4:
                continue

            add_trait(character.gameobject, "retired")

            business = occupation.business

            if business.get_component(Business).owner == character:
                # Try to find a successor
                business_data = business.get_component(Business)

                potential_successions: list[PromotedToBusinessOwner] = []
                succession_scores: list[float] = []

                for employee, _ in business_data.employees.items():
                    succession = PromotedToBusinessOwner(
                        character=employee, business=business, former_owner=character
                    )
                    succession_score = succession.get_probability()

                    if succession_score >= 0.6:
                        potential_successions.append(succession)
                        succession_scores.append(succession_score)

                if potential_successions:
                    rng = character.world.resource_manager.get_resource(random.Random)
                    chosen_succession = rng.choices(
                        population=potential_successions, weights=succession_scores, k=1
                    )[0]

                    LeaveJobEvent(
                        character=character,
                        business=business,
                        job_role=self.job_role,
                        reason="retired",
                    )
                    chosen_succession
                    return

                # Could not find suitable successors. Just leave and lay people off.
                LeaveJobEvent(
                    character=character,
                    business=business,
                    job_role=self.job_role,
                    reason="retired",
                )
                BusinessClosedEvent(character, business, "owner retired")
                return

            # This is an employee. Keep the business running as usual
            LeaveJobEvent(
                character=character, business=business, job_role=self.job_role
            )

            return RetirementEvent(
                character=character,
                business=occupation.business,
                job_role=occupation.job_role,
            )


class ChildMoveOutSystem(System):

    def on_update(self, world: World) -> None:
        for _, (character, _) in world.get_components((Character, Active)):

            if character.life_stage < LifeStage.YOUNG_ADULT:
                return None

            parents_they_live_with = get_relationships_with_traits(
                character.gameobject, "parent", "live_together"
            )
            owns_home = False

            if resident := character.gameobject.try_component(Resident):
                owns_home = resident.residence.get_component(ResidentialUnit).is_owner(
                    character.gameobject
                )

            if len(parents_they_live_with) > 0 and owns_home is False:
                vacant_housing = world.get_components((ResidentialUnit, Vacant))

                if vacant_housing:
                    _, (residence, _) = vacant_housing[0]
                    move_into_residence(
                        character.gameobject, residence.gameobject, is_owner=True
                    )

                else:
                    move_out_of_residence(character.gameobject)
                    depart_settlement(character.gameobject)


class CrushFormationSystem(System):

    def on_update(self, world: World) -> None:
        for _, (relationship, _) in world.get_components((Relationship, Active)):
            owner = relationship.owner
            target = relationship.target

            if not target.has_component(Character):
                continue

            if not owner.has_component(Character):
                continue

            rng = world.resources.get_resource(random.Random)

            romance = get_stat(relationship.gameobject, "romance")

            probability = 0
            if romance.value > 90:
                probability = 0.9
            elif romance.value > 70:
                probability = 0.7
            elif romance.value > 50:
                probability = 0.5

            # TODO: This calculation should take other factors into consideration.
            if rng.random() < probability:

                for rel in get_relationships_with_traits(owner, "crush"):
                    remove_trait(rel, "crush")

                add_trait(get_relationship(owner, target), "crush")
