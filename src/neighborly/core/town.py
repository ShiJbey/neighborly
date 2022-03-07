from abc import abstractmethod
from dataclasses import dataclass
from typing import Tuple, List, Set, Protocol, Optional

from neighborly.core.ecs import Component
from neighborly.core.name_generation import get_name


@dataclass(frozen=True)
class TownConfig:
    """
    Configuration parameters for Town instance

    Attributes
    ----------
    name : str
        Tracery grammar used to generate a town's name
    town_width : int
        Number of space tiles wide the town will be
    town_length : int
        Number of space tile long the town will be
    """

    name: str = "#town_name#"
    town_width: int = 5
    town_length: int = 5


class Town(Component):
    """Simulated town where characters live"""

    __slots__ = "name", "layout"

    def __init__(self, name: str, layout: 'TownLayout') -> None:
        super().__init__()
        self.name: str = name
        self.layout: 'TownLayout' = layout

    @classmethod
    def create(cls, config: TownConfig) -> "Town":
        """Create a town instance"""
        town_name = get_name(config.name)
        layout = TownLayout(config.town_width, config.town_length)
        return cls(name=town_name, layout=layout)


@dataclass
class LayoutGridSpace:
    # Identifier given to this space
    space_id: int
    # Position of the space in the grid
    position: Tuple[int, int]
    # ID of the gameobject for the place occupying this space
    place_id: Optional[int] = None


class SpaceSelectionStrategy(Protocol):
    """Uses a heuristic to select a space within the town"""

    @abstractmethod
    def choose_space(self, spaces: List[LayoutGridSpace]) -> LayoutGridSpace:
        """Choose a space based on an internal heuristic"""
        raise NotImplementedError()


class TownLayout:
    """Manages an occupancy grid of what tiles in the town currently have places built on them

    Attributes
    ----------
    width : int
        Size of the grid in the x-direction
    length : int
        Size of the grid in the y-direction
    """

    __slots__ = "_width", "_length", "_spaces", "_unoccupied", "_occupied"

    def __init__(self, width: int, length: int) -> None:
        self._width: int = width
        self._length: int = length
        self._spaces: List[LayoutGridSpace] = []
        for x in range(width):
            for y in range(length):
                self._spaces.append(LayoutGridSpace(len(self._spaces), (x, y)))
        assert len(self._spaces) == width * length
        self._unoccupied: List[int] = list(range(0, width * length))
        self._occupied: Set[int] = set()

    @property
    def width(self) -> int:
        """Return the width of the layout"""
        return self._width

    @property
    def length(self) -> int:
        """Return the length of the layout"""
        return self._length

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the width x length of the town"""
        return self._width, self._length

    def get_num_vacancies(self) -> int:
        """Return number of vacant spaces"""
        return len(self._unoccupied)

    def has_vacancy(self) -> bool:
        """Returns True if there are empty spaces available in the town"""
        return bool(self._unoccupied)

    def allocate_space(self, selection_strategy: Optional[SpaceSelectionStrategy] = None) -> LayoutGridSpace:
        """Allocates a space for a location, setting it as occupied"""
        if self._unoccupied:
            if selection_strategy:
                space = selection_strategy.choose_space(
                    [self._spaces[i] for i in self._unoccupied])
            else:
                space = self._spaces[self._unoccupied[0]]

            self._unoccupied.remove(space.space_id)
            self._occupied.add(space.space_id)

            return space

        raise RuntimeError("Attempting to get space from full town layout")

    def free_space(self, space: int) -> None:
        """Frees up a space in the town to be used by another location"""
        self._spaces[space].place_id = None
        self._unoccupied.append(space)
        self._occupied.remove(space)
