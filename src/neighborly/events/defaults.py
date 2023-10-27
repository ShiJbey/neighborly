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
from neighborly.components.character import Character, LifeStage
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.settlement import District
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.helpers.location import (
    remove_all_frequented_locations,
    remove_all_frequenting_characters,
    remove_frequented_location,
)
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.traits import add_trait, has_trait, remove_trait
from neighborly.life_event import EventRole, LifeEvent


class Death(LifeEvent):
    """Event emitted when a character passes away."""

    base_probability = 0.0

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject, True)]
        )

    def execute(self) -> None:
        character = self.roles["subject"]
        remove_all_frequented_locations(character)
        character.deactivate()
        add_trait(character, "deceased")

        # Remove the character from their residence
        if resident_data := character.try_component(Resident):
            residence = resident_data.residence
            ChangeResidenceEvent(subject=character, new_residence=None).dispatch()

            # If there are no-more residents that are owner's remove everyone from
            # the residence and have them depart the simulation.
            residence_data = residence.get_component(Residence)
            if len(list(residence_data.owners)) == 0:
                residents = list(residence_data.residents)
                for resident in residents:
                    DepartSettlement(resident, "death in family")

        # Remove the character from their occupation
        if occupation := character.try_component(Occupation):
            LeaveJob(
                subject=character,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
                reason="died",
            ).dispatch()

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def __str__(self) -> str:
        character = self.roles["subject"]
        return f"[{self.timestamp}] {character.name} died."


class JoinSettlementEvent(LifeEvent):
    """Dispatched when a character joins a settlement."""

    def __init__(self, subject: GameObject, settlement: GameObject) -> None:
        super().__init__(
            world=subject.world,
            roles=[
                EventRole("subject", subject, True),
                EventRole("settlement", settlement),
            ],
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def execute(self) -> None:
        return

    def __str__(self) -> str:
        character = self.roles["subject"]
        settlement = self.roles["settlement"]

        return f"[{self.timestamp}] {character.name} immigrated to {settlement.name}."


class BecomeAdolescentEvent(LifeEvent):
    """Event dispatched when a character becomes an adolescent."""

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject, True)]
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def execute(self) -> None:
        subject = self.roles["subject"]
        subject.get_component(Character).life_stage = LifeStage.ADOLESCENT

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.roles["subject"].uid}

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.roles['subject'].name} became an adolescent."


class BecomeYoungAdultEvent(LifeEvent):
    """Event dispatched when a character becomes a young adult."""

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject, True)]
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def execute(self) -> None:
        subject = self.roles["subject"]
        subject.get_component(Character).life_stage = LifeStage.YOUNG_ADULT

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.roles["subject"].uid}

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.roles['subject'].name} became a young adult."


class BecomeAdultEvent(LifeEvent):
    """Event dispatched when a character becomes an adult."""

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject, True)]
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def execute(self) -> None:
        subject = self.roles["subject"]
        subject.get_component(Character).life_stage = LifeStage.ADULT

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.roles["subject"].uid}

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.roles['subject'].name} became an adult."


class BecomeSeniorEvent(LifeEvent):
    """Event dispatched when a character becomes a senior."""

    def __init__(self, subject: GameObject) -> None:
        super().__init__(
            world=subject.world, roles=[EventRole("subject", subject, True)]
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def execute(self) -> None:
        subject = self.roles["subject"]
        subject.get_component(Character).life_stage = LifeStage.SENIOR

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.roles["subject"].uid}

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.roles['subject'].name} became a senior."


class ChangeResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    def __init__(
        self,
        subject: GameObject,
        new_residence: Optional[GameObject],
        is_owner: bool = False,
    ) -> None:
        super().__init__(
            world=subject.world,
            roles=(EventRole("subject", subject),),
            is_owner=is_owner,
        )

        if new_residence is not None:
            self.roles.add_role(EventRole("new_residence", new_residence))

    def execute(self) -> None:
        character = self.roles["subject"]
        new_residence = self.roles.get_first_or_none("new_residence")

        if resident := character.try_component(Resident):
            # This character is currently a resident at another location
            former_residence = resident.residence
            former_residence_comp = former_residence.get_component(Residence)

            if former_residence_comp.is_owner(character):
                former_residence_comp.remove_owner(character)

            former_residence_comp.remove_resident(character)
            character.remove_component(Resident)

            former_district = former_residence.get_component(
                Residence
            ).district.get_component(District)
            former_district.population -= 1

            if len(former_residence_comp) <= 0:
                former_residence.add_component(Vacant())

        # Don't add them to a new residence if none is given
        if new_residence is None:
            return

        # Move into new residence
        new_residence.get_component(Residence).add_resident(character)

        if self.data["is_owner"]:
            new_residence.get_component(Residence).add_owner(character)

        character.add_component(Resident(residence=new_residence))

        if new_residence.has_component(Vacant):
            new_residence.remove_component(Vacant)

        new_district = new_residence.get_component(Residence).district.get_component(
            District
        )
        new_district.population += 1

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def __str__(self) -> str:
        subject = self.roles["subject"]
        new_residence = self.roles.get_first_or_none("new_residence")

        if new_residence is not None:
            district = new_residence.get_component(Residence).district
            settlement = district.get_component(District).settlement

            return (
                f"[{self.timestamp}] {subject.name} moved into a new residence "
                f"({new_residence.name}) in the {district.name} district of "
                f"{settlement.name}."
            )

        return f"[{self.timestamp}] {subject.name} moved out of their residence."


class BirthEvent(LifeEvent):
    """Event dispatched when a child is born."""

    base_probability = 0.0

    def __init__(
        self,
        subject: GameObject,
    ) -> None:
        super().__init__(
            world=subject.world, roles=(EventRole("subject", subject, True),)
        )

    def execute(self) -> None:
        return

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return BirthEvent(subject)

    def __str__(self) -> str:
        return f"[{self.timestamp}] {self.roles['subject'].name} was born."


class HaveChildEvent(LifeEvent):
    """Event dispatched when a character has a child."""

    base_probability = 0

    def __init__(
        self,
        parent_0: GameObject,
        parent_1: GameObject,
        child: GameObject,
    ) -> None:
        super().__init__(
            world=parent_0.world,
            roles=(
                EventRole("subject", parent_0, True),
                EventRole("subject", parent_1, True),
                EventRole("child", child),
            ),
        )

    def execute(self) -> None:
        return

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        return None

    def __str__(self) -> str:
        parent_0, parent_1 = self.roles.get_all("subject")
        child = self.roles["child"]
        return (
            f"[{self.timestamp}] {parent_0.name} and "
            f"{parent_1.name} welcomed a new child, {child.name}."
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
                EventRole("business", business),
                EventRole("job_role", job_role),
            ],
            reason=reason,
        )

    @classmethod
    def instantiate(cls, subject: GameObject, **kwargs: Any) -> LifeEvent | None:
        if occupation := subject.try_component(Occupation):
            return LeaveJob(
                subject=subject,
                business=occupation.business,
                job_role=occupation.job_role.gameobject,
            )

        return None

    def execute(self) -> None:
        business = self.roles["business"]
        subject = self.roles["subject"]

        current_date = self.world.resource_manager.get_resource(SimDate)

        business_comp = business.get_component(Business)

        remove_frequented_location(subject, business)

        if business_comp.owner is not None and subject == business_comp.owner:
            business_comp.set_owner(None)

            # Update relationships boss/employee relationships
            for employee, _ in business_comp.employees.items():
                remove_trait(get_relationship(subject, employee), "employee")
                remove_trait(get_relationship(employee, subject), "boss")

            subject.add_component(Unemployed(timestamp=current_date))

            subject.remove_component(Occupation)

            subject.add_component(Unemployed(timestamp=current_date))

            # BusinessShutsDown(business, f"owner {reason}")
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
                f"[{self.timestamp}] {subject.name} left their job as a "
                f"{job_role.name} at {business.name} due to {reason}."
            )

        return (
            f"[{self.timestamp}] {subject.name} left their job as a "
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
            residence_data = resident_data.residence.get_component(Residence)
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

        current_date = self.world.resource_manager.get_resource(SimDate)

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
        if business_comp.owner is not None and business_comp.owner_role is not None:
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
        return (
            f"[{self.timestamp}] {subject.name}'s business {business.name} has "
            "closed for business."
        )
