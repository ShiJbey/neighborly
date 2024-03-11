"""Built-in life event subtypes.

"""

from __future__ import annotations

from typing import Any, Optional

from neighborly.components.business import (
    Business,
    ClosedForBusiness,
    Occupation,
    OpenForBusiness,
    Unemployed,
)
from neighborly.components.residence import Resident, ResidentialUnit
from neighborly.components.settlement import District
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.life_event import LifeEvent


class Death(LifeEvent):
    """Event emitted when a character passes away."""

    subject: GameObject
    """The character that died."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} died."


class JoinSettlementEvent(LifeEvent):
    """Dispatched when a character joins a settlement."""

    subject: GameObject
    """The character the joined."""
    settlement: GameObject
    """The settlement that was joined."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} immigrated to {self.settlement.name}."


class BecomeAdolescentEvent(LifeEvent):
    """Event dispatched when a character becomes an adolescent."""

    subject: GameObject
    """The character that became an adolescent."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} became an adolescent."


class BecomeYoungAdultEvent(LifeEvent):
    """Event dispatched when a character becomes a young adult."""

    subject: GameObject
    """The character that became a young adult."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} became a young adult."


class BecomeAdultEvent(LifeEvent):
    """Event dispatched when a character becomes an adult."""

    subject: GameObject
    """The character that became an adult."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} became an adult."


class BecomeSeniorEvent(LifeEvent):
    """Event dispatched when a character becomes a senior."""

    subject: GameObject
    """The character that became a senior."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} became a senior."


class ChangeResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    subject: GameObject
    """The character that changed residences."""
    new_residence: Optional[GameObject]
    """The residence the subject moved to."""
    old_residence: Optional[GameObject]
    """The residence the subject moved from."""

    @property
    def description(self) -> str:
        if self.new_residence is not None:
            district = self.new_residence.get_component(ResidentialUnit).district
            settlement = district.get_component(District).settlement

            return (
                f"{self.subject.name} moved into a new residence "
                f"({self.new_residence.name}) in the {district.name} district of "
                f"{settlement.name}."
            )

        if self.old_residence is not None and self.new_residence is None:
            return f"{self.subject.name} moved out of {self.old_residence.name}."

        return f"{self.subject.name} moved"


class BirthEvent(LifeEvent):
    """Event dispatched when a child is born."""

    subject: GameObject
    """The character that was born."""

    def __str__(self) -> str:
        return f"{self.subject.name} was born."


class HaveChildEvent(LifeEvent):
    """Event dispatched when a character has a child."""

    birthing_parent: GameObject
    other_parent: Optional[GameObject]
    child: GameObject

    def __str__(self) -> str:
        if self.other_parent is not None:
            return (
                f"{self.birthing_parent.name} and "
                f"{self.other_parent.name} welcomed a new child, {self.child.name}."
            )
        else:
            return (
                f"{self.birthing_parent.name} welcomed a new child, {self.child.name}."
            )


class LeaveJob(LifeEvent):
    """Character leaves job of their own will."""

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        job_role: GameObject,
        reason: str = "",
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, log_event=True),
                EventRole("business", business, log_event=True),
                EventRole("job_role", job_role),
            ],
            reason=reason,
        )

    def execute(self) -> None:
        business = self.roles["business"]
        subject = self.roles["subject"]

        current_date = self.world.resources.get_resource(SimDate)

        business_comp = business.get_component(Business)

        remove_frequented_location(subject, business)

        if subject == business_comp.owner:
            business_comp.set_owner(None)

            # Update relationships boss/employee relationships
            for employee, _ in business_comp.employees.items():
                remove_trait(get_relationship(subject, employee), "employee")
                remove_trait(get_relationship(employee, subject), "boss")

            subject.add_component(Unemployed(timestamp=current_date))

            subject.remove_component(Occupation)

            subject.add_component(Unemployed(timestamp=current_date))

        else:
            business_comp.remove_employee(subject)

            # Update boss/employee relationships if needed
            owner = business_comp.owner
            if owner is not None:
                remove_trait(get_relationship(subject, owner), "boss")
                remove_trait(get_relationship(owner, subject), "employee")

            # Update coworker relationships
            for other_employee, _ in business_comp.employees.items():
                if other_employee == subject:
                    continue

                remove_trait(get_relationship(subject, other_employee), "coworker")
                remove_trait(get_relationship(other_employee, subject), "coworker")

        subject.add_component(Unemployed(timestamp=current_date))
        subject.remove_component(Occupation)

    def __str__(self) -> str:
        subject = self.roles["subject"]
        reason = self.data["reason"]
        business = self.roles["business"]
        job_role = self.roles["job_role"]

        if reason:
            return (
                f"{subject.name} left their job as a "
                f"{job_role.name} at {business.name} due to {reason}."
            )

        return (
            f"{subject.name} left their job as a "
            f"{job_role.name} at {business.name}."
        )


