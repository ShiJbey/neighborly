from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar

from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.serializable import ISerializable


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

    __slots__ = "name", "population"

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name
        self.population: int = 0

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


@dataclass
class LayoutGridSpace:
    # ID of the gameobject for the place occupying this space
    occupant: Optional[int] = None

    def reset(self) -> None:
        self.occupant = None


class CompassDirection(Enum):
    """Compass directions to string"""

    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3

    def __str__(self) -> str:
        """Convert compass direction to string"""
        mapping = {
            CompassDirection.NORTH: "north",
            CompassDirection.SOUTH: "south",
            CompassDirection.EAST: "east",
            CompassDirection.WEST: "west",
        }

        return mapping[self]

    def to_direction_tuple(self) -> Tuple[int, int]:
        """Convert direction to (x,y) tuple for the direction"""
        mapping = {
            CompassDirection.NORTH: (0, -1),
            CompassDirection.SOUTH: (0, 1),
            CompassDirection.EAST: (1, 0),
            CompassDirection.WEST: (-1, 0),
        }

        return mapping[self]


_GT = TypeVar("_GT")


class Grid(Generic[_GT]):
    """
    Grids house spatially-related data using a graph implemented
    as a grid of nodes. Nodes are stored in column-major order
    for easier interfacing with higher-level positioning systems
    """

    __slots__ = "_width", "_length", "_grid"

    def __init__(
        self, width: int, length: int, default_factory: Callable[[], _GT]
    ) -> None:
        self._width: int = width
        self._length: int = length
        self._grid: List[_GT] = [default_factory() for _ in range(width * length)]

    @property
    def shape(self) -> Tuple[int, int]:
        return self._width, self._length

    def __setitem__(self, point: Tuple[int, int], value: _GT) -> None:
        index = (point[0] * self.shape[1]) + point[1]
        self._grid[index] = value

    def __getitem__(self, point: Tuple[int, int]) -> _GT:
        index = (point[0] * self.shape[1]) + point[1]
        return self._grid[index]

    def get_adjacent_cells(self, point: Tuple[int, int]) -> Dict[str, Tuple[int, int]]:
        adjacent_cells: Dict[str, Tuple[int, int]] = {}

        if point[0] > 0:
            adjacent_cells["west"] = (point[0] - 1, point[1])

        if point[0] < self.shape[0] - 1:
            adjacent_cells["east"] = (point[0] + 1, point[1])

        if point[1] > 0:
            adjacent_cells["north"] = (point[0], point[1] - 1)

        if point[1] < self.shape[1] - 1:
            adjacent_cells["south"] = (point[0], point[1] + 1)

        return adjacent_cells

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self._length,
            "width": self._width,
            "grid": [str(cell) for cell in self._grid],
        }


class LandGrid:
    """
    Manages an occupancy grid of what tiles in the town
    currently have places built on them

    Attributes
    ----------
    width : int
        Size of the grid in the x-direction
    length : int
        Size of the grid in the y-direction
    """

    __slots__ = "_unoccupied", "_occupied", "_grid"

    def __init__(self, size: Tuple[int, int]) -> None:
        width, length = size
        self._grid: Grid[LayoutGridSpace] = Grid(
            width, length, lambda: LayoutGridSpace()
        )
        self._unoccupied: List[Tuple[int, int]] = list(
            itertools.product(list(range(width)), list(range(length)))
        )
        self._occupied: Set[Tuple[int, int]] = set()

    @property
    def grid(self) -> Grid[LayoutGridSpace]:
        return self._grid

    def get_vacancies(self) -> List[Tuple[int, int]]:
        """Return the positions that are unoccupied in town"""
        return self._unoccupied

    def has_vacancy(self) -> bool:
        """Returns True if there are empty spaces available in the town"""
        return bool(self._unoccupied)

    def reserve_space(
        self,
        position: Tuple[int, int],
        occupant_id: int,
    ) -> None:
        """Allocates a space for a location, setting it as occupied"""

        if position in self._occupied:
            raise RuntimeError("Grid space already occupied")

        space = self._grid[position]
        space.occupant = occupant_id
        self._unoccupied.remove(position)
        self._occupied.add(position)

    def free_space(self, space: Tuple[int, int]) -> None:
        """Frees up a space in the town to be used by another location"""
        self._grid[space].reset()
        self._unoccupied.append(space)
        self._occupied.remove(space)
