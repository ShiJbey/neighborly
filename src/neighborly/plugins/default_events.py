"""Other event implementations.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.business import JobRole
from neighborly.ecs import GameObject
from neighborly.life_event import LifeEvent


class StartNewJobEvent(LifeEvent):
    """A character will attempt to find a job."""

    __event_type__ = "new_job"

    __slots__ = ("character", "business", "job_role")

    character: GameObject
    business: GameObject
    job_role: JobRole

    def __init__(
        self, character: GameObject, business: GameObject, job_role: JobRole
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} started a new job as a "
            f"{self.job_role.name} at {self.business.name}."
        )


class StartBusinessEvent(LifeEvent):
    """Character becomes owner of a business."""

    __event_type__ = "start-business"

    __slots__ = ("character", "business")

    character: GameObject
    business: GameObject

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} opened a new business, {self.business.name}."


class BecomeBusinessOwnerEvent(LifeEvent):
    """Character becomes owner of a business."""

    __event_type__ = "become-business-owner"

    __slots__ = ("character", "business")

    character: GameObject
    business: GameObject

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} became the business owner of {self.business.name}."
        )


class RejectDatingProposalEvent(LifeEvent):
    """A character was rejected."""

    __event_type__ = "reject_dating_proposal"

    __slots__ = ("performer", "target")

    performer: GameObject
    target: GameObject

    def __init__(self, performer: GameObject, target: GameObject) -> None:
        super().__init__(performer.world)
        self.performer = performer
        self.target = target
        self.data["performer"] = performer
        self.data["target"] = target

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.performer.uid,
            "partner": self.target.uid,
        }

    def __str__(self) -> str:
        return f"{self.performer.name} rejected {self.target.name}'s dating proposal."


class AskOutEvent(LifeEvent):
    """A character tried to ask another to start dating."""

    __event_type__ = "ask_out"

    __slots__ = ("performer", "target")

    performer: GameObject
    target: GameObject

    def __init__(self, performer: GameObject, target: GameObject) -> None:
        super().__init__(performer.world)
        self.performer = performer
        self.target = target
        self.data["performer"] = performer
        self.data["target"] = target

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.performer.uid,
            "partner": self.target.uid,
        }

    def __str__(self) -> str:
        return f"{self.performer.name} asked {self.target.name} to date."


class StartDatingEvent(LifeEvent):
    """Event dispatched when two characters start dating."""

    __event_type__ = "start_dating"

    __slots__ = ("initiator", "partner")

    initiator: GameObject
    partner: GameObject

    def __init__(self, initiator: GameObject, partner: GameObject) -> None:
        super().__init__(initiator.world)
        self.initiator = initiator
        self.partner = partner
        self.data["performer"] = initiator
        self.data["target"] = partner

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.initiator.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.initiator.name} and {self.partner.name} started dating."


class ProposeMarriageEvent(LifeEvent):
    """Event dispatched when two characters get married."""

    __event_type__ = "marriage-proposal"

    __slots__ = ("performer", "target")

    performer: GameObject
    target: GameObject

    def __init__(self, performer: GameObject, target: GameObject) -> None:
        super().__init__(performer.world)
        self.performer = performer
        self.target = target
        self.data["performer"] = performer
        self.data["target"] = target

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.performer.uid,
            "partner": self.target.uid,
        }

    def __str__(self) -> str:
        return f"{self.performer.name} proposed marriage to {self.target.name}."


class MarriageEvent(LifeEvent):
    """Event dispatched when two characters get married."""

    __event_type__ = "marriage"

    __slots__ = ("initiator", "partner")

    initiator: GameObject
    partner: GameObject

    def __init__(self, initiator: GameObject, partner: GameObject) -> None:
        super().__init__(initiator.world)
        self.initiator = initiator
        self.partner = partner

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.initiator.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.initiator.name} and {self.partner.name} got married."


class MarriageProposalRejectionEvent(LifeEvent):
    """Event dispatched when two characters get married."""

    __event_type__ = "marriage-rejection"

    __slots__ = ("performer", "target")

    performer: GameObject
    target: GameObject

    def __init__(self, performer: GameObject, target: GameObject) -> None:
        super().__init__(performer.world)
        self.performer = performer
        self.target = target
        self.data["performer"] = performer
        self.data["target"] = target

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.performer.uid,
            "partner": self.target.uid,
        }

    def __str__(self) -> str:
        return f"{self.performer.name} rejected {self.target.name}'s marriage proposal."


class DivorceEvent(LifeEvent):
    """Event dispatched when a character chooses to divorce from their spouse."""

    __event_type__ = "divorce"

    __slots__ = ("initiator", "partner")

    initiator: GameObject
    partner: GameObject

    def __init__(self, initiator: GameObject, partner: GameObject) -> None:
        super().__init__(initiator.world)
        self.initiator = initiator
        self.partner = partner

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.initiator.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.initiator.name} divorced from {self.partner.name}."


class DatingBreakUpEvent(LifeEvent):
    """Event dispatched when a character decides to stop dating another."""

    __event_type__ = "dating_break_up"

    __slots__ = ("initiator", "partner")

    initiator: GameObject
    partner: GameObject

    def __init__(self, initiator: GameObject, partner: GameObject) -> None:
        super().__init__(initiator.world)
        self.initiator = initiator
        self.partner = partner

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.initiator.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.initiator.name} broke up with {self.partner.name}."


class PregnancyEvent(LifeEvent):
    """Event dispatched when a character becomes pregnant."""

    __event_type__ = "pregnancy"

    __slots__ = ("character", "partner")

    character: GameObject
    partner: GameObject

    def __init__(
        self,
        character: GameObject,
        partner: GameObject,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.partner = partner

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} got pregnant."


class RetirementEvent(LifeEvent):
    """Event dispatched when a character retires from an occupation."""

    __event_type__ = "retirement"

    __slots__ = ("character", "business", "job_role")

    character: GameObject
    business: GameObject
    job_role: JobRole

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
        job_role: JobRole,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} retired from their "
            f"position as a(n) {self.job_role.name} at {self.business.name}."
        )


class JobPromotionEvent(LifeEvent):
    """Event dispatched when a character is promoted at their job."""

    __event_type__ = "job_promotion"

    __slots__ = ("character", "business", "job_role")

    character: GameObject
    business: GameObject
    job_role: JobRole

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
        job_role: JobRole,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} was promoted to "
            f"{self.job_role.name} at {self.business.name}."
        )


class FiredFromJobEvent(LifeEvent):
    """Event dispatched when a character is fired from their job."""

    __event_type__ = "fired"

    __slots__ = ("character", "business", "job_role")

    character: GameObject
    business: GameObject
    job_role: JobRole

    def __init__(
        self, character: GameObject, business: GameObject, job_role: JobRole
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} was fired from their role as a(n) "
            f"{self.job_role.name} at {self.business.name}."
        )


class DeathEvent(LifeEvent):
    """Event emitted when a character passes away."""

    __event_type__ = "death"

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.life_event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r}, "
            f"character={self.character.name!r})"
        )

    def __str__(self) -> str:
        return f"{self.character.name} died."


class JoinSettlementEvent(LifeEvent):
    """Dispatched when a character joins a settlement."""

    __event_type__ = "join-settlement"

    __slots__ = ("settlement", "character")

    settlement: GameObject
    character: GameObject

    def __init__(self, character: GameObject, settlement: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.settlement = settlement
        self.data = {"character": character, "settlement": settlement}

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "settlement": self.settlement.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} joined settlement, {self.settlement.name}."


class BecomeAdolescentEvent(LifeEvent):
    """Event dispatched when a character becomes an adolescent."""

    __event_type__ = "become-adolescent"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __str__(self) -> str:
        return f"{self.character.name} became an adolescent."


class BecomeYoungAdultEvent(LifeEvent):
    """Event dispatched when a character becomes a young adult."""

    __event_type__ = "become-young-adult"

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __str__(self) -> str:
        return f"{self.character.name} became a young adult."


class BecomeAdultEvent(LifeEvent):
    """Event dispatched when a character becomes an adult."""

    __event_type__ = "become-adult"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __str__(self) -> str:
        return f"{self.character.name} became an adult."


class BecomeSeniorEvent(LifeEvent):
    """Event dispatched when a character becomes a senior."""

    __event_type__ = "become-senior"

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __str__(self) -> str:
        return f"{self.character.name} became a senior."


class BirthEvent(LifeEvent):
    """Event dispatched when a child is born."""

    __event_type__ = "birth"

    __slots__ = ("character",)

    character: GameObject

    def __init__(
        self,
        character: GameObject,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.data = {"character": character}

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} was born."


class ChildBirthEvent(LifeEvent):
    """Event dispatched when a character has a child."""

    __event_type__ = "child-birth"

    __slots__ = ("child", "birthing_parent", "other_parent")

    child: GameObject
    birthing_parent: GameObject
    other_parent: GameObject

    def __init__(
        self,
        birthing_parent: GameObject,
        other_parent: GameObject,
        child: GameObject,
    ) -> None:
        super().__init__(child.world)
        self.child = child
        self.birthing_parent = birthing_parent
        self.other_parent = other_parent
        self.data = {
            "birthing_parent": birthing_parent,
            "other_parent": other_parent,
            "child": child,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "child": self.child.uid,
            "birthing_parent": self.birthing_parent.uid,
            "other_parent": self.other_parent.uid,
        }

    def __str__(self) -> str:
        return (
            f"{self.birthing_parent.name} and "
            f"{self.other_parent.name} welcomed a new child, {self.child.name}."
        )


class LeaveJobEvent(LifeEvent):
    """Character leaves job of their own will."""

    __event_type__ = "leave-job"

    __slots__ = ("business", "character", "job_role", "reason")

    reason: str
    business: GameObject
    job_role: JobRole
    character: GameObject

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
        job_role: JobRole,
        reason: str = "",
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role
        self.reason = reason
        self.data = {
            "character": self.character,
            "business": self.business,
            "job_role": self.job_role,
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
            "reason": self.reason,
        }

    def __str__(self) -> str:
        if self.reason:
            return (
                f"{self.character.name} left their job as a "
                f"{self.job_role.name} at {self.business.name} due to {self.reason}."
            )

        return (
            f"{self.character.name} left their job as a "
            f"{self.job_role.name} at {self.business.name}."
        )


class DepartSettlementEvent(LifeEvent):
    """Character leave the settlement and the simulation."""

    __event_type__ = "depart"

    __slots__ = ("character", "reason")

    character: GameObject
    reason: str

    def __init__(self, character: GameObject, reason: str = "") -> None:
        super().__init__(character.world)
        self.character = character
        self.reason = reason
        self.data = {
            "character": self.character,
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "reason": self.reason,
        }

    def __str__(self):
        return f"{self.character.name} departed from the settlement."


class LayOffEvent(LifeEvent):
    """The character is laid off from their job."""

    __event_type__ = "lay-off"

    __slots__ = ("business", "job_role", "character", "reason")

    business: GameObject
    job_role: JobRole
    character: GameObject
    reason: str

    def __init__(
        self,
        character: GameObject,
        business: GameObject,
        job_role: JobRole,
        reason: str = "",
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.business = business
        self.job_role = job_role
        self.reason = reason
        self.data = {
            "character": self.character,
            "business": self.business,
            "job_role": self.job_role,
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "business": self.business.uid,
            "job_role": self.job_role.definition_id,
            "reason": self.reason,
        }

    def __str__(self):
        return (
            f"{self.character.name} was laid off from their job as a {self.job_role.name} "
            f"at {self.business.name}."
        )


class BusinessClosedEvent(LifeEvent):
    """Event emitted when a business closes."""

    __event_type__ = "business-closed"

    __slots__ = ("business", "reason")

    business: GameObject
    reason: str

    def __init__(self, business: GameObject, reason: str = "") -> None:
        super().__init__(business.world)
        self.business = business
        self.reason = reason
        self.data = {
            "business": self.business,
            "reason": self.reason,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "business": self.business.uid,
            "reason": self.reason,
        }

    def __str__(self) -> str:
        return f"{self.business.name} has closed for business."


class SettlementAddedEvent(LifeEvent):
    """Event dispatched when a settlement is created."""

    __event_type__ = "settlement-added"

    __slots__ = ("settlement",)

    settlement: GameObject

    def __init__(self, settlement: GameObject) -> None:
        super().__init__(settlement.world)
        self.settlement = settlement
        self.data = {
            "settlement": self.settlement,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "settlement": self.settlement.uid,
        }

    def __str__(self) -> str:
        return f"Created new settlement, {self.settlement.name}."
