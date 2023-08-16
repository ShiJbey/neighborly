"""Spawn Tables.

Spawn tables are used to manage the relative frequency of certain content appearing in 
the simulation.

"""

from __future__ import annotations

import random
import re
from typing import ClassVar, List, Optional, TypedDict

import pandas as pd

from neighborly.ecs import World
from neighborly.settlement import Settlement
from neighborly.time import SimDateTime


class CharacterSpawnTableEntry(TypedDict):
    """Data for a single row in a CharacterSpawnTable."""

    name: str
    """The name of an entry."""

    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""


class CharacterSpawnTable:
    """Manages the frequency that character types are spawned."""

    __slots__ = "_table"

    _table: pd.DataFrame
    """Contains spawn table data."""

    _TABLE_SCHEMA: ClassVar[List[str]] = ["name", "spawn_frequency"]

    def __init__(
        self, entries: Optional[List[CharacterSpawnTableEntry]] = None
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        self._table = pd.DataFrame(columns=CharacterSpawnTable._TABLE_SCHEMA)

        if entries:
            self._table = pd.DataFrame.from_records(
                entries, columns=CharacterSpawnTable._TABLE_SCHEMA
            )

    def update(self, entry: CharacterSpawnTableEntry) -> None:
        """Add an entry to the spawn table or overwrite an existing entry.

        Parameters
        ----------
        entry
            Row data.
        """
        new_data = pd.DataFrame.from_records(
            [entry], columns=CharacterSpawnTable._TABLE_SCHEMA
        )

        if entry["name"] in self._table["name"]:
            self._table.update(new_data)
        else:
            self._table = pd.concat([self._table, new_data])

    def choose_random(self, rng: random.Random) -> str:
        """Performs a weighted random selection across all entries.

        Parameters
        ----------
        rng
            A Random instance.

        Returns
        -------
        str
            The name of an entry.
        """

        if len(self._table) == 0:
            raise IndexError("Character spawn table is empty")

        return rng.choices(
            population=self._table["name"].to_list(),
            weights=self._table["spawn_frequency"].to_list(),
            k=1,
        )[0]

    def get_matching_names(self, *patterns: str) -> List[str]:
        """Get all entries with names that match the given regex strings.

        Parameters
        ----------
        *patterns
            Glob-patterns of names to check for.

        Returns
        -------
        List[str]
            The names of entries in the table that match the pattern.
        """

        matches: List[str] = []

        name: str  # Type hint the loop variable
        for name in self._table["name"]:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._table.__len__()


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

    year_available: int
    """The minimum year that this business can spawn."""

    year_obsolete: int
    """The maximum year that this business can spawn."""


class BusinessSpawnTable:
    """Manages the frequency that business types are spawned"""

    __slots__ = "_table"

    _TABLE_SCHEMA: ClassVar[List[str]] = [
        "name",
        "spawn_frequency",
        "max_instances",
        "min_population",
        "year_available",
        "year_obsolete",
        "instances",
    ]

    _table: pd.DataFrame
    """Table data with entries."""

    def __init__(self, entries: Optional[List[BusinessSpawnTableEntry]] = None) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries in the form [{"name": ..., "frequency": ...}, ...],
            by default None
        """
        self._table = pd.DataFrame(columns=BusinessSpawnTable._TABLE_SCHEMA)

        if entries:
            for entry in entries:
                self.update(entry)

    def update(self, entry: BusinessSpawnTableEntry) -> None:
        """Add an entry to the spawn table or overwrite an existing entry.

        Parameters
        ----------
        entry
            Row data
        """
        new_data = pd.DataFrame.from_records(
            [{**entry, "instances": 0}],
            columns=BusinessSpawnTable._TABLE_SCHEMA,
        )

        if entry["name"] in self._table["name"]:
            self._table.update(new_data)
        else:
            self._table = pd.concat([self._table, new_data])

    def increment_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self._table.loc[self._table["name"] == name, "instances"] += 1

    def decrement_count(self, name: str) -> None:
        """Increment the instance count for an entry.

        Parameters
        ----------
        name
            The name of entry to update
        """
        self._table.loc[self._table["name"] == name, "instances"] -= 1

    def get_frequency(self, name: str) -> int:
        return self._table.loc[self._table["name"] == name, "spawn_frequency"].item()

    def choose_random(self, world: World) -> Optional[str]:
        """Randomly choose entry that may be built in the given settlement.

        Parameters
        ----------
        world
            The World instance

        Returns
        -------
        str or None
            Returns the name of an entry or None if no eligible entries
            were found.
        """

        if len(self) == 0:
            raise IndexError("Business spawn table is empty")

        settlement = world.resource_manager.get_resource(Settlement)
        date = world.resource_manager.get_resource(SimDateTime)
        rng = world.resource_manager.get_resource(random.Random)

        eligible_entries = self._table[
            (self._table["max_instances"] > self._table["instances"])
            & (self._table["min_population"] <= settlement.population)
            & (self._table["year_available"] <= date.year)
            & (self._table["year_obsolete"] > date.year)
        ]

        if len(eligible_entries) > 0:
            return rng.choices(
                population=self._table["name"].to_list(),
                weights=self._table["spawn_frequency"].to_list(),
                k=1,
            )[0]

        return None

    def get_eligible(self, world: World) -> List[str]:
        """Get all business entries that can be built in the given settlement"""
        settlement = world.resource_manager.get_resource(Settlement)
        date = world.resource_manager.get_resource(SimDateTime)

        eligible_entries = self._table[
            (self._table["max_instances"] > self._table["instances"])
            & (self._table["min_population"] <= settlement.population)
            & (self._table["year_available"] <= date.year)
            & (self._table["year_obsolete"] > date.year)
        ]

        return eligible_entries["name"].to_list()

    def get_matching_names(self, *patterns: str) -> List[str]:
        """Get all entries with names that match the given regex strings.

        Parameters
        ----------
        *patterns: Tuple[str, ...]
            Glob-patterns of names to check for.

        Returns
        -------
        List[str]
            The names of entries in the table that match the pattern.
        """

        matches: List[str] = []

        for name in self._table["name"]:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._table.__len__()


class ResidenceSpawnTableEntry(TypedDict):
    """Data for a single row in a ResidenceSpawnTable."""

    name: str
    """The name of an entry."""

    spawn_frequency: int
    """The relative frequency that this entry should spawn relative to others."""


class ResidenceSpawnTable:
    """Manages the frequency that residence types are spawned"""

    __slots__ = "_table"

    _TABLE_SCHEMA: ClassVar[List[str]] = ["name", "spawn_frequency"]

    _table: pd.DataFrame
    """Contains spawn table data."""

    def __init__(
        self, entries: Optional[List[ResidenceSpawnTableEntry]] = None
    ) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries.
        """
        self._table = pd.DataFrame(columns=ResidenceSpawnTable._TABLE_SCHEMA)

        if entries:
            for entry in entries:
                self.update(entry)

    def update(self, entry: ResidenceSpawnTableEntry) -> None:
        """Add an entry to the spawn table or overwrite an existing entry.

        Parameters
        ----------
        entry
            Row data.
        """
        new_data = pd.DataFrame.from_records(
            [entry], columns=ResidenceSpawnTable._TABLE_SCHEMA
        )

        if entry["name"] in self._table["name"]:
            self._table.update(new_data)
        else:
            self._table = pd.concat([self._table, new_data])

    def choose_random(self, rng: random.Random) -> str:
        """Performs a weighted random selection across all entries.

        Parameters
        ----------
        rng
            A Random instance.

        Returns
        -------
        str
            The name of an entry.
        """

        if len(self._table) == 0:
            raise IndexError("Residence spawn table is empty")

        return rng.choices(
            population=self._table["name"].to_list(),
            weights=self._table["spawn_frequency"].to_list(),
            k=1,
        )[0]

    def get_matching_names(self, *patterns: str) -> List[str]:
        """Get all entries with names that match the given regex strings.

        Parameters
        ----------
        *patterns
            Glob-patterns of names to check for.

        Returns
        -------
        List[str]
            The names of entries in the table that match the pattern.
        """

        matches: List[str] = []

        name: str  # Type hint the loop variable
        for name in self._table["name"]:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._table.__len__()
