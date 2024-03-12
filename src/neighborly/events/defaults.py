"""Built-in life event subtypes.

"""

from __future__ import annotations

from typing import Optional

from neighborly.components.residence import ResidentialUnit
from neighborly.components.settlement import District
from neighborly.ecs import GameObject
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

    subject: GameObject
    """The character that left the job."""
    business: GameObject
    """The subject's former employer."""
    role: GameObject
    """The subject's former role at the business."""
    reason: str
    """The reason for leaving."""

    @property
    def description(self) -> str:
        if self.reason:
            return (
                f"{self.subject.name} left their job as a "
                f"{self.role.name} at {self.business.name} due to {self.reason}."
            )

        return (
            f"{self.subject.name} left their job as a "
            f"{self.role.name} at {self.business.name}."
        )


class DepartSettlement(LifeEvent):
    """Character leave the settlement and the simulation."""

    subject: GameObject
    """The character that departed."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} departed from the settlement."


class LaidOffFromJob(LifeEvent):
    """The character is laid off from their job."""

    subject: GameObject
    """The character that was laid off."""
    business: GameObject
    """The subject's former employer."""
    role: GameObject
    """The subject's former role at the business."""
    reason: str
    """The reason for leaving."""

    @property
    def description(self) -> str:
        if self.reason:
            return (
                f"{self.subject.name} was laid off from their job as a {self.role.name} "
                f"at {self.business.name} due to {self.reason}"
            )

        return (
            f"{self.subject.name} was laid off from their job as a {self.role.name} "
            f"at {self.business.name}"
        )


class BusinessClosedEvent(LifeEvent):
    """Event emitted when a business closes."""

    subject: GameObject
    """The business that closed."""

    @property
    def description(self) -> str:
        return f"{self.subject.name} has closed for business."
