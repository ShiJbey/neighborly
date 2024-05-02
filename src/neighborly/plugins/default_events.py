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
    """Character starts a specific business."""

    __event_type__ = "start_business"

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

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "initiator": self.initiator.uid,
            "partner": self.partner.uid,
        }

    def __str__(self) -> str:
        return f"{self.initiator.name} and {self.partner.name} started dating."


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
