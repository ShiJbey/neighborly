from __future__ import annotations

import itertools
from typing import Any, Dict, List, Optional, Set, Tuple

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
    _population: int
        The number of active town residents
    """

    __slots__ = "name", "_population"

    def __init__(self, name: str, population: int = 0) -> None:
        super().__init__()
        self.name: str = name
        self._population: int = population

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


class LandGrid(ISerializable):
    """
    Manages what spaces are available to place buildings on within the town
    """

    __slots__ = ("_unoccupied", "_occupied", "_grid")

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        width, length = size
        assert width >= 0 and length >= 0
        self._grid: Grid[Optional[int]] = Grid(size, lambda: None)
        self._unoccupied: List[Tuple[int, int]] = list(
            itertools.product(list(range(width)), list(range(length)))
        )
        self._occupied: Set[Tuple[int, int]] = set()

    @property
    def shape(self) -> Tuple[int, int]:
        return self._grid.shape

    def in_bounds(self, point: Tuple[int, int]) -> bool:
        """Returns True if the given point is within the grid"""
        return self._grid.in_bounds(point)

    def get_neighbors(
        self, point: Tuple[int, int], include_diagonals: bool = False
    ) -> List[Tuple[int, int]]:
        return self._grid.get_neighbors(point, include_diagonals)

    def get_vacancies(self) -> List[Tuple[int, int]]:
        """Return the positions that are unoccupied in town"""
        return self._unoccupied

    def has_vacancy(self) -> bool:
        """Returns True if there are empty spaces available in the town"""
        return bool(self._unoccupied)

    def __len__(self) -> int:
        return self.shape[0] * self.shape[1]

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

    def __repr__(self) -> str:
        return f"Land Grid(shape={self.shape}, vacant: {len(self._unoccupied)}, occupied: {len(self._occupied)})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "width": self._grid.shape[0],
            "length": self._grid.shape[1],
            "grid": [cell for cell in self._grid.get_cells()],
        }
