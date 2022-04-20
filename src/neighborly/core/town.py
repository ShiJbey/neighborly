from __future__ import annotations

import itertools
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Tuple, List, Set, Protocol, Optional, Dict, Generic, Callable, TypeVar, Any

from pydantic import BaseModel

from neighborly.core.ecs import Component
from neighborly.core.name_generation import get_name


class TownConfig(BaseModel):
    """
    Static configuration parameters for Town instance

    Attributes
    ----------
    name : str
        Tracery grammar used to generate a town's name
    width : int
        Number of space tiles wide the town will be
    length : int
        Number of space tile long the town will be
    """

    name: str = "#town_name#"
    width: int = 5
    length: int = 5


class Town(Component):
    """Simulated town where characters live"""

    __slots__ = "name", "layout", "population"

    def __init__(self, name: str, layout: 'TownLayout') -> None:
        super().__init__()
        self.name: str = name
        self.population: int = 0
        self.layout: 'TownLayout' = layout

    @classmethod
    def create(cls, config: TownConfig) -> "Town":
        """Create a town instance"""
        town_name = get_name(config.name)
        layout = TownLayout(config.width, config.length)
        return cls(name=town_name, layout=layout)


@dataclass
class LayoutGridSpace:
    # Identifier given to this space
    # space_id: int
    # Position of the space in the grid
    # position: Tuple[int, int]
    # ID of the gameobject for the place occupying this space
    place_id: Optional[int] = None


class SpaceSelectionStrategy(Protocol):
    """Uses a heuristic to select a space within the town"""

    @abstractmethod
    def choose_space(self, spaces: List[LayoutGridSpace]) -> Tuple[int, int]:
        """Choose a space based on an internal heuristic"""
        raise NotImplementedError()


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


_GT = TypeVar('_GT')


class Grid(Generic[_GT]):
    """
    Grids house spatially-related data using a graph implemented
    as a grid of nodes. Nodes are stored in column-major order
    for easier interfacing with higher-level positioning systems
    """

    __slots__ = "_width", "_length", "_grid"

    def __init__(
            self,
            width: int,
            length: int,
            default_factory: Callable[[], _GT]
    ) -> None:
        self._width: int = width
        self._length: int = length
        self._grid: List[_GT] = [default_factory()
                                 for _ in range(width * length)]

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
            adjacent_cells['west'] = (point[0] - 1, point[1])

        if point[0] < self.shape[0] - 1:
            adjacent_cells['east'] = (point[0] + 1, point[1])

        if point[1] > 0:
            adjacent_cells['north'] = (point[0], point[1] - 1)

        if point[1] < self.shape[1] - 1:
            adjacent_cells['south'] = (point[0], point[1] + 1)

        return adjacent_cells

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": type(self).__name__,
            "height": self._length,
            "width": self._width,
            "grid": [str(cell) for cell in self._grid]
        }


class TownLayout:
    """Manages an occupancy grid of what tiles in the town currently have places built on them

    Attributes
    ----------
    width : int
        Size of the grid in the x-direction
    length : int
        Size of the grid in the y-direction
    """

    __slots__ = "_unoccupied", "_occupied", "_grid"

    def __init__(self, width: int, length: int) -> None:
        self._grid: Grid[LayoutGridSpace] = Grid(width, length, lambda: LayoutGridSpace())
        self._unoccupied: List[Tuple[int, int]] = \
            list(itertools.product(list(range(width)), list(range(length))))
        self._occupied: Set[Tuple[int, int]] = set()

    @property
    def grid(self) -> Grid[LayoutGridSpace]:
        return self._grid

    def get_num_vacancies(self) -> int:
        """Return number of vacant spaces"""
        return len(self._unoccupied)

    def has_vacancy(self) -> bool:
        """Returns True if there are empty spaces available in the town"""
        return bool(self._unoccupied)

    def allocate_space(
            self,
            place_id: int,
            selection_strategy: Optional[SpaceSelectionStrategy] = None
    ) -> Tuple[int, int]:
        """Allocates a space for a location, setting it as occupied"""
        if self._unoccupied:
            if selection_strategy:
                space = selection_strategy.choose_space(
                    [self._grid[i] for i in self._unoccupied])
            else:
                space = self._unoccupied[0]

            self._grid[space].place_id = place_id
            self._unoccupied.remove(space)
            self._occupied.add(space)

            return space

        raise RuntimeError("Attempting to get space from full town layout")

    def free_space(self, space: Tuple[int, int]) -> None:
        """Frees up a space in the town to be used by another location"""
        self._grid[space].place_id = None
        self._unoccupied.append(space)
        self._occupied.remove(space)
