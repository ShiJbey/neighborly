"""Built-in life event subtypes.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.business import JobRole
from neighborly.ecs import GameObject
from neighborly.life_event import LifeEvent


class DeathEvent(LifeEvent):
    """Event emitted when a character passes away."""

    __event_type__ = "death"

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character = character

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

    def to_dict(self) -> dict[str, Any]:
        return {**super().to_dict(), "character": self.character.uid}

    def __str__(self) -> str:
        return f"{self.character.name} became a senior."


class MoveOutOfResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    __event_type__ = "move-out-residence"

    __slots__ = ("character", "residence")

    character: GameObject
    residence: GameObject

    def __init__(self, character: GameObject, residence: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.residence = residence

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "residence": self.residence.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} moved out of their residence, {self.residence.name}."


class MoveIntoResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    __event_type__ = "move-into-residence"

    __slots__ = ("character", "residence")

    character: GameObject
    residence: GameObject

    def __init__(self, character: GameObject, residence: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.residence = residence

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
            "residence": self.residence.uid,
        }

    def __str__(self) -> str:
        return (
            f"{self.character.name} moved into a new residence, {self.residence.name}"
        )


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

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "character": self.character.uid,
        }

    def __str__(self) -> str:
        return f"{self.character.name} was born."


class HaveChildEvent(LifeEvent):
    """Event dispatched when a character has a child."""

    __event_type__ = "have_child"

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

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "settlement": self.settlement.uid,
        }

    def __str__(self) -> str:
        return f"Created new settlement, {self.settlement.name}."