class DepartSettlement(LifeEvent):
    """Character leave the settlement and the simulation."""

    def __init__(self, subject: GameObject, reason: str = "") -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject)], reason=reason
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return DepartSettlement(subject)

    def execute(self) -> None:
        character = self.roles["subject"]

        remove_all_frequented_locations(character)
        add_trait(character, "departed")
        character.deactivate()

        deactivate_relationships(character)

        # Have the character leave their job
        if occupation := character.try_component(Occupation):
            if occupation.business.get_component(Business).owner == character:
                BusinessClosedEvent(
                    subject=character, business=occupation.business
                ).dispatch()
            else:
                LeaveJob(
                    subject=character,
                    business=occupation.business,
                    job_role=occupation.job_role.gameobject,
                    reason="departed settlement",
                ).dispatch()

        # Have the character leave their residence
        if resident_data := character.try_component(Resident):
            residence_data = resident_data.residence.get_component(ResidentialUnit)
            ChangeResidenceEvent(subject=character, new_residence=None).dispatch()

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
                    DepartSettlement(resident).dispatch()

                elif has_trait(rel_to_resident, "child") and not has_trait(
                    resident, "departed"
                ):
                    DepartSettlement(resident).dispatch()

    def __str__(self):
        subject = self.roles["subject"]
        return f"{subject.name} departed from the settlement."


class LaidOffFromJob(LifeEvent):
    """The character is laid off from their job."""

    def __init__(
        self,
        subject: GameObject,
        business: GameObject,
        job_role: GameObject,
        reason: str = "",
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, log_event=True),
                EventRole("business", business),
                EventRole("job_role", job_role),
            ],
            reason=reason,
        )

    def execute(self) -> None:
        business = self.roles["business"]
        employee = self.roles["subject"]

        current_date = self.world.resources.get_resource(SimDate)

        business_comp = business.get_component(Business)

        remove_frequented_location(employee, business)

        business_comp.remove_employee(employee)

        # Update boss/employee relationships if needed
        owner = business_comp.owner
        if owner is not None:
            remove_trait(get_relationship(employee, owner), "boss")
            remove_trait(get_relationship(owner, employee), "employee")

        # Update coworker relationships
        for other_employee, _ in business_comp.employees.items():
            if other_employee == employee:
                continue

            remove_trait(get_relationship(employee, other_employee), "coworker")
            remove_trait(get_relationship(other_employee, employee), "coworker")

        employee.add_component(Unemployed(timestamp=current_date))
        employee.remove_component(Occupation)

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        if occupation := subject.try_component(Occupation):
            return LaidOffFromJob(
                subject=subject,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
            )

        return None

    def __str__(self):
        subject = self.roles["subject"]
        business = self.roles["business"]
        job_role = self.roles["job_role"]
        return (
            f"{subject.name} was laid off from their job as a {job_role.name} "
            f"at {business.name}"
        )


class BusinessClosedEvent(LifeEvent):
    """Event emitted when a business closes."""

    def __init__(
        self, subject: GameObject, business: GameObject, reason: str = ""
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("business", business, True),
            ],
            reason=reason,
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        if occupation := subject.get_component(Occupation):
            business_data = occupation.business.get_component(Business)

            if business_data.owner == subject:
                return BusinessClosedEvent(
                    subject=subject, business=business_data.gameobject
                )

        return None

    def execute(self) -> None:
        business = self.roles["business"]
        business_comp = business.get_component(Business)

        # Update the business as no longer active
        business.remove_component(OpenForBusiness)
        business.add_component(ClosedForBusiness())

        # Remove all the employees
        for employee, role in [*business_comp.employees.items()]:
            LaidOffFromJob(
                subject=employee,
                business=business,
                job_role=role.gameobject,
            ).dispatch()

        # Remove the owner if applicable
        if business_comp.owner is not None:
            LeaveJob(
                business=business,
                subject=business_comp.owner,
                job_role=business_comp.owner_role.gameobject,
                reason="business closed",
            ).dispatch()

        # Decrement the number of this type
        business_comp.district.get_component(BusinessSpawnTable).decrement_count(
            business.metadata["definition_id"]
        )
        business_comp.district.get_component(District).remove_business(business)

        # Remove any other characters that frequent the location
        remove_all_frequenting_characters(business)

        # Un-mark the business as active so it doesn't appear in queries
        business.deactivate()

    def __str__(self) -> str:
        subject = self.roles["subject"]
        business = self.roles["business"]
        return f"{subject.name}'s business {business.name} has closed for business."
