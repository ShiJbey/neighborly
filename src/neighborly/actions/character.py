"""Character Action Definitions.

"""

from typing import Optional, cast

from neighborly.actions.base_types import Action, ActionInstance
from neighborly.components.business import Business, Occupation
from neighborly.components.relationship import Relationship
from neighborly.components.residence import Resident, ResidentialUnit, Vacant
from neighborly.components.settlement import District
from neighborly.ecs import GameObject, World
from neighborly.events.defaults import BusinessClosedEvent
from neighborly.helpers.location import remove_all_frequented_locations
from neighborly.helpers.relationship import (
    deactivate_relationships,
    get_relationship,
    get_relationships_with_traits,
)
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.plugins.default_events import BecomeBusinessOwnerEvent


def die_action_definition() -> Action:
    """Create die action definition"""

    def on_execute(world: World, instance: ActionInstance) -> bool:
        character = world.gameobjects.get_gameobject(
            cast(int, instance.bindings["?agent"])
        )

        remove_all_frequented_locations(character)
        character.deactivate()

        add_trait(character, "deceased")

        deactivate_relationships(character)

        # Remove the character from their residence
        if resident_data := character.try_component(Resident):
            residence = resident_data.residence
            change_residence(character, new_residence=None)

            # If there are no-more residents that are owner's remove everyone from
            # the residence and have them depart the simulation.
            residence_data = residence.get_component(ResidentialUnit)
            if len(list(residence_data.owners)) == 0:
                residents = list(residence_data.residents)
                for resident in residents:
                    depart_settlement(resident, "death in family")

        # Adjust relationships
        for rel in get_relationships_with_traits(character, "dating"):
            target = rel.get_component(Relationship).target

            remove_trait(rel, "dating")
            remove_trait(get_relationship(target, character), "dating")

            add_trait(rel, "ex_partner")
            add_trait(get_relationship(target, character), "ex_partner")

        for rel in get_relationships_with_traits(character, "spouse"):
            target = rel.get_component(Relationship).target

            remove_trait(rel, "spouse")
            remove_trait(get_relationship(target, character), "spouse")

            add_trait(rel, "ex_spouse")
            add_trait(get_relationship(target, character), "ex_spouse")

            add_trait(rel, "widow")

        # Remove the character from their occupation
        if occupation := character.try_component(Occupation):
            leave_job(
                subject=character,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
                reason="died",
            )

        return True

    return Action(
        action_id="die",
        agent_type="character",
        on_execute=on_execute,
    )


def die(character: GameObject) -> None:
    """Have the character dies"""

    action: ActionInstance = instantiate_action("die", character)
    action.execute(character.world)


def depart_settlement(character: GameObject) -> None:
    remove_all_frequented_locations(character)
    add_trait(character, "departed")
    character.deactivate()

    deactivate_relationships(character)

    # Have the character leave their job
    if occupation := character.try_component(Occupation):  # type: ignore
        if occupation.business.get_component(Business).owner == character:
            BusinessClosedEvent(subject=character, business=occupation.business)
        else:
            leave_job(
                subject=character,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
                reason="departed settlement",
            )

    # Have the character leave their residence
    if resident_data := character.try_component(Resident):
        residence_data = resident_data.residence.get_component(ResidentialUnit)
        ChangeResidenceEvent(subject=character, new_residence=None)

        # Get people that this character lives with and have them depart with their
        # spouse(s) and children. This function may need to be refactored in the future
        # to perform BFS on the relationship tree when moving out extended families
        # living within the same residence
        for resident in list(residence_data.residents):
            if resident == character:
                continue

            rel_to_resident = get_relationship(character, resident)

            if has_trait(rel_to_resident, "spouse") and not has_trait(
                resident, "departed"
            ):
                DepartSettlement(resident)

            elif has_trait(rel_to_resident, "child") and not has_trait(
                resident, "departed"
            ):
                DepartSettlement(resident)


