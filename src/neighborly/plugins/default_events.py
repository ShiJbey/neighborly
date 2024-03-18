"""Other event implementations.

"""

from __future__ import annotations

from typing import Optional

import attrs

from neighborly.ecs import GameObject
from neighborly.life_event import LifeEvent


@attrs.define
class StartJobEvent(LifeEvent):
    """A character will attempt to find a job."""

    subject: GameObject
    """The character started the new job."""
    business: GameObject
    """The business they started working at."""
    role: GameObject
    """The role they work."""

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} started a new job as a "
            f"{self.role.name} at {self.business.name}."
        )


@attrs.define
class StartBusinessEvent(LifeEvent):
    """Character starts a specific business."""

    subject: GameObject
    business: GameObject
    district: GameObject
    settlement: GameObject

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} opened a new business, "
            f"{self.business.name}, in the {self.district.name} district of "
            f"{self.settlement.name}."
        )


@attrs.define
class StartDatingEvent(LifeEvent):
    """Event dispatched when two characters start dating."""

    subject: GameObject
    partner: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.partner.name} started dating."


@attrs.define
class MarriageEvent(LifeEvent):
    """Event dispatched when two characters get married."""

    subject: GameObject
    spouse: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.spouse.name} got married."


@attrs.define
class DivorceEvent(LifeEvent):
    """Dispatched to officially divorce two married characters."""

    subject: GameObject
    ex_spouse: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} divorced from {self.ex_spouse.name}."


@attrs.define
class BreakUpEvent(LifeEvent):
    """Dispatched to officially break up a dating relationship between characters."""

    initiator: GameObject
    ex_partner: GameObject

    @property
    def description(self) -> str:
        return f"{self.initiator.name} broke up with " f"{self.ex_partner.name}."


@attrs.define
class PregnancyEvent(LifeEvent):
    """Characters have a chance of getting pregnant while in romantic relationships."""

    subject: GameObject
    partner: Optional[GameObject] = None

    @property
    def description(self) -> str:
        if self.partner is not None:
            return f"{self.subject.name} got pregnant by {self.partner.name}."

        return f"{self.subject.name} got pregnant."


@attrs.define
class RetirementEvent(LifeEvent):
    """Simulates a character retiring from their position at a business.

    When a business owner retires they may appoint a current employee or family member
    to become the owner of the business. If they can't find a suitable successor,
    then they shut the business down and everyone is laid-off.

    If the retiree is an employee, they are just removed from their role and business
    continues as usual.
    """

    subject: GameObject
    business: GameObject
    job_role: GameObject

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} retired from their "
            f"position as {self.job_role.name} at {self.business.name}."
        )


@attrs.define
class StartFriendshipEvent(LifeEvent):
    """Two characters become friends."""

    subject: GameObject
    other: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.other.name} became friends."


@attrs.define
class EndFriendshipEvent(LifeEvent):
    """Two characters stop being friends."""

    subject: GameObject
    other: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.other.name} stopped being friends."


@attrs.define
class StartEnmityEvent(LifeEvent):
    """Two characters become enemies."""

    subject: GameObject
    other: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.other.name} became enemies."


@attrs.define
class EndEnmityEvent(LifeEvent):
    """Two characters stop being enemies."""

    subject: GameObject
    other: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} and {self.other.name} stopped being enemies."


@attrs.define
class FormCrushEvent(LifeEvent):
    """A character forms a new crush on someone."""

    subject: GameObject
    other: GameObject
    subject: GameObject
    other: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} formed a crush on {self.other.name}"


@attrs.define
class BecomeBusinessOwnerEvent(LifeEvent):
    """Simulate a character being promoted to the owner of a business."""

    subject: GameObject
    business: GameObject

    @property
    def description(self) -> str:
        return f"{self.subject.name} became the owner of {self.business.name}."


@attrs.define
class JobPromotionEvent(LifeEvent):
    """The character is promoted at their job from a lower role to a higher role."""

    subject: GameObject
    business: GameObject
    old_role: GameObject
    new_role: GameObject

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} was promoted from {self.old_role.name} to "
            f"{self.new_role.name} at {self.business.name}."
        )


@attrs.define
class FiredFromJobEvent(LifeEvent):
    """The character is fired from their job."""

    subject: GameObject
    business: GameObject
    job_role: GameObject

    @property
    def description(self) -> str:
        return (
            f"{self.subject.name} was fired from their role as a "
            f"{self.job_role.name} at {self.business.name}."
        )
