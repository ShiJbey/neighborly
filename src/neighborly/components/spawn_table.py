"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in
the simulation.

"""

from __future__ import annotations

from typing import Any, Sequence, TypedDict, cast

import polars as pl

from neighborly.ecs import Component


class CharacterSpawnTableEntry(TypedDict):
    """Data for a single row in a CharacterSpawnTable."""

    name: str
    """The name of an entry."""
    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""


class CharacterSpawnTable(Component):
    """Manages the frequency that character defs are spawned."""

    __slots__ = ("table",)

    table: pl.DataFrame
    """Column names mapped to column data."""

    def __init__(self, entries: list[CharacterSpawnTableEntry]) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = pl.from_dicts(
            cast(Sequence[dict[str, Any]], entries),
            schema=[("name", str), ("spawn_frequency", int)],
        )

    def to_dict(self) -> dict[str, Any]:
        return {}


class BusinessSpawnTableEntry(TypedDict):
    """A single row of data from a BusinessSpawnTable."""

    name: str
    """The name of an entry."""
    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""
    max_instances: int
    """Max number of instances of the business that may exist."""
    min_population: int
    """The minimum settlement population required to spawn."""
    instances: int
    """The current number of active instances."""


class BusinessSpawnTable(Component):
    """Manages the frequency that business types are spawned"""

    __slots__ = ("table",)

    table: pl.DataFrame
    """Table data with entries."""

    def __init__(self, entries: list[BusinessSpawnTableEntry]) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = pl.from_dicts(
            cast(Sequence[dict[str, Any]], entries),
            schema=[
                ("name", str),
                ("spawn_frequency", int),
                ("max_instances", int),
                ("min_population", int),
                ("instances", int),
            ],
        )

    def increment_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self.table = self.table.with_columns(  # type: ignore
            instances=(
                pl.when(pl.col("name") == name)  # type: ignore
                .then(pl.col("instances") + 1)
                .otherwise(pl.col("instances"))
            )
        )

    def decrement_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self.table = self.table.with_columns(  # type: ignore
            instances=(
                pl.when(pl.col("name") == name)  # type: ignore
                .then(pl.col("instances") - 1)
                .otherwise(pl.col("instances"))
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {}


class ResidenceSpawnTableEntry(TypedDict):
    """Data for a single row in a ResidenceSpawnTable."""

    name: str
    """The name of an entry."""
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

    table: pl.DataFrame
    """Column names mapped to column data."""

    def __init__(self, entries: list[ResidenceSpawnTableEntry]) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        super().__init__()
        self.table = pl.from_dicts(
            cast(Sequence[dict[str, Any]], entries),
            schema=[
                ("name", str),
                ("spawn_frequency", int),
                ("required_population", int),
                ("is_multifamily", bool),
                ("instances", int),
                ("max_instances", int),
            ],
        )

    def increment_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self.table = self.table.with_columns(  # type: ignore
            instances=(
                pl.when(pl.col("name") == name)  # type: ignore
                .then(pl.col("instances") + 1)
                .otherwise(pl.col("instances"))
            )
        )

    def decrement_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self.table = self.table.with_columns(  # type: ignore
            instances=(
                pl.when(pl.col("name") == name)  # type: ignore
                .then(pl.col("instances") - 1)
                .otherwise(pl.col("instances"))
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {}
