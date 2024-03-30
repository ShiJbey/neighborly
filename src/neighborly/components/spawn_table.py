"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in
the simulation.

"""

from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from neighborly.ecs import Component, GameData, GameObject


class CharacterSpawnTableEntry(GameData):
    """Data for a single row in a CharacterSpawnTable."""

    __tablename__ = "character_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    name: Mapped[str]
    """The name of an entry."""
    spawn_frequency: Mapped[int]
    """The relative frequency that this entry should spawn relative to others."""


class CharacterSpawnTable(Component):
    """Manages the frequency that character defs are spawned."""

    __slots__ = ("table",)

    table: dict[str, CharacterSpawnTableEntry]
    """Spawn table data."""

    def __init__(
        self, gameobject: GameObject, entries: list[CharacterSpawnTableEntry]
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__(gameobject)
        self.table = {}

        with gameobject.world.session.begin() as session:
            for entry in entries:
                entry.uid = gameobject.uid
                self.table[entry.name] = entry
                session.add(entry)

    def __len__(self) -> int:
        return len(self.table)

    def to_dict(self) -> dict[str, Any]:
        return {}


class BusinessSpawnTableEntry(GameData):
    """A single row of data from a BusinessSpawnTable."""

    __tablename__ = "business_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    name: Mapped[str]
    """The name of an entry."""
    spawn_frequency: Mapped[int]
    """The relative frequency that this entry should spawn relative to others."""
    max_instances: Mapped[int]
    """Max number of instances of the business that may exist."""
    min_population: Mapped[int]
    """The minimum settlement population required to spawn."""
    instances: Mapped[int]
    """The current number of active instances."""


class BusinessSpawnTable(Component):
    """Manages the frequency that business types are spawned"""

    __slots__ = ("table",)

    table: dict[str, BusinessSpawnTableEntry]
    """Table data with entries."""

    def __init__(
        self, gameobject: GameObject, entries: list[BusinessSpawnTableEntry]
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__(gameobject)
        self.table = {}

        with gameobject.world.session.begin() as session:
            for entry in entries:
                entry.uid = gameobject.uid
                self.table[entry.name] = entry
                session.add(entry)

    def increment_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        with self.gameobject.world.session.begin() as session:
            entry = session.scalar(
                select(BusinessSpawnTableEntry)
                .where(BusinessSpawnTableEntry.uid == self.gameobject.uid)
                .where(BusinessSpawnTableEntry.name == name)
            )

            if entry:
                entry.instances += 1
                session.add(entry)

    def decrement_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        with self.gameobject.world.session.begin() as session:
            entry = session.scalar(
                select(BusinessSpawnTableEntry)
                .where(BusinessSpawnTableEntry.uid == self.gameobject.uid)
                .where(BusinessSpawnTableEntry.name == name)
            )

            if entry:
                entry.instances -= 1
                session.add(entry)

    def to_dict(self) -> dict[str, Any]:
        return {}

    def __len__(self) -> int:
        return len(self.table)


class ResidenceSpawnTableEntry(GameData):
    """Data for a single row in a ResidenceSpawnTable."""

    __tablename__ = "residence_spawn_table"

    key: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uid: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    name: Mapped[str]
    """The name of an entry."""
    spawn_frequency: Mapped[int]
    """The relative frequency that this entry should spawn relative to others."""
    required_population: Mapped[int]
    """The number of people that need to live in the district."""
    is_multifamily: Mapped[bool]
    """Is this a multifamily residential building."""
    instances: Mapped[int]
    """The number of instances of this residence type"""
    max_instances: Mapped[int]
    """Max number of instances of the business that may exist."""


class ResidenceSpawnTable(Component):
    """Manages the frequency that residence types are spawned"""

    __slots__ = ("table",)

    table: dict[str, ResidenceSpawnTableEntry]
    """Column names mapped to column data."""

    def __init__(
        self, gameobject: GameObject, entries: list[ResidenceSpawnTableEntry]
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__(gameobject)
        self.table = {}

        with gameobject.world.session.begin() as session:
            for entry in entries:
                entry.uid = gameobject.uid
                self.table[entry.name] = entry
                session.add(entry)

    def increment_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        with self.gameobject.world.session.begin() as session:
            entry = session.scalar(
                select(ResidenceSpawnTableEntry)
                .where(ResidenceSpawnTableEntry.uid == self.gameobject.uid)
                .where(ResidenceSpawnTableEntry.name == name)
            )

            if entry:
                entry.instances += 1
                session.add(entry)

    def decrement_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        with self.gameobject.world.session.begin() as session:
            entry = session.scalar(
                select(ResidenceSpawnTableEntry)
                .where(ResidenceSpawnTableEntry.uid == self.gameobject.uid)
                .where(ResidenceSpawnTableEntry.name == name)
            )

            if entry:
                entry.instances -= 1
                session.add(entry)

    def __len__(self) -> int:
        return len(self.table)

    def to_dict(self) -> dict[str, Any]:
        return {}
