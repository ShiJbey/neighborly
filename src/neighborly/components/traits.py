"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

import dataclasses
from typing import ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.ecs import Component, Event, EventEmitter, GameData, GameObject


class TraitInstance(GameData):
    """Instance information about a trait."""

    __tablename__ = "trait_instance"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("traits.uid"))
    trait_id: Mapped[str]
    description: Mapped[str]
    has_duration: Mapped[bool]
    duration: Mapped[int]
    traits: Mapped[Traits] = relationship(
        back_populates="instances", foreign_keys=[uid]
    )

    def __str__(self) -> str:
        return (
            f"TraitInstance(uid={self.uid!r}, trait_id={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def __repr__(self) -> str:
        return (
            f"TraitInstance(uid={self.uid!r}, trait_id={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )


@dataclasses.dataclass(kw_only=True)
class TraitAddedEvent(Event):
    """Event emitted when a stat's value changes."""

    gameobject: GameObject
    trait_id: str


@dataclasses.dataclass(kw_only=True)
class TraitRemovedEvent(Event):
    """Event emitted when a stat's value changes."""

    gameobject: GameObject
    trait_id: str


class Traits(Component):
    """Tracks a GameObject's traits."""

    __tablename__ = "traits"

    on_trait_added: ClassVar[EventEmitter[TraitAddedEvent]] = EventEmitter()
    on_trait_removed: ClassVar[EventEmitter[TraitRemovedEvent]] = EventEmitter()

    instances: Mapped[list[TraitInstance]] = relationship(back_populates="traits")
    """Trait instances associated with the GameObject."""

    def __str__(self) -> str:
        trait_names = [t.trait_id for t in self.instances]
        return f"Traits(uid={self.uid!r}, traits={trait_names!r})"

    def __repr__(self) -> str:
        trait_names = [t.trait_id for t in self.instances]
        return f"Traits(uid={self.uid!r}, traits={trait_names!r})"
