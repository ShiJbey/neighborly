from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    TypeVar,
)

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, ISerializable


class ISettlementMap(ABC):
    """Interface implemented by classes that operate as world maps.

    SettlementMaps are responsible for managing land usage in settlements
    they provide a model of space to the simulation where buildings are placed
    on individual lots.
    """

    @abstractmethod
    def get_size(self) -> Tuple[int, int]:
        """Get the Width and Length of the map."""
        raise NotImplementedError

    @abstractmethod
    def get_total_lots(self) -> int:
        """Get the total number of lots on the map."""
        raise NotImplementedError

    @abstractmethod
    def get_vacant_lots(self) -> List[int]:
        """Get the IDs of lots that are currently not occupied."""
        raise NotImplementedError

    @abstractmethod
    def get_lot_position(self, lot_id: int) -> Tuple[float, float]:
        """Get the position of a lot on the map.

        Parameters
        ----------
        lot_id
            The ID of the lot to get the position of.

        Returns
        -------
        Tuple[float, float]
            The 2D position of the lot on the map.
        """
        raise NotImplementedError

    @abstractmethod
    def get_neighboring_lots(self, lot_id: int) -> List[int]:
        """Get the lots that neighbor the given lot.

        Parameters
        ----------
        lot_id
            The ID of the lot to get the neighbors of.

        Returns
        -------
        List[int]
            The IDs of the neighboring lots.
        """
        raise NotImplementedError

    @abstractmethod
    def reserve_lot(self, lot_id: int, building_id: int) -> None:
        """Set a lot as being taken by a building.

        Parameters
        ----------
        lot_id
            The lot to set as taken.
        building_id
            The GameObject ID of the building that owns the spot.
        """
        raise NotImplementedError

    @abstractmethod
    def free_lot(self, lot_id: int) -> None:
        """Sets a lot as not being owned by a building

        Parameters
        ----------
        lot_id
            The ID of a lot
        """
        raise NotImplementedError

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serializes the map to a dictionary"""
        raise NotImplementedError


class Settlement(Component, ISerializable):
    """A place where characters live, go to work, and interact.

    Settlements can represent towns, cities, villages, etc. They are responsible for
    tracking the population and other information about locations within the
    settlement.
    """

    __slots__ = (
        "land_map",
        "population",
        "business_counts",
        "locations",
        "businesses",
    )

    land_map: ISettlementMap
    """The map of the town used to manage land usage."""

    population: int
    """The number of characters who are residents of the settlement."""

    business_counts: DefaultDict[str, int]
    """
    A count of the number of types of businesses that exist in the town.
    The dict key is the name of the BusinessPrefab used to construct
    the business GameObject.
    """

    locations: OrderedSet[int]
    """
    The GameObject IDs of all the GameObjects with Location components that belong
    to this settlement.
    """

    businesses: OrderedSet[int]
    """
    The GameObject IDs of all the GameObjects with Business components that belong
    to this settlement.
    """

    def __init__(self, land_map: ISettlementMap) -> None:
        """
        Parameters
        ----------
        land_map
            The map of the town used to manage land usage
        """
        super().__init__()
        self.land_map = land_map
        self.population = 0
        self.business_counts = defaultdict(lambda: 0)
        self.locations = OrderedSet()
        self.businesses = OrderedSet()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "population": self.population,
            "land_map": self.land_map.to_dict(),
        }

    def __str__(self) -> str:
        return f"Settlement(Pop. {self.population})"

    def __repr__(self) -> str:
        return f"Settlement(population={self.population})"


class GridSettlementMap(ISettlementMap):
    """Stores lots for buildings in a cartesian grid.s"""

    __slots__ = "_unoccupied", "_occupied", "_grid"

    _grid: Grid[Optional[int]]
    """An internal grid that stores the building IDs"""

    _unoccupied: List[int]
    """The IDs of lots that are not occupied."""

    _occupied: Set[int]
    """The IDs of lots that are currently occupied."""

    def __init__(self, size: Tuple[int, int]) -> None:
        """
        Parameters
        ----------
        size
            The width abd length of the map grid
        """
        super().__init__()
        width, length = size
        assert width >= 0 and length >= 0
        self._grid = Grid(size, lambda: None)
        self._unoccupied = list(range(width * length))
        self._occupied = set()

    def get_size(self) -> Tuple[int, int]:
        return self._grid.shape

    def get_total_lots(self) -> int:
        return self._grid.shape[0] * self._grid.shape[1]

    def get_vacant_lots(self) -> List[int]:
        # Make a copy of the array
        return [*self._unoccupied]

    def get_lot_position(self, lot_id: int) -> Tuple[float, float]:
        x = lot_id % self._grid.shape[0]
        y = lot_id // self._grid.shape[0]
        return x, y

    def get_neighboring_lots(self, lot_id: int) -> List[int]:
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
        """Convert lot position to lot ID

        Parameters
        ----------
        position
            The X,Y position of the lot

        Returns
        -------
        int
            The ID of the lot at that position
        """
        return (position[1] * self._grid.shape[0]) + position[0]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "width": self.get_size()[0],
            "height": self.get_size()[1],
            "cells": [cell if cell else -1 for cell in self._grid.get_cells()],
        }


_GT = TypeVar("_GT")
"""Generic grid type."""


class Grid(Generic[_GT]):
    """A generic container for storing data in a 2-dimensional grid."""

    __slots__ = "_width", "_length", "_cells"

    _width: int
    """The size of the grid in the X-dimension."""

    _length: int
    """The size of the grid in the Y-dimension."""

    _cells: List[_GT]
    """The data cells of the grid stored in row-major order."""

    def __init__(
        self, size: Tuple[int, int], default_factory: Callable[[], _GT]
    ) -> None:
        """
        Parameters
        ----------
        size
            The X, Y size of the grid.
        default_factory
            A factory method used to initialize all the grid cells.
        """
        self._width = size[0]
        self._length = size[1]
        self._cells = [default_factory() for _ in range(self._width * self._length)]

    @property
    def shape(self) -> Tuple[int, int]:
        """The width and length of the grid."""
        return self._width, self._length

    def in_bounds(self, point: Tuple[int, int]) -> bool:
        """Check if a point is within a grid.

        Parameters
        ----------
        point
            The X, Y position of a grid cell.

        Returns
        -------
        bool
            True if the point is within bounds, False otherwise.
        """
        return 0 <= point[0] < self._width and 0 <= point[1] < self._length

    def get_neighbors(
        self, point: Tuple[int, int], include_diagonals: bool = False
    ) -> List[Tuple[int, int]]:
        """Get all the grid cells neighboring the given position.

        Parameters
        ----------
        point
            The X, Y position of a grid cell.
        include_diagonals
            Flag if to include diagonal neighbors (defaults to False).

        Returns
        -------
        List[Tuple[int, int]]
            The X, Y positions of grid cells
        """
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
        """Get all the data stored in the grid cells.

        Returns
        -------
        List[_GT]
            The cell data in row-major order.
        """
        return self._cells

    def __setitem__(self, point: Tuple[int, int], value: _GT) -> None:
        """Set the value for a cell.

        Parameters
        ----------
        point
            The X, Y position of a grid cell..
        value
            The data to store in the grid cell.
        """
        if 0 <= point[0] <= self._width and 0 <= point[1] <= self._length:
            index = (point[1] * self.shape[0]) + point[0]
            self._cells[index] = value
        else:
            raise IndexError(point)

    def __getitem__(self, point: Tuple[int, int]) -> _GT:
        """Get the value for a cell.

        Parameters
        ----------
        point
            The X, Y position of a grid cell.

        Returns
        -------
        _GT
            The data in the grid cell.
        """
        if self.in_bounds(point):
            index = (point[1] * self.shape[0]) + point[0]
            return self._cells[index]
        else:
            raise IndexError(point)