def try_to_find_own_place(subject: GameObject) -> None:

    vacant_housing = subject.world.get_components((ResidentialUnit, Vacant))

    if vacant_housing:
        _, (residence, _) = vacant_housing[0]
        ChangeResidenceEvent(subject, new_residence=residence.gameobject, is_owner=True)

    else:
        ChangeResidenceEvent(subject, new_residence=None)
        DepartSettlement(subject)


def get_married(subject_0: GameObject, subject_1: GameObject) -> None:

    remove_trait(get_relationship(subject_0, subject_1), "dating")
    remove_trait(get_relationship(subject_1, subject_0), "dating")

    add_trait(get_relationship(subject_0, subject_1), "spouse")
    add_trait(get_relationship(subject_1, subject_0), "spouse")

    # Update residences
    shared_residence = subject_0.get_component(Resident).residence

    ChangeResidenceEvent(subject_1, new_residence=shared_residence, is_owner=True)

    for rel in get_relationships_with_traits(subject_1, "child", "live_together"):
        target = rel.get_component(Relationship).target
        ChangeResidenceEvent(target, new_residence=shared_residence)

    # Update step sibling relationships
    for rel_0 in get_relationships_with_traits(subject_0, "child"):
        if not rel_0.is_active:
            continue

        child_0 = rel_0.get_component(Relationship).target

        for rel_1 in get_relationships_with_traits(subject_1, "child"):
            if not rel_1.is_active:
                continue

            child_1 = rel_1.get_component(Relationship).target

            add_trait(get_relationship(child_0, child_1), "step_sibling")
            add_trait(get_relationship(child_0, child_1), "sibling")
            add_trait(get_relationship(child_1, child_0), "step_sibling")
            add_trait(get_relationship(child_1, child_0), "sibling")

    # Update relationships parent/child relationships
    for rel in get_relationships_with_traits(subject_0, "child"):
        if rel.is_active:
            child = rel.get_component(Relationship).target
            if not has_trait(get_relationship(subject_1, child), "child"):
                add_trait(get_relationship(subject_1, child), "child")
                add_trait(get_relationship(subject_1, child), "step_child")
                add_trait(get_relationship(child, subject_1), "parent")
                add_trait(get_relationship(child, subject_1), "step_parent")

    for rel in get_relationships_with_traits(subject_1, "child"):
        if rel.is_active:
            child = rel.get_component(Relationship).target
            if not has_trait(get_relationship(subject_0, child), "child"):
                add_trait(get_relationship(subject_0, child), "child")
                add_trait(get_relationship(subject_0, child), "step_child")
                add_trait(get_relationship(child, subject_0), "parent")
                add_trait(get_relationship(child, subject_0), "step_parent")


def form_crush(subject: GameObject, other: GameObject) -> None:
    # remove existing crushes
    for rel in get_relationships_with_traits(subject, "crush"):
        remove_trait(rel, "crush")

    add_trait(get_relationship(subject, other), "crush")


def retire_from_job(
    subject: GameObject, business: GameObject, job_role: GameObject
) -> None:

    add_trait(subject, "retired")

    if business.get_component(Business).owner == subject:
        # Try to find a successor
        business_data = business.get_component(Business)

        potential_successions: list[BecomeBusinessOwnerEvent] = []
        succession_scores: list[float] = []

        for employee, _ in business_data.employees.items():
            succession = BecomeBusinessOwnerEvent(
                subject=employee, business=business, former_owner=subject
            )
            succession_score = succession.get_probability()

            if succession_score >= 0.6:
                potential_successions.append(succession)
                succession_scores.append(succession_score)

        if potential_successions:
            rng = subject.world.rng
            chosen_succession = rng.choices(
                population=potential_successions, weights=succession_scores, k=1
            )[0]

            LeaveJob(
                subject=subject,
                business=business,
                job_role=job_role,
                reason="retired",
            )
            chosen_succession
            return

        # Could not find suitable successors. Just leave and lay people off.
        leave_job(
            subject=subject,
            business=business,
            job_role=job_role,
            reason="retired",
        )
        go_out_of_business(subject, business, "owner retired")
        return

    # This is an employee. Keep the business running as usual
    leave_job(subject=subject, business=business, job_role=job_role)


