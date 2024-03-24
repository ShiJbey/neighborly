"""Trait system

This module contains class definitions for implementing the trait system.

"""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import GameData


class Trait(GameData):
    """A trait attached to a GameObject."""

    __tablename__ = "traits"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    gameobject: Mapped[int]
    trait_id: Mapped[str]
    description: Mapped[str]
    has_duration: Mapped[bool]
    duration: Mapped[int]

    def __str__(self) -> str:
        return (
            f"Trait(gameobject={self.gameobject!r}, trait_id={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Trait(gameobject={self.gameobject!r}, trait_id={self.trait_id!r}, "
            f"duration={self.duration!r}, description={self.description!r})"
        )
