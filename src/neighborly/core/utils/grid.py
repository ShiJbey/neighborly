from __future__ import annotations

from typing import Callable, Generic, List, Tuple, TypeVar

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

    def __setitem__(self, point: Tuple[int, int], value: _GT) -> None:
        if 0 <= point[0] <= self._width and 0 <= point[1] <= self._length:
            index = (point[0] * self.shape[1]) + point[1]
            self._grid[index] = value
        else:
            raise IndexError(point)

    def __getitem__(self, point: Tuple[int, int]) -> _GT:
        if 0 <= point[0] <= self._width and 0 <= point[1] <= self._length:
            index = (point[0] * self.shape[1]) + point[1]
            return self._grid[index]
        else:
            raise IndexError(point)
