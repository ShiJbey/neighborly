"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in
the simulation.

"""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import GameData


class CharacterSpawnTableEntry(GameData):
    """Configuration parameters for selecting what characters to spawn."""

    __tablename__ = "character_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    definition_id: Mapped[str]
    """The ID of a character definition."""
    spawn_frequency: Mapped[int] = mapped_column(default=1)
    """The relative frequency that this entry should spawn relative to others."""
    gameobject: Mapped[int]
    """The UID of the GameObject that owns this table entry."""


class BusinessSpawnTableEntry(GameData):
    """A single row of data from a BusinessSpawnTable."""

    __tablename__ = "business_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    definition_id: Mapped[str]
    """The ID of a business definition."""
    spawn_frequency: Mapped[int] = mapped_column(default=1)
    """The relative frequency that this entry should spawn relative to others."""
    max_instances: Mapped[int] = mapped_column(default=999_999)
    """Max number of instances of the business that may exist."""
    min_population: Mapped[int] = mapped_column(default=0)
    """The minimum settlement population required to spawn."""
    instances: Mapped[int] = mapped_column(default=0)
    """The current number of active instances."""
    gameobject: Mapped[int]
    """The UID of the GameObject that owns this table entry."""


class ResidenceSpawnTableEntry(GameData):
    """Configuration parameters for selecting what characters to spawn."""

    __tablename__ = "residence_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    definition_id: Mapped[str]
    """The ID of an residence definition."""
    spawn_frequency: Mapped[int] = mapped_column(default=1)
    """The relative frequency that this entry should spawn relative to others."""
    required_population: Mapped[int] = mapped_column(default=0)
    """The number of people that need to live in the district."""
    is_multifamily: Mapped[bool]
    """Is this a multifamily residential building."""
    instances: Mapped[int] = mapped_column(default=0)
    """The number of instances of this residence type"""
    max_instances: Mapped[int] = mapped_column(default=999_999)
    """Max number of instances of the business that may exist."""
    gameobject: Mapped[int]
    """The UID of the GameObject that owns this table entry."""
