from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Set, Tuple

from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.serializable import ISerializable
from neighborly.core.utils.grid import Grid


class Town(ISerializable):
    """
    Simulated town where characters live

    Notes
    -----
    The town is stored in the ECS as a global resource

    Attributes
    ----------
    name: str
        The name of the town
    population: int
        The number of active town residents
    """

    __slots__ = "name", "_population"

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name
        self._population: int = 0

    @property
    def population(self) -> int:
        return self._population

    def increment_population(self) -> None:
        self._population += 1

    def decrement_population(self) -> None:
        self._population -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "population": self.population}

    def __str__(self) -> str:
        return f"{self.name} (Pop. {self.population})"

    def __repr__(self) -> str:
        return f"Town(name={self.name}, population={self.population})"

    @classmethod
    def create(cls, world: World, **kwargs) -> Town:
        """
        Create a town instance

        Parameters
        ----------
        kwargs.name: str
            The name of the town as a string or Tracery pattern
        """
        town_name = kwargs.get("name", "Town")
        town_name = world.get_resource(NeighborlyEngine).name_generator.get_name(
            town_name
        )
        return cls(name=town_name)


class LandGrid(ISerializable):
    """
    Manages what spaces are available to place buildings on within the town
    """

    __slots__ = ("_unoccupied", "_occupied", "_grid")

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        width, length = size
        self._grid: Grid[Optional[int]] = Grid(size, lambda: None)
        self._unoccupied: List[Tuple[int, int]] = list(
            itertools.product(list(range(width)), list(range(length)))
        )
        self._occupied: Set[Tuple[int, int]] = set()

    @property
    def shape(self) -> Tuple[int, int]:
        return self._grid.shape

    def get_vacancies(self) -> List[Tuple[int, int]]:
        """Return the positions that are unoccupied in town"""
        return self._unoccupied

    def has_vacancy(self) -> bool:
        """Returns True if there are empty spaces available in the town"""
        return bool(self._unoccupied)

    def __setitem__(self, position: Tuple[int, int], value: Optional[int]) -> None:
        if value is None:
            self._grid[position] = None
            self._unoccupied.append(position)
            self._occupied.remove(position)
        else:
            if position in self._occupied:
                raise RuntimeError("Grid space already occupied")
            self._grid[position] = value
            self._unoccupied.remove(position)
            self._occupied.add(position)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self._grid.shape[0],
            "length": self._grid.shape[1],
            "grid": [str(cell) for cell in self._grid],
        }
