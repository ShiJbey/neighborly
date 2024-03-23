"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

import attrs
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.components.shared import Agent
from neighborly.defs.base_types import StatModifierData
from neighborly.ecs import Component, GameData, GameObject


class ActiveSocialRule(GameData):
    """A record of a social rule being applied to a relationship."""

    __tablename__ = "active_social_rule"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str]
    description: Mapped[str]
    relationship_id: Mapped[int] = mapped_column(ForeignKey("relationship.uid"))
    relationship: Mapped[Relationship] = relationship(
        foreign_keys=[relationship_id], back_populates="active_rules"
    )


class Relationship(Component):
    """A relationship between agents."""

    __tablename__ = "relationship"

    owner_id: Mapped[int] = mapped_column(ForeignKey("agent.uid"))
    owner: Mapped[Agent] = relationship(foreign_keys=[owner_id])
    target_id: Mapped[int] = mapped_column(ForeignKey("agent.uid"))
    target: Mapped[Agent] = relationship(foreign_keys=[target_id])
    active_rules: Mapped[list[ActiveSocialRule]] = relationship(
        back_populates="relationship"
    )

    def __repr__(self) -> str:
        return f"Relationship(uid={self.uid!r}, owner={self.owner_id!r}, target={self.target_id!r})"


@attrs.define
class SocialRule:
    """A rule that modifies a relationship depending on some preconditions."""

    rule_id: str
    """Unique identifier for this rule."""
    preconditions: list[str]
    """Conditions that need to be met to apply the rule."""
    modifiers: list[StatModifierData]
    """Side-effects of the rule applied to a relationship."""
    description: str
    """Description of the social rule."""

    def check_preconditions(self, obj: GameObject) -> bool:
        """Check that a relationship passes all the preconditions."""
        raise NotImplementedError()
