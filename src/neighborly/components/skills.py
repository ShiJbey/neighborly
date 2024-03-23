"""Skill system.

"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.components.stats import StatModifierType
from neighborly.ecs import Component, GameData


class SkillsModifier(GameData):
    """Applies a numerical modifier to a skill entry."""

    __tablename__ = "skill_modifier"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("skill_entry.uid"))
    skill: Mapped[SkillEntry] = relationship(
        back_populates="modifiers", foreign_keys=[uid]
    )
    value: Mapped[float]
    """The amount to modify the stat."""
    modifier_type: Mapped[StatModifierType]
    """How the modifier value is applied."""
    order: Mapped[int]
    """The priority of this modifier when calculating final stat values."""
    source: Mapped[str] = mapped_column(nullable=True)
    """The source of the modifier."""


class SkillEntry(GameData):
    """Information about a single stat."""

    __tablename__ = "skill_entry"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    value: Mapped[float]
    base_value: Mapped[float]
    modifiers: Mapped[list[SkillsModifier]] = relationship(back_populates="skill")
    is_discrete: Mapped[bool] = mapped_column(default=False)
    uid: Mapped[int] = mapped_column(ForeignKey("skills.uid"))
    component: Mapped[Skills] = relationship(
        back_populates="entries", foreign_keys=[uid]
    )


class Skills(Component):
    """Tracks all the various skills for a GameObject."""

    __tablename__ = "skills"

    entries: Mapped[list[SkillEntry]] = relationship(back_populates="component")
