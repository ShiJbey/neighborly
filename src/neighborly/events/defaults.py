"""Built-in life event subtypes.

"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.components.business import JobRole
from neighborly.ecs import GameObject
from neighborly.life_event import LifeEvent


class DeathEvent(LifeEvent):
    """Event emitted when a character passes away."""

    __event_id__ = "death"
    __tablename__ = "death_event"
    __mapper_args__ = {
        "polymorphic_identity": "death",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character_id = character.uid
        self.character = character

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f"event_type={self.event_type!r}, timestamp={self.timestamp!r}, "
            f"character={self.character.name!r})"
        )

    def __str__(self) -> str:
        return f"{self.character.name} died."


class JoinSettlementEvent(LifeEvent):
    """Dispatched when a character joins a settlement."""

    __event_id__ = "join-settlement"
    __tablename__ = "join_settlement_event"
    __mapper_args__ = {
        "polymorphic_identity": "join_settlement",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    settlement_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    settlement: GameObject
    character: GameObject

    def __init__(self, character: GameObject, settlement: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.settlement = settlement
        self.character_id = character.uid
        self.settlement_id = settlement.uid

    def __str__(self) -> str:
        return f"{self.character.name} joined settlement, {self.settlement.name}."


class BecomeAdolescentEvent(LifeEvent):
    """Event dispatched when a character becomes an adolescent."""

    __event_id__ = "become-adolescent"
    __tablename__ = "become_adolescent_event"
    __mapper_args__ = {
        "polymorphic_identity": "become_adolescent",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character_id = character.uid
        self.character = character

    def __str__(self) -> str:
        return f"{self.character.name} became an adolescent."


class BecomeYoungAdultEvent(LifeEvent):
    """Event dispatched when a character becomes a young adult."""

    __event_id__ = "become-young-adult"
    __tablename__ = "become_young_adult_event"
    __mapper_args__ = {
        "polymorphic_identity": "become-young-adult",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character_id = character.uid
        self.character = character

    def __str__(self) -> str:
        return f"{self.character.name} became a young adult."


class BecomeAdultEvent(LifeEvent):
    """Event dispatched when a character becomes an adult."""

    __event_id__ = "become-adult"
    __tablename__ = "become_adult_event"
    __mapper_args__ = {
        "polymorphic_identity": "become-adult",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character_id = character.uid
        self.character = character

    def __str__(self) -> str:
        return f"{self.character.name} became an adult."


class BecomeSeniorEvent(LifeEvent):
    """Event dispatched when a character becomes a senior."""

    __event_id__ = "become-senior"
    __tablename__ = "become_senior_event"
    __mapper_args__ = {
        "polymorphic_identity": "become_senior",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(world=character.world)
        self.character_id = character.uid
        self.character = character

    def __str__(self) -> str:
        return f"{self.character.name} became a senior."


class MoveOutOfResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    __event_id__ = "move-out-residence"
    __tablename__ = "move_out_residence_event"
    __mapper_args__ = {
        "polymorphic_identity": "move-out-residence",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject
    residence_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    residence: GameObject

    def __init__(self, character: GameObject, residence: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.character_id = character.uid
        self.residence = residence
        self.residence_id = residence.uid

    def __str__(self) -> str:
        return f"{self.character.name} moved out of their residence, {self.residence.name}."


class MoveIntoResidenceEvent(LifeEvent):
    """Sets the characters current residence."""

    __event_id__ = "move-into-residence"
    __tablename__ = "move_into_residence_event"
    __mapper_args__ = {
        "polymorphic_identity": "move-into-residence",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject
    residence_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    residence: GameObject

    def __init__(self, character: GameObject, residence: GameObject) -> None:
        super().__init__(character.world)
        self.character = character
        self.character_id = character.uid
        self.residence = residence
        self.residence_id = residence.uid

    def __str__(self) -> str:
        return (
            f"{self.character.name} moved into a new residence, {self.residence.name}"
        )


class BirthEvent(LifeEvent):
    """Event dispatched when a child is born."""

    __event_id__ = "birth"
    __tablename__ = "birth_event"
    __mapper_args__ = {
        "polymorphic_identity": "birth",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject

    def __init__(
        self,
        character: GameObject,
    ) -> None:
        super().__init__(character.world)
        self.character = character
        self.character_id = character.uid

    def __str__(self) -> str:
        return f"{self.character.name} was born."


class HaveChildEvent(LifeEvent):
    """Event dispatched when a character has a child."""

    __event_id__ = "have_child"
    __tablename__ = "have_child_event"
    __mapper_args__ = {
        "polymorphic_identity": "have_child",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    child_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    child: GameObject
    birthing_parent_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    birthing_parent: GameObject
    other_parent_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    other_parent: GameObject

    def __init__(
        self,
        birthing_parent: GameObject,
        other_parent: GameObject,
        child: GameObject,
    ) -> None:
        super().__init__(child.world)
        self.child = child
        self.child_id = child.uid
        self.birthing_parent = birthing_parent
        self.birthing_parent_id = birthing_parent.uid
        self.other_parent = other_parent
        self.other_parent_id = other_parent.uid

    def __str__(self) -> str:
        return (
            f"{self.birthing_parent.name} and "
            f"{self.other_parent.name} welcomed a new child, {self.child.name}."
        )


class LeaveJobEvent(LifeEvent):
    """Character leaves job of their own will."""

    __event_id__ = "leave-job"
    __tablename__ = "leave_job_event"
    __mapper_args__ = {
        "polymorphic_identity": "leave-job",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    business_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    role_id: Mapped[str]
    reason: Mapped[str] = mapped_column(default="")
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
        self.character_id = character.uid
        self.business_id = business.uid
        self.role_id = job_role.definition_id
        self.job_role = job_role
        self.reason = reason

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

    __event_id__ = "depart"
    __tablename__ = "depart_event"
    __mapper_args__ = {
        "polymorphic_identity": "depart",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    character: GameObject
    reason: Mapped[str] = mapped_column(default="")

    def __init__(self, character: GameObject, reason: str = "") -> None:
        super().__init__(character.world)
        self.character = character
        self.character_id = character.uid
        self.reason = reason

    def __str__(self):
        return f"{self.character.name} departed from the settlement."


class LayOffEvent(LifeEvent):
    """The character is laid off from their job."""

    __event_id__ = "lay-off"
    __tablename__ = "lay_off_event"
    __mapper_args__ = {
        "polymorphic_identity": "lay-off",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    character_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    business_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    role_id: Mapped[str]
    reason: Mapped[str] = mapped_column(default="")
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
        self.character_id = character.uid
        self.business_id = business.uid
        self.role_id = job_role.definition_id
        self.job_role = job_role
        self.reason = reason

    def __str__(self):
        return (
            f"{self.character.name} was laid off from their job as a {self.job_role.name} "
            f"at {self.business.name}."
        )


class BusinessClosedEvent(LifeEvent):
    """Event emitted when a business closes."""

    __event_id__ = "business-closed"
    __tablename__ = "business_closed_event"
    __mapper_args__ = {"polymorphic_identity": "business-closed"}

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    business_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    reason: Mapped[str] = mapped_column(default="")
    business: GameObject

    def __init__(self, business: GameObject, reason: str = "") -> None:
        super().__init__(business.world)
        self.business_id = business.uid
        self.business = business
        self.reason = reason

    def __str__(self) -> str:
        return f"{self.business.name} has closed for business."


class NewSettlementEvent(LifeEvent):
    """Event dispatched when a settlement is created."""

    __event_id__ = "settlement-added"
    __tablename__ = "settlement_added_event"
    __mapper_args__ = {
        "polymorphic_identity": "settlement-added",
    }

    event_id: Mapped[int] = mapped_column(
        ForeignKey("life_events.event_id"), primary_key=True, autoincrement=True
    )
    settlement_id: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    settlement: GameObject

    def __init__(self, settlement: GameObject) -> None:
        super().__init__(settlement.world)
        self.settlement_id = settlement.uid
        self.settlement = settlement

    def __str__(self) -> str:
        return f"Created new settlement, {self.settlement.name}."