def become_friends(subject: GameObject, other: GameObject) -> None:
    add_trait(get_relationship(subject, other), "friend")
    add_trait(get_relationship(other, subject), "friend")


def change_residence(
    character: GameObject, new_residence: Optional[GameObject], is_owner: bool = False
):

    if resident := character.try_component(Resident):
        # This character is currently a resident at another location
        former_residence = resident.residence
        former_residence_comp = former_residence.get_component(ResidentialUnit)

        for resident in former_residence_comp.residents:
            if resident == character:
                continue

            remove_trait(get_relationship(character, resident), "live_together")
            remove_trait(get_relationship(resident, character), "live_together")

        if former_residence_comp.is_owner(character):
            former_residence_comp.remove_owner(character)

        former_residence_comp.remove_resident(character)
        character.remove_component(Resident)

        former_district = former_residence.get_component(
            ResidentialUnit
        ).district.get_component(District)
        former_district.population -= 1

        if len(former_residence_comp) <= 0:
            former_residence.add_component(Vacant())

    # Don't add them to a new residence if none is given
    if new_residence is None:
        return

    # Move into new residence
    new_residence.get_component(ResidentialUnit).add_resident(character)

    if is_owner:
        new_residence.get_component(ResidentialUnit).add_owner(character)

    character.add_component(Resident(residence=new_residence))

    if new_residence.has_component(Vacant):
        new_residence.remove_component(Vacant)

    for resident in new_residence.get_component(ResidentialUnit).residents:
        if resident == character:
            continue

        add_trait(get_relationship(character, resident), "live_together")
        add_trait(get_relationship(resident, character), "live_together")

    new_district = new_residence.get_component(ResidentialUnit).district.get_component(
        District
    )

    new_district.population += 1


class BreakUp:

    initiator: GameObject
    ex_partner: GameObject

    def on_execute(self):
        remove_trait(get_relationship(self.initiator, self.ex_partner), "dating")
        remove_trait(get_relationship(self.ex_partner, self.initiator), "dating")

        add_trait(get_relationship(self.initiator, self.ex_partner), "ex_partner")
        add_trait(get_relationship(self.ex_partner, self.initiator), "ex_partner")

        get_stat(
            get_relationship(self.ex_partner, self.initiator), "romance"
        ).base_value -= 15


class Divorce:

    initiator: GameObject
    ex_spouse: GameObject

    def on_execute(self) -> None:
        remove_trait(get_relationship(self.initiator, self.ex_spouse), "spouse")
        remove_trait(get_relationship(self.ex_spouse, self.initiator), "spouse")

        add_trait(get_relationship(self.initiator, self.ex_spouse), "ex_spouse")
        add_trait(get_relationship(self.ex_spouse, self.initiator), "ex_spouse")

        get_stat(
            get_relationship(self.ex_spouse, self.initiator), "romance"
        ).base_value -= 25

        # initiator finds new place to live or departs
        vacant_housing = self.initiator.world.get_components((ResidentialUnit, Vacant))

        if vacant_housing:
            # _, (residence, _) = vacant_housing[0]
            # ChangeResidence(
            #     self.initiator, new_residence=residence.gameobject, is_owner=True
            # )
            pass

        else:
            # ChangeResidence(initiator, new_residence=None).execute()
            # DepartSettlement(initiator).execute()
            pass


class StartDating:
    """Event dispatched when two characters start dating."""

    subject: GameObject
    partner: GameObject

    def on_execute(self) -> None:
        add_trait(get_relationship(self.subject, self.partner), "dating")
        add_trait(get_relationship(self.partner, self.subject), "dating")
