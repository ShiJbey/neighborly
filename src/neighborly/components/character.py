"""Components for representing Characters.

"""

from __future__ import annotations

import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component


class LifeStage(enum.IntEnum):
    """An enumeration of all the various life stages aging characters pass through."""

    CHILD = 0
    ADOLESCENT = 1
    YOUNG_ADULT = 2
    ADULT = 3
    SENIOR = 4


class Sex(enum.IntEnum):
    """The characters current sex."""

    MALE = enum.auto()
    FEMALE = enum.auto()
    NOT_SPECIFIED = enum.auto()


class Character(Component):
    """A character agent."""

    __tablename__ = "character"

    name: Mapped[str]
    last_name: Mapped[str]
    life_stage: Mapped[LifeStage]
    sex: Mapped[Sex]
    species: Mapped[str]

    @property
    def full_name(self) -> str:
        """The full name of the character."""
        return f"{self.name} {self.last_name}"

    def __str__(self) -> str:
        return (
            f"Character(uid={self.uid!r}, full_name={self.full_name!r}, "
            f"life_stage={self.life_stage.name!r}, sex={self.sex.name!r}, "
            f"species={self.species!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Character(uid={self.uid!r}, full_name={self.full_name!r}, "
            f"life_stage={self.life_stage.name!r}, sex={self.sex.name!r}, "
            f"species={self.species!r})"
        )


class Pregnancy(Component):
    """Tags a character as pregnant and tracks relevant information."""

    __tablename__ = "pregnancy"

    partner_id: Mapped[int] = mapped_column(ForeignKey("character.uid"))
    """The GameObject ID of the character that impregnated this character."""
    ordinal_due_date: Mapped[int]
    """The ordinal date the baby is due."""
    due_date: Mapped[str]
    """The string timestamp of the due date."""

    def __str__(self) -> str:
        return (
            f"Pregnancy(partner={self.partner_id!r}, due_date={self.due_date!r}, "
            f"ordinal_due_date={self.ordinal_due_date!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Pregnancy(partner={self.partner_id!r}, due_date={self.due_date!r}, "
            f"ordinal_due_date={self.ordinal_due_date!r})"
        )
