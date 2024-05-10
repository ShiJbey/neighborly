"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in
the simulation.

"""

from __future__ import annotations

from typing import Any, Optional

import attrs

from neighborly.components.business import JobRole
from neighborly.ecs import Component


@attrs.define
class CharacterSpawnTableEntry:
    """Data for a single row in a CharacterSpawnTable."""

    definition_id: str
    """The ID of a character definition."""
    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""


class CharacterSpawnTable(Component):
    """Manages the frequency that character defs are spawned."""

    __slots__ = ("table",)

    table: dict[str, CharacterSpawnTableEntry]
    """Spawn table data."""

    def __init__(
        self,
        entries: Optional[list[CharacterSpawnTableEntry]] = None,
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = {}

        if entries:
            for entry in entries:
                self.table[entry.definition_id] = entry

    def to_dict(self) -> dict[str, Any]:
        return {}


@attrs.define
class BusinessSpawnTableEntry:
    """A single row of data from a BusinessSpawnTable."""

    definition_id: str
    """The ID of a business definition."""
    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""
    max_instances: int
    """Max number of instances of the business that may exist."""
    min_population: int
    """The minimum settlement population required to spawn."""
    instances: int
    """The current number of active instances."""
    owner_role: JobRole
    """The role of the owner."""


class BusinessSpawnTable(Component):
    """Manages the frequency that business types are spawned"""

    __slots__ = ("table",)

    table: dict[str, BusinessSpawnTableEntry]
    """Table data with entries."""

    def __init__(
        self,
        entries: Optional[list[BusinessSpawnTableEntry]] = None,
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = {}

        if entries:
            for entry in entries:
                self.table[entry.definition_id] = entry

    def increment_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID of the entry to update.
        """
        self.table[definition_id].instances += 1

    def decrement_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID of the entry to update.
        """
        self.table[definition_id].instances -= 1

    def to_dict(self) -> dict[str, Any]:
        return {}


@attrs.define
class ResidenceSpawnTableEntry:
    """Data for a single row in a ResidenceSpawnTable."""

    definition_id: str
    """The ID of a residence definition."""
    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""
    required_population: int
    """The number of people that need to live in the district."""
    is_multifamily: bool
    """Is this a multifamily residential building."""
    instances: int
    """The number of instances of this residence type"""
    max_instances: int
    """Max number of instances of the business that may exist."""


class ResidenceSpawnTable(Component):
    """Manages the frequency that residence types are spawned"""

    __slots__ = ("table",)

    table: dict[str, ResidenceSpawnTableEntry]
    """Column names mapped to column data."""

    def __init__(
        self,
        entries: Optional[list[ResidenceSpawnTableEntry]] = None,
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = {}

        if entries:
            for entry in entries:
                self.table[entry.definition_id] = entry

    def increment_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID of the entry to update.
        """
        self.table[definition_id].instances += 1

    def decrement_count(self, definition_id: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        definition_id
            The definition ID of the entry to update.
        """
        self.table[definition_id].instances -= 1

    def to_dict(self) -> dict[str, Any]:
        return {}
