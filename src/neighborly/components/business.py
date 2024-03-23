"""Business Components.

This module contains class definitions for components and classes that model businesses
in the settlement and character occupations.

"""

from __future__ import annotations

import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.components.character import Character
from neighborly.components.settlement import District
from neighborly.ecs import Component, GameData


class BusinessStatus(enum.Enum):
    """Current activity status of the business."""

    CLOSED = enum.auto()
    OPEN = enum.auto()
    PENDING = enum.auto()


class JobOpening(GameData):
    """Information about job openings at a business."""

    __tablename__ = "job_opening"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """Unique ID among other job openings."""
    role_id: Mapped[str]
    """The ID of the job role definition."""
    quantity: Mapped[int]
    """The number of this role available at a business"""
    business_id: Mapped[int] = mapped_column(ForeignKey("business.uid"))
    """The UID of the business that has this opening."""
    business: Mapped[Business] = relationship(
        foreign_keys=[business_id], back_populates="job_openings"
    )
    """A reference to the business that has this job opening."""

    def __repr__(self) -> str:
        return (
            f"JobOpening(role_id={self.role_id!r}, quantity={self.quantity!r}, "
            f"business_id={self.business_id!r})"
        )

    def __str__(self) -> str:
        return (
            f"JobOpening(role_id={self.role_id!r}, quantity={self.quantity!r}, "
            f"business_id={self.business_id!r})"
        )


class Business(Component):
    """A business agent."""

    __tablename__ = "business"

    name: Mapped[str]
    owner_role_id: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey("character.uid"))
    owner: Mapped[Character] = relationship(foreign_keys=[owner_id])
    employees: Mapped[list[Occupation]] = relationship(back_populates="business")
    district_id: Mapped[int] = mapped_column(ForeignKey("district.uid"))
    job_openings: Mapped[list[JobOpening]] = relationship(back_populates="business")
    district: Mapped[District] = relationship(foreign_keys=[district_id])
    status: Mapped[BusinessStatus] = mapped_column(default=BusinessStatus.PENDING)

    def __str__(self) -> str:
        return (
            f"Business(uid={self.uid!r}, name={self.name!r}, "
            f"status={self.status.name!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Business(uid={self.uid!r}, name={self.name!r}, "
            f"status={self.status.name!r})"
        )


class Occupation(Component):
    """Information about a character's employment status."""

    __tablename__ = "occupation"

    role_id: Mapped[str]
    business_id: Mapped[int] = mapped_column(ForeignKey("business.uid"))
    business: Mapped[Business] = relationship(
        back_populates="employees", foreign_keys=[business_id]
    )
    start_date: Mapped[str]

    def __repr__(self) -> str:
        return (
            f"Occupation(role_id={self.role_id!r}, business_id={self.business_id!r}, "
            f"start_date={self.start_date!r})"
        )

    def __str__(self) -> str:
        return (
            f"Occupation(role_id={self.role_id!r}, business_id={self.business_id!r}, "
            f"start_date={self.start_date!r})"
        )
