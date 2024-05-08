"""Action definitions.

"""

import random

from neighborly.action import Action
from neighborly.components.business import (
    Business,
    BusinessStatus,
    JobRole,
    Occupation,
    Unemployed,
)
from neighborly.components.character import Pregnant
from neighborly.components.relationship import Relationship
from neighborly.components.residence import (
    Resident,
    ResidentialBuilding,
    ResidentialUnit,
    Vacant,
)
from neighborly.components.settlement import District
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.events.defaults import BusinessClosedEvent, DeathEvent, LayOffEvent
from neighborly.helpers.action import get_action_success_probability, get_action_utility
from neighborly.helpers.location import (
    add_frequented_location,
    remove_all_frequented_locations,
    remove_all_frequenting_characters,
    remove_frequented_location,
)
from neighborly.helpers.relationship import deactivate_relationships, get_relationship
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import (
    add_relationship_trait,
    add_trait,
    get_relationships_with_traits,
    has_trait,
    remove_relationship_trait,
)
from neighborly.life_event import add_to_personal_history, dispatch_life_event
from neighborly.plugins.default_events import (
    DatingBreakUpEvent,
    DivorceEvent,
    FiredFromJobEvent,
    JobPromotionEvent,
    MarriageEvent,
    PregnancyEvent,
    RetirementEvent,
    StartBusinessEvent,
    StartDatingEvent,
    StartNewJobEvent,
)


