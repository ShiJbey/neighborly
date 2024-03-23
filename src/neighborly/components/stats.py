"""Stat System.

This module contains an implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

The code for the stat class is based on Kryzarel's tutorial on YouTube:
https://www.youtube.com/watch?v=SH25f3cXBVc.

"""

from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.ecs import Component, GameData


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
    __allow_unmapped__ = True

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("stat_entry.uid"))
    stat: Mapped[StatEntry] = relationship(
        back_populates="modifiers", foreign_keys=[uid]
    )
    value: Mapped[float]
    """The amount to modify the stat."""
    modifier_type: Mapped[StatModifierType]
    """How the modifier value is applied."""
    order: Mapped[int]
    """The priority of this modifier when calculating final stat values."""
    source: Optional[object] = None
    """The source of the modifier (for debugging purposes)."""


class StatEntry(GameData):
    """Information about a single stat."""

    __tablename__ = "stat_entry"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    value: Mapped[float]
    base_value: Mapped[float]
    modifiers: Mapped[list[StatModifier]] = relationship(back_populates="stat")
    min_value: Mapped[float]
    max_value: Mapped[float]
    is_discrete: Mapped[bool] = mapped_column(default=False)
    uid: Mapped[int] = mapped_column(ForeignKey("stats.uid"))
    component: Mapped[Stats] = relationship(
        back_populates="entries", foreign_keys=[uid]
    )


class Stats(Component):
    """Tracks all the various stats for a GameObject."""

    __tablename__ = "stats"

    entries: Mapped[list[StatEntry]] = relationship(back_populates="component")
