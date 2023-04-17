import random
import re
from typing import Any, Dict, List, Optional

from neighborly.core.ecs import Component, GameObject
from neighborly.core.settlement import Settlement
from neighborly.core.time import SimDateTime


class CharacterSpawnTable(Component):
    """Manages the frequency that character prefabs are spawned"""

    __slots__ = "_names", "_frequencies", "_size", "_index_map"

    def __init__(self, entries: Optional[List[Dict[str, Any]]] = None) -> None:
        """
        Parameters
        ----------
        entries
            Starting entries in the form [{"name": ..., "frequency": ...}, ...],
            by default None
        """
        super().__init__()
        # Names and frequencies are separate buffers to optimize random selection.
        # If we stored them as a list of dicts, we would have to iterate the list to
        # get all the spawn frequencies before selecting an entry
        self._names: List[str] = []
        self._frequencies: List[int] = []
        self._index_map: Dict[str, int] = {}
        self._size = 0

        if entries:
            for entry in entries:
                self.add(**entry)

    def add(self, name: str, frequency: int = 1) -> None:
        """Add an entry to the spawn table.

        Parameters
        ----------
        name
            The name of a prefab.
        frequency
            The relative frequency that this prefab should spawn relative to others.
        """
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

    def to_dict(self) -> Dict[str, Any]:
        # This returns an empty because this would bloat the simulation output with
        # configuration data
        return {}


class BusinessSpawnTable(Component):
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
        super().__init__()
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
                self.add(**entry)

    def add(
        self,
        name: str,
        frequency: int = 1,
        max_instances: int = 9999,
        min_population: int = 0,
        year_available: int = 0,
        year_obsolete: int = 9999,
    ) -> None:
        """
        Add an entry to the spawn table

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
        date = world.get_resource(SimDateTime)
        rng = world.get_resource(random.Random)

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
        date = world.get_resource(SimDateTime)

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

    def to_dict(self) -> Dict[str, Any]:
        # This returns an empty because this would bloat the simulation output with
        # configuration data
        return {}


class ResidenceSpawnTable(Component):
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
        super().__init__()
        # Names and frequencies are separate buffers to optimize random selection.
        # If we stored them as a list of dicts, we would have to iterate the list to
        # get all the spawn frequencies before selecting an entry
        self._names: List[str] = []
        self._frequencies: List[int] = []
        self._index_map: Dict[str, int] = {}
        self._size = 0

        if entries:
            for entry in entries:
                self.add(**entry)

    def add(self, name: str, frequency: int = 1) -> None:
        """
        Add an entry to the spawn table

        Parameters
        ----------
        name: str
            The name of a prefab
        frequency: int
            The relative frequency that this prefab should spawn relative to others
        """
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

    def to_dict(self) -> Dict[str, Any]:
        # This returns an empty because this would bloat the simulation output with
        # configuration data
        return {}