class BecomeBusinessOwner(Action):
    """Character attempts to become the owner of a business."""

    __action_id__ = "become-business-owner"

    __slots__ = ("character", "business")

    character: GameObject
    business: GameObject

    def __init__(self, character: GameObject, business: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business

    def execute(self) -> None:
        owner_role = self.business.get_component(Business).owner_role
        business_component = self.business.get_component(Business)

        self.character.add_component(
            Occupation(
                business=self.business,
                start_date=self.world.resources.get_resource(SimDate).copy(),
                job_role=owner_role,
            )
        )

        add_frequented_location(self.character, self.business)

        business_component.set_owner(self.character)

        business_component.status = BusinessStatus.OPEN

        if self.character.has_component(Unemployed):
            self.character.remove_component(Unemployed)

        start_business_event = StartBusinessEvent(
            character=self.character,
            business=self.business,
        )

        add_to_personal_history(self.character, start_business_event)
        add_to_personal_history(self.business, start_business_event)
        dispatch_life_event(self.world, start_business_event)


class FormCrush(Action):
    """A character forms a crush on another."""

    __action_id__ = "form-crush"

    __slots__ = ("character", "crush")

    character: GameObject
    crush: GameObject

    def __init__(self, character: GameObject, crush: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.crush = crush

    def execute(self) -> None:
        for rel in get_relationships_with_traits(self.character, "crush"):
            relationship = rel.get_component(Relationship)

            remove_relationship_trait(relationship.owner, relationship.target, "crush")

        add_relationship_trait(self.character, self.crush, "crush")


class Retire(Action):
    """A character retires from their position at a business."""

    __action_id__ = "retire"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def execute(self) -> None:
        rng = self.world.resource_manager.get_resource(random.Random)

        occupation = self.character.get_component(Occupation)
        business = occupation.business
        business_data = business.get_component(Business)

        add_trait(self.character, "retired")
        event = RetirementEvent(self.character, business, occupation.job_role)
        add_to_personal_history(self.character, event)
        dispatch_life_event(
            self.world,
            event,
        )
        LeaveJob(business, self.character).execute()

        # If the character retiring is the owner of the business, try to find a
        # successor among the people they like. If none is found, lay everyone off and
        # close the business.
        if business.get_component(Business).owner == self.character:

            potential_successors: list[tuple[GameObject, float]] = sorted(
                [
                    (
                        employee,
                        get_stat(
                            get_relationship(self.character, employee), "reputation"
                        ).value,
                    )
                    for employee, _ in business_data.employees.items()
                ],
                key=lambda entry: entry[1],
            )

            if not potential_successors:
                return

            successor = potential_successors[-1][0]

            action = BecomeBusinessOwner(successor, business)

            utility_score = get_action_utility(action)

            if rng.random() < utility_score:

                probability_success = get_action_success_probability(action)

                if rng.random() < probability_success:
                    action.execute()


class GetPregnant(Action):
    """A character gets pregnant by another."""

    __action_id__ = "get-pregnant"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        due_date = self.world.resources.get_resource(SimDate).copy()
        due_date.increment(months=9)

        self.character.add_component(Pregnant(self.partner, due_date))

        event = PregnancyEvent(self.character, self.partner)
        add_to_personal_history(self.character, event)
        dispatch_life_event(self.world, event)


class BreakUp(Action):
    """A character stops dating another."""

    __action_id__ = "break-up"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        remove_relationship_trait(self.character, self.partner, "dating")
        remove_relationship_trait(self.partner, self.character, "dating")

        add_relationship_trait(self.character, self.partner, "ex_partner")
        add_relationship_trait(self.partner, self.character, "ex_partner")

        get_stat(
            get_relationship(self.partner, self.character), "romance"
        ).base_value -= 15

        event = DatingBreakUpEvent(self.character, self.partner)
        add_to_personal_history(self.character, event)
        add_to_personal_history(self.partner, event)
        dispatch_life_event(self.world, event)


class Divorce(Action):
    """A character stops being married another."""

    __action_id__ = "divorce"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        remove_relationship_trait(self.character, self.partner, "spouse")
        remove_relationship_trait(self.partner, self.character, "spouse")

        add_relationship_trait(self.character, self.partner, "ex_spouse")
        add_relationship_trait(self.partner, self.character, "ex_spouse")

        get_stat(
            get_relationship(self.partner, self.character), "romance"
        ).base_value -= 25

        event = DivorceEvent(self.character, self.partner)

        add_to_personal_history(self.character, event)
        add_to_personal_history(self.partner, event)
        dispatch_life_event(self.world, event)

        # initiator finds new place to live or departs
        vacant_housing = self.world.get_components((ResidentialUnit, Vacant))

        MoveOutOfResidence(self.character).execute()

        if vacant_housing:
            _, (residence, _) = vacant_housing[0]

            MoveIntoResidence(
                self.character, residence=residence.gameobject, is_owner=True
            ).execute()

        else:
            DepartSettlement(self.character).execute()


class GetMarried(Action):
    """A two characters get married."""

    __action_id__ = "get-married"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        remove_relationship_trait(self.character, self.partner, "dating")
        remove_relationship_trait(self.partner, self.character, "dating")

        add_relationship_trait(self.character, self.partner, "spouse")
        add_relationship_trait(self.partner, self.character, "spouse")

        # Update residences
        shared_residence = self.character.get_component(Resident).residence

        MoveIntoResidence(self.partner, shared_residence, is_owner=True).execute()

        for rel in get_relationships_with_traits(
            self.partner, "child", "live_together"
        ):
            target = rel.get_component(Relationship).target
            MoveIntoResidence(target, shared_residence).execute()

        # Update step sibling relationships
        for rel_0 in get_relationships_with_traits(self.character, "child"):
            if not rel_0.is_active:
                continue

            child_0 = rel_0.get_component(Relationship).target

            for rel_1 in get_relationships_with_traits(self.partner, "child"):
                if not rel_1.is_active:
                    continue

                child_1 = rel_1.get_component(Relationship).target

                add_relationship_trait(child_0, child_1, "step_sibling")
                add_relationship_trait(child_0, child_1, "sibling")
                add_relationship_trait(child_1, child_0, "step_sibling")
                add_relationship_trait(child_1, child_0, "sibling")

        # Update relationships parent/child relationships
        for rel in get_relationships_with_traits(self.character, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(self.partner, child), "child"):
                    add_relationship_trait(self.partner, child, "child")
                    add_relationship_trait(self.partner, child, "step_child")
                    add_relationship_trait(child, self.partner, "parent")
                    add_relationship_trait(child, self.partner, "step_parent")

        for rel in get_relationships_with_traits(self.partner, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(self.character, child), "child"):
                    add_relationship_trait(self.character, child, "child")
                    add_relationship_trait(self.character, child, "step_child")
                    add_relationship_trait(child, self.character, "parent")
                    add_relationship_trait(child, self.character, "step_parent")

        event = MarriageEvent(self.character, self.partner)

        add_to_personal_history(self.character, event)
        add_to_personal_history(self.partner, event)
        dispatch_life_event(self.world, event)


class StartDating(Action):
    """A character start dating another."""

    __action_id__ = "start-dating"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        add_relationship_trait(self.character, self.partner, "dating")
        add_relationship_trait(self.partner, self.character, "dating")

        event = StartDatingEvent(self.character, self.partner)

        add_to_personal_history(self.character, event)
        add_to_personal_history(self.partner, event)
        dispatch_life_event(self.world, event)


class HireEmployee(Action):
    """A business hires an employee."""

    __action_id__ = "fire-employee"

    __slots__ = ("business", "character", "role")

    business: GameObject
    character: GameObject
    role: JobRole

    def __init__(
        self, business: GameObject, character: GameObject, role: JobRole
    ) -> None:
        super().__init__(business.world)
        self.business = business
        self.character = character
        self.role = role

    def execute(self) -> None:
        business_comp = self.business.get_component(Business)

        current_date = self.world.resource_manager.get_resource(SimDate)

        self.character.add_component(
            Occupation(
                business=self.business,
                start_date=current_date,
                job_role=self.role,
            )
        )

        add_frequented_location(self.character, self.business)

        if self.character.has_component(Unemployed):
            self.character.remove_component(Unemployed)

        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            add_relationship_trait(self.character, business_comp.owner, "boss")
            add_relationship_trait(business_comp.owner, self.character, "employee")

        # Update employee/employee relationships
        for employee, _ in business_comp.employees.items():
            add_relationship_trait(self.character, employee, "coworker")
            add_relationship_trait(employee, self.character, "coworker")

        business_comp.add_employee(self.character, self.role)

        event = StartNewJobEvent(self.character, self.business, self.role)

        add_to_personal_history(self.character, event)
        dispatch_life_event(self.world, event)


class FireEmployee(Action):
    """A business owner fires an employee."""

    __action_id__ = "fire-employee"

    __slots__ = ("business", "character")

    business: GameObject
    character: GameObject

    def __init__(self, business: GameObject, character: GameObject) -> None:
        super().__init__(business.world)
        self.business = business
        self.character = character

    def execute(self) -> None:
        business = self.character.get_component(Occupation).business
        job_role = self.character.get_component(Occupation).job_role

        event = FiredFromJobEvent(self.character, business, job_role)

        dispatch_life_event(business.world, event)
        add_to_personal_history(self.character, event)

        LeaveJob(business, self.character).execute()

        business_data = business.get_component(Business)

        owner = business_data.owner
        if owner is not None:
            get_stat(
                get_relationship(self.character, owner), "reputation"
            ).base_value -= 20
            get_stat(
                get_relationship(owner, self.character), "reputation"
            ).base_value -= 10
            get_stat(
                get_relationship(self.character, owner), "romance"
            ).base_value -= 30


class PromoteEmployee(Action):
    """A business owner promotes an employee."""

    __action_id__ = "promote-employee"

    __slots__ = ("character", "employee", "role")

    character: GameObject
    employee: GameObject
    role: JobRole

    def __init__(
        self, character: GameObject, employee: GameObject, role: JobRole
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.employee = employee
        self.role = role

    def execute(self) -> None:
        business = self.character.get_component(Occupation).business
        business_data = business.get_component(Business)

        # Remove the old occupation
        self.character.remove_component(Occupation)

        business_data.remove_employee(self.character)

        # Add the new occupation
        self.character.add_component(
            Occupation(
                business=business,
                start_date=self.character.world.resource_manager.get_resource(SimDate),
                job_role=self.role,
            )
        )

        business_data.add_employee(self.character, self.role)

        event = JobPromotionEvent(self.character, business, self.role)

        add_to_personal_history(self.character, event)
        dispatch_life_event(self.character.world, event)


class LayOffEmployee(Action):
    """A business owner fires an employee."""

    __action_id__ = "lay-off-employee"

    __slots__ = ("business", "character")

    business: GameObject
    character: GameObject

    def __init__(self, business: GameObject, character: GameObject) -> None:
        super().__init__(business.world)
        self.business = business
        self.character = character

    def execute(self) -> None:

        current_date = self.world.resource_manager.get_resource(SimDate)

        business_comp = self.business.get_component(Business)

        remove_frequented_location(self.character, self.business)

        business_comp.remove_employee(self.character)

        # Update boss/employee relationships if needed
        owner = business_comp.owner
        if owner is not None:
            remove_relationship_trait(self.character, owner, "boss")
            remove_relationship_trait(owner, self.character, "employee")

        # Update coworker relationships
        for other_employee, _ in business_comp.employees.items():
            if other_employee == self.character:
                continue

            remove_relationship_trait(self.character, other_employee, "coworker")
            remove_relationship_trait(other_employee, self.character, "coworker")

        self.character.add_component(Unemployed(timestamp=current_date))

        job_role = self.character.get_component(Occupation).job_role

        self.character.remove_component(Occupation)

        event = LayOffEvent(self.character, self.business, job_role)

        add_to_personal_history(self.character, event)
        dispatch_life_event(self.world, event)


class LeaveJob(Action):
    """A business owner fires an employee."""

    __action_id__ = "leave-job-employee"

    __slots__ = ("business", "character")

    business: GameObject
    character: GameObject

    def __init__(self, business: GameObject, character: GameObject) -> None:
        super().__init__(business.world)
        self.business = business
        self.character = character

    def execute(self) -> None:

        current_date = self.world.resource_manager.get_resource(SimDate)

        business_comp = self.business.get_component(Business)

        remove_frequented_location(self.character, self.business)

        if self.character == business_comp.owner:
            business_comp.set_owner(None)

            # Update relationships boss/employee relationships
            for employee, _ in business_comp.employees.items():
                remove_relationship_trait(self.character, employee, "employee")
                remove_relationship_trait(employee, self.character, "boss")

        else:
            business_comp.remove_employee(self.character)

            # Update boss/employee relationships if needed
            owner = business_comp.owner
            if owner is not None:
                remove_relationship_trait(self.character, owner, "boss")
                remove_relationship_trait(owner, self.character, "employee")

            # Update coworker relationships
            for other_employee, _ in business_comp.employees.items():
                if other_employee == self.character:
                    continue

                remove_relationship_trait(self.character, other_employee, "coworker")
                remove_relationship_trait(other_employee, self.character, "coworker")

        self.character.add_component(Unemployed(timestamp=current_date))
        self.character.remove_component(Occupation)


class CloseBusiness(Action):
    """Permanently close a business."""

    __action_id__ = "close-business"

    __slots__ = ("business",)

    business: GameObject

    def __init__(self, business: GameObject) -> None:
        super().__init__(business.world)
        self.business = business

    def execute(self) -> None:

        business_comp = self.business.get_component(Business)

        # Update the business as no longer active
        business_comp.status = BusinessStatus.CLOSED

        # Remove all the employees
        for employee, _ in [*business_comp.employees.items()]:
            LayOffEmployee(self.business, employee).execute()

        # Remove the owner if applicable
        if business_comp.owner is not None:
            LeaveJob(self.business, business_comp.owner).execute()

        # Decrement the number of this type
        if business_comp.district:
            business_comp.district.get_component(BusinessSpawnTable).decrement_count(
                self.business.metadata["definition_id"]
            )
            business_comp.district.get_component(District).remove_business(
                self.business
            )

        # Remove any other characters that frequent the location
        remove_all_frequenting_characters(self.business)

        # Un-mark the business as active so it doesn't appear in queries
        self.business.deactivate()

        event = BusinessClosedEvent(self.business)

        add_to_personal_history(self.business, event)
        dispatch_life_event(self.world, event)


class Die(Action):
    """A character dies."""

    __action_id__ = "die"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def execute(self) -> None:
        """Have a character die."""

        death_event = DeathEvent(self.character)

        add_to_personal_history(self.character, death_event)
        dispatch_life_event(self.world, death_event)

        self.character.deactivate()

        remove_all_frequented_locations(self.character)

        add_trait(self.character, "deceased")

        deactivate_relationships(self.character)

        MoveOutOfResidence(self.character).execute()

        # Remove the character from their residence
        if resident_data := self.character.try_component(Resident):
            residence = resident_data.residence
            MoveOutOfResidence(self.character).execute()

            # If there are no-more residents that are owner's remove everyone from
            # the residence and have them depart the simulation.
            residence_data = residence.get_component(ResidentialUnit)
            if len(list(residence_data.owners)) == 0:
                residents = list(residence_data.residents)
                for resident in residents:
                    DepartSettlement(resident).execute()

        # Adjust relationships
        for rel in get_relationships_with_traits(self.character, "dating"):
            target = rel.get_component(Relationship).target

            remove_relationship_trait(target, self.character, "dating")
            remove_relationship_trait(self.character, target, "dating")
            add_relationship_trait(target, self.character, "ex_partner")
            add_relationship_trait(self.character, target, "ex_partner")

        for rel in get_relationships_with_traits(self.character, "spouse"):
            target = rel.get_component(Relationship).target

            remove_relationship_trait(self.character, target, "spouse")
            remove_relationship_trait(target, self.character, "spouse")
            add_relationship_trait(target, self.character, "ex_spouse")
            add_relationship_trait(self.character, target, "ex_spouse")
            add_relationship_trait(target, self.character, "widow")

        # Remove the character from their occupation
        if occupation := self.character.try_component(Occupation):
            LeaveJob(occupation.business, self.character).execute()


class MoveOutOfResidence(Action):
    """A character moves out of a residence."""

    __action_id__ = "move-out-of-residence"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def execute(self) -> None:
        """Have the character move out of their current residence."""

        if resident := self.character.try_component(Resident):
            # This character is currently a resident at another location
            former_residence = resident.residence
            former_residence_comp = former_residence.get_component(ResidentialUnit)

            for resident in former_residence_comp.residents:
                if resident == self.character:
                    continue

                add_relationship_trait(self.character, resident, "live_together")
                add_relationship_trait(resident, self.character, "live_together")

            if former_residence_comp.is_owner(self.character):
                former_residence_comp.remove_owner(self.character)

            former_residence_comp.remove_resident(self.character)
            self.character.remove_component(Resident)

            remove_frequented_location(self.character, former_residence)

            former_district = (
                former_residence.get_component(ResidentialUnit)
                .building.get_component(ResidentialBuilding)
                .district
            )

            if former_district:
                former_district.get_component(District).population -= 1

            if len(former_residence_comp) <= 0:
                former_residence.add_component(Vacant())


class MoveIntoResidence(Action):
    """A character moves into a new residence."""

    __action_id__ = "move-into-residence"

    __slots__ = ("character", "residence", "is_owner")

    character: GameObject
    residence: GameObject
    is_owner: bool

    def __init__(
        self, character: GameObject, residence: GameObject, is_owner: bool = False
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.residence = residence
        self.is_owner = is_owner

    def execute(self) -> None:
        """Have the character move into a new residence."""

        if self.character.has_component(Resident):
            MoveOutOfResidence(self.character).execute()

        self.residence.get_component(ResidentialUnit).add_resident(self.character)

        if self.is_owner:
            self.residence.get_component(ResidentialUnit).add_owner(self.character)

        self.character.add_component(Resident(residence=self.residence))

        add_frequented_location(self.character, self.residence)

        if self.residence.has_component(Vacant):
            self.residence.remove_component(Vacant)

        for resident in self.residence.get_component(ResidentialUnit).residents:
            if resident == self.character:
                continue

            add_relationship_trait(self.character, resident, "live_together")
            add_relationship_trait(resident, self.character, "live_together")

        new_district = (
            self.residence.get_component(ResidentialUnit)
            .building.get_component(ResidentialBuilding)
            .district
        )

        if new_district:
            new_district.get_component(District).population += 1
        else:
            raise RuntimeError("Residential building is missing district.")


class DepartSettlement(Action):
    """A character departs from the settlement and simulation."""

    __action_id__ = "depart-settlement"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def execute(self) -> None:
        """Have the given character depart the settlement."""

        remove_all_frequented_locations(self.character)
        add_trait(self.character, "departed")
        self.character.deactivate()

        deactivate_relationships(self.character)

        # Have the character leave their job
        if occupation := self.character.try_component(Occupation):
            if occupation.business.get_component(Business).owner == self.character:
                CloseBusiness(occupation.business).execute()
            else:
                LeaveJob(occupation.business, self.character).execute()

        # Have the character leave their residence
        if resident_data := self.character.try_component(Resident):
            residence_data = resident_data.residence.get_component(ResidentialUnit)
            MoveOutOfResidence(self.character).execute()

            # Get people that this character lives with and have them depart with their
            # spouse(s) and children. This function may need to be refactored in the future
            # to perform BFS on the relationship tree when moving out extended families
            # living within the same residence
            for resident in list(residence_data.residents):
                if resident == self.character:
                    continue

                rel_to_resident = get_relationship(self.character, resident)

                if has_trait(rel_to_resident, "spouse") and not has_trait(
                    resident, "departed"
                ):
                    DepartSettlement(resident).execute()

                elif has_trait(rel_to_resident, "child") and not has_trait(
                    resident, "departed"
                ):
                    DepartSettlement(resident).execute()
