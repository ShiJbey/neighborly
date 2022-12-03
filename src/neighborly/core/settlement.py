from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Protocol, Set, Tuple

from neighborly.core.serializable import ISerializable
from neighborly.core.utils.grid import Grid


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

    __slots__ = "name", "land_map", "population", "business_counts"

    def __init__(self, name: str, land_map: ISettlementMap) -> None:
        self.name: str = name
        self.land_map: ISettlementMap = land_map
        self.population: int = 0
        self.business_counts: DefaultDict[str, int] = defaultdict(default=0)

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
