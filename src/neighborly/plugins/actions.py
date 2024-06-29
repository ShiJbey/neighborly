"""Action definitions.

"""

import random
from typing import Optional

from neighborly.action import Action
from neighborly.components.business import Business, BusinessStatus, JobRole, Occupation
from neighborly.components.character import (
    Character,
    Household,
    MemberOfHousehold,
    Pregnant,
    ResidentOf,
)
from neighborly.components.location import CurrentDistrict
from neighborly.components.relationship import Relationship
from neighborly.components.settlement import District, Settlement
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.ecs import Event, GameObject
from neighborly.events.defaults import (
    BusinessClosedEvent,
    DeathEvent,
    DepartSettlementEvent,
    LayOffEvent,
    LeaveJobEvent,
)
from neighborly.helpers.action import get_action_probability
from neighborly.helpers.business import (
    add_employee,
    create_business,
    remove_employee,
    set_business_owner,
    set_business_status,
)
from neighborly.helpers.character import (
    add_character_to_household,
    create_household,
    remove_character_from_household,
    set_character_name,
    set_household_head,
)
from neighborly.helpers.location import (
    add_frequented_location,
    remove_all_frequented_locations,
    remove_all_frequenting_characters,
    remove_frequented_location,
)
from neighborly.helpers.relationship import (
    deactivate_relationships,
    get_relationship,
    get_relationships_with_traits,
)
from neighborly.helpers.settlement import remove_character_from_settlement
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.life_event import dispatch_life_event
from neighborly.plugins.default_events import (
    BecomeBusinessOwnerEvent,
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


class StartBusiness(Action):
    """Character opens a new business and becomes the owner."""

    __action_id__ = "start-business"

    __slots__ = ("character", "district", "business_definition_id", "owner_role")

    character: GameObject
    district: GameObject
    business_definition_id: str
    owner_role: JobRole

    def __init__(
        self,
        character: GameObject,
        district: GameObject,
        business_definition_id: str,
        owner_role: JobRole,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.district = district
        self.business_definition_id = business_definition_id
        self.owner_role = owner_role

    def execute(self) -> bool:
        # (1) Create the new business GameObject
        business = create_business(self.world, self.business_definition_id)

        # (2) Add the business to the district
        business.add_component(CurrentDistrict(district=self.district))
        district = self.district.get_component(District)
        district.gameobject.get_component(BusinessSpawnTable).increment_count(
            self.business_definition_id
        )

        # (3) Dispatch a global event that a business was added to the sim.
        self.world.events.dispatch_event(
            Event("business-added", self.world, business=business)
        )

        # (4) Dispatch a life event for starting a business
        start_business_event = StartBusinessEvent(
            character=self.character,
            business=business,
        )
        dispatch_life_event(start_business_event, [self.character, business])

        # (5) Execute the action for becoming a business owner. This will
        # Dispatch a life event for becoming a business owner
        # Although this might seem like a duplicate, some systems might
        # only listen for "become-business-owner" events. So we do this
        # to ensure they also include when characters start businesses.
        # Also, this action ensures that relationships are properly updated
        return BecomeBusinessOwner(
            character=self.character, business=business
        ).execute()


class BecomeBusinessOwner(Action):
    """Character becomes the owner of a business."""

    __action_id__ = "become-business-owner"

    __slots__ = ("character", "business")

    character: GameObject
    business: Business

    def __init__(self, character: GameObject, business: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business.get_component(Business)

    def execute(self) -> bool:
        # (1) Update the state of the new owner and business

        set_business_owner(self.business, self.character)

        add_frequented_location(self.character, self.business.gameobject)

        set_business_status(self.business, BusinessStatus.OPEN)

        # (2) Update relationships with any existing employees
        for employee, _ in self.business.employees.items():
            add_trait(get_relationship(self.character, employee), "employee")
            add_trait(get_relationship(employee, self.character), "boss")

        # (4) Dispatch a life event for becoming the owner of this business
        become_business_owner_event = BecomeBusinessOwnerEvent(
            character=self.character,
            business=self.business.gameobject,
        )

        dispatch_life_event(
            become_business_owner_event, [self.character, self.business.gameobject]
        )

        return True


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

    def execute(self) -> bool:
        for rel in get_relationships_with_traits(self.character, "crush"):
            remove_trait(rel, "crush")

        add_trait(get_relationship(self.character, self.crush), "crush")

        return True


class Retire(Action):
    """A character retires from their position at a business."""

    __action_id__ = "retire"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def _choose_successor(self) -> Optional[BecomeBusinessOwner]:
        rng = self.world.resource_manager.get_resource(random.Random)
        occupation = self.character.get_component(Occupation)
        business = occupation.business

        potential_successors: list[tuple[GameObject, float]] = sorted(
            [
                (
                    employee,
                    get_stat(
                        get_relationship(self.character, employee), "reputation"
                    ).value,
                )
                for employee, _ in business.get_component(Business).employees.items()
            ],
            key=lambda entry: entry[1],
        )

        if not potential_successors:
            return

        chosen_successor = potential_successors[-1][0]

        potential_succession_action = BecomeBusinessOwner(chosen_successor, business)

        action_probability = get_action_probability(potential_succession_action)

        if rng.random() < action_probability:
            return potential_succession_action

        return None

    def execute(self) -> bool:
        occupation = self.character.get_component(Occupation)
        business = occupation.business

        # Add the retired trait to the character and update employment status
        add_trait(self.character, "retired")

        # Dispatch a life event for retirement.
        retirement_event = RetirementEvent(
            self.character, business, occupation.job_role
        )
        dispatch_life_event(retirement_event, [self.character])

        LeaveJob(business=business, character=self.character, is_silent=True).execute()

        return True


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

    def execute(self) -> bool:
        due_date = self.world.resources.get_resource(SimDate).copy()
        due_date.increment(months=9)

        self.character.add_component(Pregnant(self.partner, due_date))

        event = PregnancyEvent(self.character, self.partner)
        dispatch_life_event(event, [self.character])

        return True


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

    def execute(self) -> bool:
        remove_trait(get_relationship(self.character, self.partner), "dating")
        remove_trait(get_relationship(self.partner, self.character), "dating")

        add_trait(get_relationship(self.character, self.partner), "ex_partner")
        add_trait(get_relationship(self.partner, self.character), "ex_partner")

        get_stat(
            get_relationship(self.partner, self.character), "romance"
        ).base_value -= 15

        event = DatingBreakUpEvent(self.character, self.partner)
        dispatch_life_event(event, [self.character, self.partner])

        return True


class Divorce(Action):
    """A character stops being married another."""

    __action_id__ = "divorce"

    __slots__ = ("character", "partner")

    character: Character
    partner: Character

    def __init__(self, character: GameObject, partner: GameObject) -> None:
        super().__init__(character.world)
        self.character = character.get_component(Character)
        self.partner = partner.get_component(Character)

    def execute(self) -> bool:
        remove_trait(
            get_relationship(self.character.gameobject, self.partner.gameobject),
            "spouse",
        )
        remove_trait(
            get_relationship(self.partner.gameobject, self.character.gameobject),
            "spouse",
        )

        add_trait(
            get_relationship(self.character.gameobject, self.partner.gameobject),
            "ex_spouse",
        )
        add_trait(
            get_relationship(self.partner.gameobject, self.character.gameobject),
            "ex_spouse",
        )

        get_stat(
            get_relationship(self.partner.gameobject, self.character.gameobject),
            "romance",
        ).base_value -= 25

        event = DivorceEvent(self.character.gameobject, self.partner.gameobject)

        dispatch_life_event(event, [self.character.gameobject, self.partner.gameobject])

        # Split the household
        household = self.character.gameobject.get_component(
            MemberOfHousehold
        ).household.get_component(Household)

        new_household = create_household(self.world)

        if self.character.gameobject == household.head:

            set_household_head(new_household, self.partner.gameobject)

            remove_character_from_household(
                household.gameobject, self.partner.gameobject
            )

            add_character_to_household(new_household, self.partner.gameobject)

        else:

            set_household_head(new_household, self.character.gameobject)

            remove_character_from_household(
                household.gameobject, self.character.gameobject
            )

            add_character_to_household(new_household, self.character.gameobject)

        return True


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

    def execute(self) -> bool:
        remove_trait(get_relationship(self.character, self.partner), "dating")
        remove_trait(get_relationship(self.partner, self.character), "dating")

        add_trait(get_relationship(self.character, self.partner), "spouse")
        add_trait(get_relationship(self.partner, self.character), "spouse")

        set_character_name(
            character=self.partner.get_component(Character),
            last_name=self.character.get_component(Character).last_name,
        )

        # Combine the households under the initiating character
        household = self.character.get_component(
            MemberOfHousehold
        ).household.get_component(Household)

        partner_household = self.partner.get_component(
            MemberOfHousehold
        ).household.get_component(Household)

        if self.character == household.head and self.partner == partner_household.head:
            set_household_head(partner_household.gameobject, None)

            partner_household_members = [*partner_household.members]
            for member in partner_household_members:
                remove_character_from_household(partner_household.gameobject, member)
                add_character_to_household(household.gameobject, member)

            self.world.gameobjects.destroy_gameobject(partner_household.gameobject)

        elif (
            self.character == household.head and self.partner != partner_household.head
        ):
            remove_character_from_household(partner_household.gameobject, self.partner)
            add_character_to_household(household.gameobject, self.partner)

        elif (
            self.character != household.head and self.partner != partner_household.head
        ):
            new_household = create_household(self.world).get_component(Household)
            set_household_head(new_household.gameobject, self.character)
            remove_character_from_household(household.gameobject, self.character)
            remove_character_from_household(partner_household.gameobject, self.partner)
            add_character_to_household(new_household.gameobject, self.character)
            add_character_to_household(new_household.gameobject, self.partner)
        elif (
            self.character != household.head and self.partner == partner_household.head
        ):

            new_household = create_household(self.world).get_component(Household)

            set_household_head(new_household.gameobject, self.character)
            remove_character_from_household(household.gameobject, self.character)
            add_character_to_household(new_household.gameobject, self.character)

            set_household_head(partner_household.gameobject, None)

            partner_household_members = [*partner_household.members]
            for member in partner_household_members:
                remove_character_from_household(partner_household.gameobject, member)
                add_character_to_household(new_household.gameobject, member)

            self.world.gameobjects.destroy_gameobject(partner_household.gameobject)

        # Update step sibling relationships
        for rel_0 in get_relationships_with_traits(self.character, "child"):
            if not rel_0.is_active:
                continue

            child_0 = rel_0.get_component(Relationship).target

            for rel_1 in get_relationships_with_traits(self.partner, "child"):
                if not rel_1.is_active:
                    continue

                child_1 = rel_1.get_component(Relationship).target

                add_trait(get_relationship(child_0, child_1), "step_sibling")
                add_trait(get_relationship(child_0, child_1), "sibling")
                add_trait(get_relationship(child_1, child_0), "step_sibling")
                add_trait(get_relationship(child_1, child_0), "sibling")

        # Update relationships parent/child relationships
        for rel in get_relationships_with_traits(self.character, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(self.partner, child), "child"):
                    add_trait(get_relationship(self.partner, child), "child")
                    add_trait(get_relationship(self.partner, child), "step_child")
                    add_trait(get_relationship(child, self.partner), "parent")
                    add_trait(get_relationship(child, self.partner), "step_parent")

        for rel in get_relationships_with_traits(self.partner, "child"):
            if rel.is_active:
                child = rel.get_component(Relationship).target
                if not has_trait(get_relationship(self.character, child), "child"):
                    add_trait(get_relationship(self.character, child), "child")
                    add_trait(get_relationship(self.character, child), "step_child")
                    add_trait(get_relationship(child, self.character), "parent")
                    add_trait(get_relationship(child, self.character), "step_parent")

        event = MarriageEvent(self.character, self.partner)

        dispatch_life_event(event, [self.character, self.partner])

        return True


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

    def execute(self) -> bool:
        add_trait(get_relationship(self.character, self.partner), "dating")
        add_trait(get_relationship(self.partner, self.character), "dating")

        event = StartDatingEvent(self.character, self.partner)

        dispatch_life_event(event, [self.character, self.partner])

        return True


class HireEmployee(Action):
    """A business hires an employee."""

    __action_id__ = "fire-employee"

    __slots__ = ("business", "character", "role")

    business: GameObject
    character: GameObject
    role: JobRole

    def __init__(
        self,
        business: GameObject,
        character: GameObject,
        role: JobRole,
        is_silent: bool = False,
    ) -> None:
        super().__init__(business.world, is_silent=is_silent)
        self.business = business
        self.character = character
        self.role = role

    def execute(self) -> bool:
        business_comp = self.business.get_component(Business)

        add_employee(business_comp, self.character, self.role)

        add_frequented_location(self.character, self.business)

        # Update boss/employee relationships if needed
        if business_comp.owner is not None:
            add_trait(get_relationship(self.character, business_comp.owner), "boss")
            add_trait(get_relationship(business_comp.owner, self.character), "employee")

        # Update employee/employee relationships
        for employee, _ in business_comp.employees.items():
            if employee == self.character:
                continue

            add_trait(get_relationship(self.character, employee), "coworker")
            add_trait(get_relationship(employee, self.character), "coworker")

        if not self.is_silent:
            hiring_event = StartNewJobEvent(self.character, self.business, self.role)
            dispatch_life_event(hiring_event, [self.character, self.business])

        return True


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

    def execute(self) -> bool:
        job_role = self.character.get_component(Occupation).job_role

        LeaveJob(
            business=self.business, character=self.character, is_silent=True
        ).execute()

        if not self.is_silent:
            firing_event = FiredFromJobEvent(self.character, self.business, job_role)
            dispatch_life_event(firing_event, [self.character])

        return True


class PromoteEmployee(Action):
    """A business owner promotes an employee."""

    __action_id__ = "promote-employee"

    __slots__ = ("business", "character", "role")

    business: GameObject
    character: GameObject
    role: JobRole

    def __init__(
        self, business: GameObject, character: GameObject, role: JobRole
    ) -> None:
        super().__init__(character.world)
        self.business = business
        self.character = character
        self.role = role

    def execute(self) -> bool:
        # Remove the old occupation
        LeaveJob(
            business=self.business, character=self.character, is_silent=True
        ).execute()

        # Add the new occupation
        HireEmployee(
            business=self.business,
            character=self.character,
            role=self.role,
            is_silent=True,
        ).execute()

        if not self.is_silent:
            promotion_event = JobPromotionEvent(
                self.character, self.business, self.role
            )

            dispatch_life_event(promotion_event, [self.character])

        return True


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

    def execute(self) -> bool:

        job_role = self.character.get_component(Occupation).job_role

        LeaveJob(
            business=self.business, character=self.character, is_silent=True
        ).execute()

        if not self.is_silent:
            layoff_event = LayOffEvent(self.character, self.business, job_role)
            dispatch_life_event(layoff_event, [self.character])

        return True


class LeaveJob(Action):
    """A character leaves their job."""

    __action_id__ = "leave-job"

    __slots__ = ("business", "character")

    business: GameObject
    character: GameObject

    def __init__(
        self, business: GameObject, character: GameObject, is_silent: bool = False
    ) -> None:
        super().__init__(business.world, is_silent=is_silent)
        self.business = business
        self.character = character

    def _choose_successor(self) -> Optional[BecomeBusinessOwner]:
        rng = self.world.resource_manager.get_resource(random.Random)

        potential_successors: list[tuple[GameObject, float]] = sorted(
            [
                (
                    employee,
                    get_stat(
                        get_relationship(self.character, employee), "reputation"
                    ).value,
                )
                for employee, _ in self.business.get_component(
                    Business
                ).employees.items()
            ],
            key=lambda entry: entry[1],
        )

        if not potential_successors:
            return

        chosen_successor = potential_successors[-1][0]

        potential_succession_action = BecomeBusinessOwner(
            chosen_successor, self.business
        )

        action_probability = get_action_probability(potential_succession_action)

        if rng.random() < action_probability:
            return potential_succession_action

        return None

    def execute(self) -> bool:

        job_role = self.character.get_component(Occupation).job_role
        business_comp = self.business.get_component(Business)
        succession_action: Optional[BecomeBusinessOwner] = None
        is_business_owner = self.character == business_comp.owner

        remove_frequented_location(self.character, self.business)

        if is_business_owner:
            succession_action = self._choose_successor()

            # Update relationships boss/employee relationships
            for employee, _ in business_comp.employees.items():
                remove_trait(get_relationship(self.character, employee), "employee")
                remove_trait(get_relationship(employee, self.character), "boss")

            set_business_owner(business_comp, None)

        else:

            # Update boss/employee relationships if needed
            owner = business_comp.owner
            if owner is not None:
                remove_trait(get_relationship(self.character, owner), "boss")
                remove_trait(get_relationship(owner, self.character), "employee")

            # Update coworker relationships
            for other_employee, _ in business_comp.employees.items():
                if other_employee == self.character:
                    continue

                remove_trait(
                    get_relationship(self.character, other_employee), "coworker"
                )
                remove_trait(
                    get_relationship(other_employee, self.character), "coworker"
                )

            remove_employee(business_comp, self.character)

        if not self.is_silent:
            leave_job_event = LeaveJobEvent(
                character=self.character, business=self.business, job_role=job_role
            )

            dispatch_life_event(leave_job_event, [self.character])

        # If we have a successor, put them in charge. Otherwise, close the business
        if is_business_owner:
            if succession_action:
                succession_action.execute()
            else:
                CloseBusiness(business=self.business).execute()

        return True


class CloseBusiness(Action):
    """Permanently close a business."""

    __action_id__ = "close-business"

    __slots__ = ("business",)

    business: GameObject

    def __init__(self, business: GameObject) -> None:
        super().__init__(business.world)
        self.business = business

    def execute(self) -> bool:

        business_comp = self.business.get_component(Business)
        business_location = self.business.get_component(CurrentDistrict)

        # Update the business as no longer active
        business_comp.status = BusinessStatus.CLOSED

        # Remove all the employees
        for employee, _ in [*business_comp.employees.items()]:
            LayOffEmployee(business=self.business, character=employee).execute()

        # Remove the owner if applicable
        if business_comp.owner is not None:
            LeaveJob(business=self.business, character=business_comp.owner).execute()

        # Decrement the number of this type
        business_location.district.get_component(BusinessSpawnTable).decrement_count(
            self.business.metadata["definition_id"]
        )

        # Remove any other characters that frequent the location
        remove_all_frequenting_characters(self.business)

        # Un-mark the business as active so it doesn't appear in queries
        self.business.deactivate()
        self.world.events.dispatch_event(
            Event("business-removed", self.world, business=self.business)
        )

        event = BusinessClosedEvent(self.business)
        dispatch_life_event(event, [self.business])

        return True


class Die(Action):
    """A character dies."""

    __action_id__ = "die"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject, is_silent: bool = False) -> None:
        super().__init__(character.world, is_silent=is_silent)
        self.character = character

    def execute(self) -> bool:
        """Have a character die."""

        self.character.deactivate()

        remove_all_frequented_locations(self.character)

        add_trait(self.character, "deceased")

        deactivate_relationships(self.character)

        self.world.events.dispatch_event(
            Event(event_type="death", world=self.world, character=self.character)
        )

        # Remove the character from their household
        # if member_of_household := self.character.try_component(MemberOfHousehold):

        #     household = member_of_household.household.get_component(Household)

        #     if self.character == household.head:
        #         set_household_head(household, None)

        #     if self.character == household.spouse:
        #         set_household_head_spouse(household, None)

        #     remove_character_from_household(
        #         household, self.character.get_component(Character)
        #     )

        if resident_of := self.character.try_component(ResidentOf):

            current_settlement = resident_of.settlement.get_component(Settlement)
            current_settlement.population -= 1
            self.character.remove_component(ResidentOf)

        # Adjust relationships
        for rel in get_relationships_with_traits(self.character, "dating"):
            target = rel.get_component(Relationship).target

            remove_trait(get_relationship(target, self.character), "dating")
            remove_trait(get_relationship(self.character, target), "dating")
            add_trait(get_relationship(target, self.character), "ex_partner")
            add_trait(get_relationship(self.character, target), "ex_partner")

        for rel in get_relationships_with_traits(self.character, "spouse"):
            target = rel.get_component(Relationship).target

            remove_trait(get_relationship(self.character, target), "spouse")
            remove_trait(get_relationship(target, self.character), "spouse")
            add_trait(get_relationship(target, self.character), "ex_spouse")
            add_trait(get_relationship(self.character, target), "ex_spouse")
            add_trait(get_relationship(target, self.character), "widow")

        # Remove the character from their occupation
        if occupation := self.character.try_component(Occupation):
            LeaveJob(
                business=occupation.business, character=self.character, is_silent=True
            ).execute()

        if not self.is_silent:
            death_event = DeathEvent(self.character)
            dispatch_life_event(death_event, [self.character])

        return True


class DepartSettlement(Action):
    """A character departs from the settlement and simulation."""

    __action_id__ = "depart-settlement"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(character.world)
        self.character = character

    def execute(self) -> bool:
        """Have the given character depart the settlement."""

        add_trait(self.character, "departed")

        # Have the character leave their job
        if occupation := self.character.try_component(Occupation):
            if occupation.business.get_component(Business).owner == self.character:
                CloseBusiness(occupation.business).execute()
            else:
                LeaveJob(
                    business=occupation.business, character=self.character
                ).execute()

        # Remove them from the population
        if resident_of := self.character.try_component(ResidentOf):
            settlement = resident_of.settlement.get_component(Settlement)
            remove_character_from_settlement(
                settlement, self.character.get_component(Character)
            )

        event = DepartSettlementEvent(character=self.character)
        dispatch_life_event(event, [self.character])

        remove_all_frequented_locations(self.character)

        self.character.deactivate()

        deactivate_relationships(self.character)

        # Remove the character from their household
        # household = self.character.get_component(
        #     MemberOfHousehold
        # ).household.get_component(Household)

        # if self.character == household.head:
        #     set_household_head(household, None)

        # if self.character == household.spouse:
        #     set_household_head_spouse(household, None)

        # remove_character_from_household(
        #     household, self.character.get_component(Character)
        # )

        return True
