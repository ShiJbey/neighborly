"""Stat System.

This module contains an implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

The code for the stat class is based on Kryzarel's tutorial on YouTube:
https://www.youtube.com/watch?v=SH25f3cXBVc.

"""

from __future__ import annotations

import enum

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.ecs import GameData


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    FLAT = 100
    """Adds a constant value to the base value."""

    PERCENT_ADD = 200
    """Additively stacks percentage increases on a modified stat."""

    PERCENT_MULTIPLY = 300
    """Multiplicatively stacks percentage increases on a modified stat."""


class StatModifier(GameData):
    """Stat modifiers provide buffs and de-buffs to the value of stat components.

    Modifiers are applied to stats in ascending-priority-order. So, stats with lower
    orders are added first.
    """

    __tablename__ = "stat_modifier"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    stat_key: Mapped[int] = mapped_column(ForeignKey("stats.key"))
    stat: Mapped[Stat] = relationship(
        back_populates="modifiers", foreign_keys=[stat_key]
    )
    value: Mapped[float]
    """The amount to modify the stat."""
    modifier_type: Mapped[StatModifierType]
    """How the modifier value is applied."""
    order: Mapped[int]
    """The priority of this modifier when calculating final stat values."""
    source: Mapped[str]
    """The source of the modifier."""


STAT_MIN_VALUE = 0
STAT_MAX_VALUE = 255


class Stat(GameData):
    """A numerical stat associated with a character."""

    __tablename__ = "stats"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    value: Mapped[float]
    base_value: Mapped[float]
    modifiers: Mapped[list[StatModifier]] = relationship(back_populates="stat")
    is_discrete: Mapped[bool] = mapped_column(default=False)
    gameobject: Mapped[int]
