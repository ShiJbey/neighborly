"""World Map.

This module contains the implementation for Neighborly's world map.

"""
from __future__ import annotations

from typing import Any, Callable, Dict, Generic, List, Optional, Set, Tuple, TypeVar

from neighborly.ecs import GameObject, ISerializable

_GT = TypeVar("_GT")


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
            The X, Y position of a grid cell.
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


class BuildingMap(ISerializable):
    """Stores lots for buildings in a cartesian grid.

    Notes
    -----
    This class uses lot numbers instead of directly providing grid positions because
    I thought it would help if someone could use non-cartesian grids to hold buildings.
    """

    __slots__ = "_unoccupied", "_occupied", "_grid"

    _grid: Grid[Optional[GameObject]]
    """An internal grid that stores the building IDs."""

    _unoccupied: List[Tuple[int, int]]
    """The IDs of lots that are not occupied."""

    _occupied: Set[Tuple[int, int]]
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
        if width <= 0 or length <= 0:
            raise ValueError(
                f"Dimensions of BuildingMap must be greater than 0. Given: {size}"
            )
        self._grid = Grid(size, lambda: None)
        self._unoccupied = BuildingMap._initialize_unoccupied_positions(width, length)
        self._occupied = set()

    @staticmethod
    def _initialize_unoccupied_positions(
        width: int, length: int
    ) -> List[Tuple[int, int]]:
        positions: List[Tuple[int, int]] = []

        for x in range(width):
            for y in range(length):
                positions.append((x, y))

        return positions

    def get_size(self) -> Tuple[int, int]:
        """Get the Width and Length of the map."""
        return self._grid.shape

    def get_total_lots(self) -> int:
        """Get the total number of lots on the map."""
        return self._grid.shape[0] * self._grid.shape[1]

    def get_vacant_lots(self) -> List[Tuple[int, int]]:
        """Get the IDs of lots that are currently not occupied."""
        # Make a copy of the array
        return self._unoccupied.copy()

    def get_neighboring_lots(self, position: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get the lots that neighbor the given lot.

        Parameters
        ----------
        position
            The position of the lot to get the neighbors of.

        Returns
        -------
        List[int]
            The IDs of the neighboring lots.
        """
        return self._grid.get_neighbors(position, True)

    def add_building(self, position: Tuple[int, int], building: GameObject) -> None:
        """Set a lot as being taken by a building.

        Parameters
        ----------
        position
            The lot to set as taken.
        building
            The building that owns the spot.
        """
        if position in self._occupied:
            raise RuntimeError("Lot already occupied")
        self._grid[position] = building
        self._unoccupied.remove(position)
        self._occupied.add(position)

    def remove_building_from_lot(self, position: Tuple[int, int]) -> None:
        """Sets a lot as not being owned by a building

        Parameters
        ----------
        position
            The position of a lot
        """
        self._grid[position] = None
        self._unoccupied.append(position)
        self._occupied.remove(position)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the map to a dictionary."""
        return {
            "width": self.get_size()[0],
            "height": self.get_size()[1],
            "cells": [cell.uid if cell else -1 for cell in self._grid.get_cells()],
        }
