from __future__ import annotations

from collections import defaultdict
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Set,
    Tuple,
    TypeVar,
)

from neighborly.core.serializable import ISerializable


class ISettlementMap(Protocol):
    def get_size(self) -> Tuple[int, int]:
        """Get the Width and Length of the map"""
        raise NotImplementedError

    def get_total_lots(self) -> int:
        raise NotImplementedError

    def get_vacant_lots(self) -> List[int]:
        """Get the Width and Length of the map"""
        raise NotImplementedError

    def get_lot_position(self, lot_id: int) -> Tuple[float, float]:
        """Get the Width and Length of the map"""
        raise NotImplementedError

    def get_neighboring_lots(self, lot_id: int) -> List[int]:
        """Get the Width and Length of the map"""
        raise NotImplementedError

    def reserve_lot(self, lot_id: int, building_id: int) -> None:
        raise NotImplementedError

    def free_lot(self, lot_id: int) -> None:
        raise NotImplementedError


class Settlement(ISerializable):
    """Manages all the information about the town/city/village"""

    __slots__ = "name", "land_map", "population", "business_counts"

    def __init__(self, name: str, land_map: ISettlementMap) -> None:
        self.name: str = name
        self.land_map: ISettlementMap = land_map
        self.population: int = 0
        self.business_counts: DefaultDict[str, int] = defaultdict(lambda: 0)

    def increment_population(self) -> None:
        self.population += 1

    def decrement_population(self) -> None:
        self.population -= 1

    def to_dict(self) -> Dict[str, Any]:
        return {"type": "Settlement", "name": self.name, "population": self.population}

    def __str__(self) -> str:
        return f"{self.name} (Pop. {self.population})"

    def __repr__(self) -> str:
        return f"Town(name={self.name}, population={self.population})"


class GridSettlementMap:
    """
    Uses a traditional cartesian grid to represent the settlement's
    map. Each cell in the grid is one lot in the town
    """

    __slots__ = ("_unoccupied", "_occupied", "_grid")

    def __init__(self, size: Tuple[int, int]) -> None:
        super().__init__()
        width, length = size
        assert width >= 0 and length >= 0
        self._grid: Grid[Optional[int]] = Grid(size, lambda: None)
        self._unoccupied: List[int] = list(range(width * length))
        self._occupied: Set[int] = set()

    def get_size(self) -> Tuple[int, int]:
        """Get the Width and Length of the map"""
        return self._grid.shape

    def get_total_lots(self) -> int:
        return self._grid.shape[0] * self._grid.shape[1]

    def get_vacant_lots(self) -> List[int]:
        """Get the Width and Length of the map"""
        # Make a copy of the array
        return [*self._unoccupied]

    def get_lot_position(self, lot_id: int) -> Tuple[float, float]:
        """Get the Width and Length of the map"""
        x = lot_id % self._grid.shape[0]
        y = lot_id // self._grid.shape[0]
        return x, y

    def get_neighboring_lots(self, lot_id: int) -> List[int]:
        """Get the Width and Length of the map"""
        position = self.get_lot_position(lot_id)
        rounded_position = (int(position[0]), int(position[1]))
        neighbor_positions = self._grid.get_neighbors(rounded_position, True)
        return [self._position_to_id(pos) for pos in neighbor_positions]

    def reserve_lot(self, lot_id: int, building_id: int) -> None:
        if lot_id in self._occupied:
            raise RuntimeError("Lot already occupied")
        position = self.get_lot_position(lot_id)
        rounded_position = (int(position[0]), int(position[1]))
        self._grid[rounded_position] = building_id
        self._unoccupied.remove(lot_id)
        self._occupied.add(lot_id)

    def free_lot(self, lot_id: int) -> None:
        position = self.get_lot_position(lot_id)
        rounded_position = (int(position[0]), int(position[1]))
        self._grid[rounded_position] = None
        self._unoccupied.append(lot_id)
        self._occupied.remove(lot_id)

    def _position_to_id(self, position: Tuple[int, int]) -> int:
        """Convert lot position to lot ID"""
        return (position[1] * self._grid.shape[0]) + position[0]


def create_grid_settlement(name: str, size: Tuple[int, int]) -> Settlement:
    """Creates Settlement instance that defaults to using a grid-based map"""
    return Settlement(name, GridSettlementMap(size))


_GT = TypeVar("_GT")


class Grid(Generic[_GT]):
    """
    Grids house spatially-related data using a graph implemented
    as a grid of nodes. Nodes are stored in column-major order
    for easier interfacing with higher-level positioning systems
    """

    __slots__ = "_width", "_length", "_grid"

    def __init__(
        self, size: Tuple[int, int], default_factory: Callable[[], _GT]
    ) -> None:
        self._width: int = size[0]
        self._length: int = size[1]
        self._grid: List[_GT] = [
            default_factory() for _ in range(self._width * self._length)
        ]

    @property
    def shape(self) -> Tuple[int, int]:
        return self._width, self._length

    def in_bounds(self, point: Tuple[int, int]) -> bool:
        """Returns True if the given point is within the grid"""
        return 0 <= point[0] < self._width and 0 <= point[1] < self._length

    def get_neighbors(
        self, point: Tuple[int, int], include_diagonals: bool = False
    ) -> List[Tuple[int, int]]:
        neighbors: List[Tuple[int, int]] = []

        # North-West (Diagonal)
        if self.in_bounds((point[0] - 1, point[1] - 1)) and include_diagonals:
            neighbors.append((point[0] - 1, point[1] - 1))

        # North
        if self.in_bounds((point[0], point[1] - 1)):
            neighbors.append((point[0], point[1] - 1))

        # North-East (Diagonal)
        if self.in_bounds((point[0] + 1, point[1] - 1)) and include_diagonals:
            neighbors.append((point[0] + 1, point[1] - 1))

        # East
        if self.in_bounds((point[0] + 1, point[1])):
            neighbors.append((point[0] + 1, point[1]))

        # South-East (Diagonal)
        if self.in_bounds((point[0] + 1, point[1] + 1)) and include_diagonals:
            neighbors.append((point[0] + 1, point[1] + 1))

        # South
        if self.in_bounds((point[0], point[1] + 1)):
            neighbors.append((point[0], point[1] + 1))

        # South-West (Diagonal)
        if self.in_bounds((point[0] - 1, point[1] + 1)) and include_diagonals:
            neighbors.append((point[0] - 1, point[1] + 1))

        # West
        if self.in_bounds((point[0] - 1, point[1])):
            neighbors.append((point[0] - 1, point[1]))

        return neighbors

    def get_cells(self) -> List[_GT]:
        """Return all the cells in the grid"""
        return self._grid

    def __setitem__(self, point: Tuple[int, int], value: _GT) -> None:
        if 0 <= point[0] <= self._width and 0 <= point[1] <= self._length:
            index = (point[1] * self.shape[0]) + point[0]
            self._grid[index] = value
        else:
            raise IndexError(point)

    def __getitem__(self, point: Tuple[int, int]) -> _GT:
        if self.in_bounds(point):
            index = (point[1] * self.shape[0]) + point[0]
            return self._grid[index]
        else:
            raise IndexError(point)
