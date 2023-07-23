"""Components for defining spawn tables for settlements.

"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

import pandas as pd

from neighborly.core.ecs import GameObject
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime


@dataclass
class CharacterSpawnTableEntry:
    """Data for a single row in a CharacterSpawnTable."""

    name: str
    frequency: int


class CharacterSpawnTableIterator:
    """Custom iterator for character spawn tables."""

    __slots__ = "_table", "_index"

    def __init__(self, table: CharacterSpawnTable) -> None:
        self._table = table
        self._index = 0

    def __iter__(self) -> Iterator[CharacterSpawnTableEntry]:
        return self

    def __next__(self) -> CharacterSpawnTableEntry:
        if self._index < len(self._table):
            item = self._table[self._index]
            self._index += 0
            return item
        else:
            raise StopIteration


class CharacterSpawnTable:
    """Manages the frequency that character prefabs are spawned."""

    __slots__ = "_names", "_frequencies", "_size", "_index_map", "_table"

    _table: pd.DataFrame
    """Contains spawn table data."""

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries in the form [{"name": ..., "frequency": ...}, ...],
            by default None
        """
        # Names and frequencies are separate buffers to optimize random selection.
        # If we stored them as a list of dicts, we would have to iterate the list to
        # get all the spawn frequencies before selecting an entry
        self._names: List[str] = []
        self._frequencies: List[int] = []
        self._index_map: Dict[str, int] = {}
        self._size = 0
        self._table = pd.DataFrame(columns=["name", "spawn_frequency", "species", "culture"])

        if entries:
            self._table = pd.DataFrame.from_records(
                entries,
                columns=["name", "spawn_frequency", "species", "culture"]
            )

    def update(self, name: str, frequency: int = 1) -> None:
        """Add an entry to the spawn table or overwrite an existing entry.

        Parameters
        ----------
        name
            The name of a prefab.
        frequency
            The relative frequency that this prefab should spawn relative to others.
        """

        if entry_index := self._index_map.get(name, None):
            self._frequencies[entry_index] = frequency
        else:
            self._names.append(name)
            self._frequencies.append(frequency)
            self._index_map[name] = self._size
            self._size += 1

    def choose_random(self, rng: random.Random) -> str:
        """Performs a weighted random selection across all prefab names.

        Parameters
        ----------
        rng
            A Random instance.

        Returns
        -------
        str
            The name of a prefab.
        """

        if self._size == 0:
            raise IndexError("Character spawn table is empty")

        return rng.choices(population=self._names, weights=self._frequencies, k=1)[0]

    def get_matching_prefabs(self, *patterns: str) -> List[str]:
        """Get all prefabs with names that match the given regex strings.

        Parameters
        ----------
        *patterns
            Glob-patterns of names to check for.

        Returns
        -------
        List[str]
            The names of prefabs in the table that match the pattern.
        """

        matches: List[str] = []

        for name in self._names:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)

    def __getitem__(self, item: int) -> CharacterSpawnTableEntry:
        return CharacterSpawnTableEntry(
            name=self._names[item], frequency=self._frequencies[item]
        )

    def __iter__(self) -> Iterator[CharacterSpawnTableEntry]:
        return CharacterSpawnTableIterator(self)

    def extend(self, other: CharacterSpawnTable) -> None:
        """Add entries from another table to this table.

        Parameters
        ----------
        other
            The table with new entries
        """

        for entry in other:
            self.update(name=entry.name, frequency=entry.frequency)

    @staticmethod
    def combine(*tables: CharacterSpawnTable) -> CharacterSpawnTable:
        """Create a new table that is a combination of the given tables.

        Parameters
        ----------
        *tables
            The spawn tables to combine.

        Returns
        -------
        CharacterSpawnTable
            A new spawn table.
        """

        combined_table = CharacterSpawnTable()

        for table in tables:
            combined_table.extend(table)

        return combined_table


@dataclass
class BusinessSpawnTableEntry:
    """A single row of data from a BusinessSpawnTable."""

    name: str
    frequency: int
    max_instances: int
    min_population: int
    year_available: int
    year_obsolete: int


class BusinessSpawnTableIterator:
    """Custom iterator for character spawn tables."""

    __slots__ = "_table", "_index"

    def __init__(self, table: BusinessSpawnTable) -> None:
        self._table = table
        self._index = 0

    def __iter__(self) -> Iterator[BusinessSpawnTableEntry]:
        return self

    def __next__(self) -> BusinessSpawnTableEntry:
        if self._index < len(self._table):
            item = self._table[self._index]
            self._index += 0
            return item
        else:
            raise StopIteration


