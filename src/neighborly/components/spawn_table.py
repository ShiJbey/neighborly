"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in
the simulation.

"""

from __future__ import annotations

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from neighborly.ecs import Component, GameData


class CharacterSpawnTableEntry(GameData):
    """Configuration parameters for selecting what characters to spawn."""

    __tablename__ = "character_spawn_table_entry"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    definition_id: Mapped[str]
    """The ID of a character definition."""
    spawn_frequency: Mapped[int] = mapped_column(default=1)
    """The relative frequency that this entry should spawn relative to others."""
    uid: Mapped[int] = mapped_column(ForeignKey("character_spawn_table.uid"))
    """The UID of the GameObject that owns this table entry."""
    spawn_table: Mapped[CharacterSpawnTable] = relationship(
        back_populates="entries", foreign_keys=[uid]
    )
    """The spawn table this entry belongs to."""


class CharacterSpawnTable(Component):
    """A collection of character spawn table entries."""

    __tablename__ = "character_spawn_table"

    entries: Mapped[list[CharacterSpawnTableEntry]] = relationship(
        back_populates="spawn_table"
    )
    """The entries that belong to this table."""


class BusinessSpawnTableEntry(GameData):
    """A single row of data from a BusinessSpawnTable."""

    __tablename__ = "business_spawn_table_entry"

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
    uid: Mapped[int] = mapped_column(ForeignKey("business_spawn_table.uid"))
    """The UID of the GameObject that owns this table entry."""
    spawn_table: Mapped[BusinessSpawnTable] = relationship(
        back_populates="entries", foreign_keys=[uid]
    )
    """The spawn table this entry belongs to."""


class BusinessSpawnTable(Component):
    """A collection of business spawn table entries."""

    __tablename__ = "business_spawn_table"

    entries: Mapped[list[BusinessSpawnTableEntry]] = relationship(
        back_populates="spawn_table"
    )
    """The entries that belong to this table."""

    def increment_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID to update
        """
        for entry in self.entries:
            if entry.definition_id == definition_id:
                entry.instances += 1

    def decrement_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID to update
        """
        for entry in self.entries:
            if entry.definition_id == definition_id:
                entry.instances -= 1


class ResidenceSpawnTableEntry(GameData):
    """Configuration parameters for selecting what characters to spawn."""

    __tablename__ = "residence_spawn_table_entry"

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
    uid: Mapped[int] = mapped_column(ForeignKey("residence_spawn_table.uid"))
    """The UID of the GameObject that owns this table entry."""
    spawn_table: Mapped[ResidenceSpawnTable] = relationship(
        back_populates="entries", foreign_keys=[uid]
    )
    """The spawn table this entry belongs to."""


class ResidenceSpawnTable(Component):
    """A collection of residence spawn table entries."""

    __tablename__ = "residence_spawn_table"

    entries: Mapped[list[ResidenceSpawnTableEntry]] = relationship(
        back_populates="spawn_table"
    )
    """The entries that belong to this table."""

    def increment_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID to update
        """
        for entry in self.entries:
            if entry.definition_id == definition_id:
                entry.instances += 1

    def decrement_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID to update
        """
        for entry in self.entries:
            if entry.definition_id == definition_id:
                entry.instances -= 1