class BusinessSpawnTable:
    """Manages the frequency that business prefabs are spawned"""

    __slots__ = (
        "_names",
        "_frequencies",
        "_max_instances",
        "_min_population",
        "_year_available",
        "_year_obsolete",
        "_size",
        "_index_map",
    )

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries in the form [{"name": ..., "frequency": ...}, ...],
            by default None
        """
        # Names and frequencies are separate buffers to optimize random selection.
        # If we stored them as a list of dicts, we would have to iterate the list to
        # get all the spawn frequencies before selecting an entry
        self._names: List[str] = []
        self._frequencies: List[int] = []
        self._max_instances: List[int] = []
        self._min_population: List[int] = []
        self._year_available: List[int] = []
        self._year_obsolete: List[int] = []
        self._size = 0
        self._index_map: Dict[str, int] = {}

        if entries:
            for entry in entries:
                self.update(**entry)

    def update(
        self,
        name: str,
        frequency: int = 1,
        max_instances: int = 9999,
        min_population: int = 0,
        year_available: int = 0,
        year_obsolete: int = 9999,
    ) -> None:
        """Add an entry to the spawn table or overwrite an existing entry.

        Parameters
        ----------
        name
            The name of a prefab.
        frequency
            The relative frequency that this prefab should spawn relative to others.
            defaults to 1
        max_instances
            Max number of instances of the business that may exist, defaults to 9999.
        min_population
            The minimum settlement population required to spawn, defaults to 0.
        year_available
            The minimum year that this business can spawn, defaults to 0.
        year_obsolete
            The maximum year that this business can spawn, defaults to 9999.
        """
        if entry_index := self._index_map.get(name, None):
            self._frequencies[entry_index] = frequency
            self._max_instances[entry_index] = max_instances
            self._min_population[entry_index] = min_population
            self._year_available[entry_index] = year_available
            self._year_obsolete[entry_index] = year_obsolete
        else:
            self._names.append(name)
            self._frequencies.append(frequency)
            self._max_instances.append(max_instances)
            self._min_population.append(min_population)
            self._year_available.append(year_available)
            self._year_obsolete.append(year_obsolete)
            self._index_map[name] = self._size
            self._size += 1

    def get_frequency(self, name: str) -> int:
        return self._frequencies[self._index_map[name]]

    def choose_random(self, settlement: GameObject) -> Optional[str]:
        """
        Return all business archetypes that may be built
        given the state of the simulation
        """

        if self._size == 0:
            raise IndexError("Business spawn table is empty")

        world = settlement.world
        settlement_comp = settlement.get_component(Settlement)
        date = world.resource_manager.get_resource(SimDateTime)
        rng = world.resource_manager.get_resource(random.Random)

        choices: List[str] = []
        weights: List[int] = []

        for i in range(self._size):
            if (
                settlement_comp.business_counts[self._names[i]] < self._max_instances[i]
                and settlement_comp.population >= self._min_population[i]
                and (self._year_available[i] <= date.year < self._year_obsolete[i])
            ):
                choices.append(self._names[i])
                weights.append(self._frequencies[i])

        if choices:
            # Choose an archetype at random
            return rng.choices(population=choices, weights=weights, k=1)[0]

        return None

    def get_eligible(self, settlement: GameObject) -> List[str]:
        """Get all business prefabs that can be built in the given settlement"""
        world = settlement.world
        settlement_comp = settlement.get_component(Settlement)
        date = world.resource_manager.get_resource(SimDateTime)

        matches: List[str] = []

        for i in range(self._size):
            if (
                settlement_comp.business_counts[self._names[i]] < self._max_instances[i]
                and settlement_comp.population >= self._min_population[i]
                and (self._year_available[i] <= date.year < self._year_obsolete[i])
            ):
                matches.append(self._names[i])

        return matches

    def get_matching_prefabs(self, *patterns: str) -> List[str]:
        """
        Get all prefabs with names that match the given regex strings

        Parameters
        ----------
        *patterns: Tuple[str, ...]
            Glob-patterns of names to check for

        Returns
        -------
        List[str]
            The names of prefabs in the table that match the pattern
        """

        matches: List[str] = []

        for name in self._names:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)

    def __getitem__(self, item: int) -> BusinessSpawnTableEntry:
        return BusinessSpawnTableEntry(
            name=self._names[item],
            frequency=self._frequencies[item],
            max_instances=self._max_instances[item],
            min_population=self._min_population[item],
            year_available=self._year_available[item],
            year_obsolete=self._year_obsolete[item],
        )

    def __iter__(self) -> Iterator[BusinessSpawnTableEntry]:
        return BusinessSpawnTableIterator(self)

    def extend(self, other: BusinessSpawnTable) -> None:
        """Add entries from another table to this table.

        Parameters
        ----------
        other
            The table with new entries
        """

        for entry in other:
            self.update(
                name=entry.name,
                frequency=entry.frequency,
                max_instances=entry.max_instances,
                min_population=entry.min_population,
                year_available=entry.year_available,
                year_obsolete=entry.year_obsolete,
            )

    @staticmethod
    def combine(*tables: BusinessSpawnTable) -> BusinessSpawnTable:
        """Create a new table that is a combination of the given tables.

        Parameters
        ----------
        *tables
            The spawn tables to combine.

        Returns
        -------
        CharacterSpawnTable
            A new spawn table.
        """

        combined_table = BusinessSpawnTable()

        for table in tables:
            combined_table.extend(table)

        return combined_table


@dataclass
class ResidenceSpawnTableEntry:
    """Data for a single row in a ResidenceSpawnTable."""

    name: str
    frequency: int


class ResidenceSpawnTableIterator:
    """Custom iterator for character spawn tables."""

    __slots__ = "_table", "_index"

    def __init__(self, table: ResidenceSpawnTable) -> None:
        self._table = table
        self._index = 0

    def __iter__(self) -> Iterator[ResidenceSpawnTableEntry]:
        return self

    def __next__(self) -> ResidenceSpawnTableEntry:
        if self._index < len(self._table):
            item = self._table[self._index]
            self._index += 0
            return item
        else:
            raise StopIteration


class ResidenceSpawnTable:
    """Manages the frequency that residence prefabs are spawned"""

    __slots__ = "_names", "_frequencies", "_size", "_index_map"

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Parameters
        ----------
        entries : Optional[List[Dict[str, Any]]], optional
            Starting entries in the form [{"name": ..., "frequency": ...}, ...],
            by default None
        """
        # Names and frequencies are separate buffers to optimize random selection.
        # If we stored them as a list of dicts, we would have to iterate the list to
        # get all the spawn frequencies before selecting an entry
        self._names: List[str] = []
        self._frequencies: List[int] = []
        self._index_map: Dict[str, int] = {}
        self._size = 0

        if entries:
            for entry in entries:
                self.update(**entry)

    def update(self, name: str, frequency: int = 1) -> None:
        """Add an entry to the spawn table or overwrite an existing one.

        Parameters
        ----------
        name: str
            The name of a prefab.
        frequency: int
            The relative frequency that this prefab should spawn relative to others.
        """
        if entry_index := self._index_map.get(name, None):
            self._frequencies[entry_index] = frequency
        else:
            self._names.append(name)
            self._frequencies.append(frequency)
            self._index_map[name] = self._size
            self._size += 1

    def choose_random(self, rng: random.Random) -> str:
        """
        Performs a weighted random selection across all prefab names

        Parameters
        ----------
        rng: random.Random
            A Random rng instance

        Returns
        -------
        str
            The name of a prefab
        """

        if self._size == 0:
            raise IndexError("Residence spawn table is empty")

        return rng.choices(population=self._names, weights=self._frequencies, k=1)[0]

    def get_matching_prefabs(self, *patterns: str) -> List[str]:
        """
        Get all prefabs with names that match the given regex strings

        Parameters
        ----------
        *patterns: Tuple[str, ...]
            Glob-patterns of names to check for

        Returns
        -------
        List[str]
            The names of prefabs in the table that match the pattern
        """

        matches: List[str] = []

        for name in self._names:
            if any([re.match(p, name) for p in patterns]):
                matches.append(name)

        return matches

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return bool(self._size)

    def __getitem__(self, item: int) -> ResidenceSpawnTableEntry:
        return ResidenceSpawnTableEntry(
            name=self._names[item], frequency=self._frequencies[item]
        )

    def __iter__(self) -> Iterator[ResidenceSpawnTableEntry]:
        return ResidenceSpawnTableIterator(self)

    def extend(self, other: ResidenceSpawnTable) -> None:
        """Add entries from another table to this table.

        Parameters
        ----------
        other
            The table with new entries
        """

        for entry in other:
            self.update(name=entry.name, frequency=entry.frequency)

    @staticmethod
    def combine(*tables: ResidenceSpawnTable) -> ResidenceSpawnTable:
        """Create a new table that is a combination of the given tables.

        Parameters
        ----------
        *tables
            The spawn tables to combine.

        Returns
        -------
        CharacterSpawnTable
            A new spawn table.
        """

        combined_table = ResidenceSpawnTable()

        for table in tables:
            combined_table.extend(table)

        return combined_table
