"""Components definitions used by multiple types of GameObjects.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, GameObject, ISerializable


@dataclass
class Name(Component, ISerializable):
    """The name of a GameObject."""

    value: str
    """The GameObject's name."""

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    def __str__(self) -> str:
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


@dataclass
class Age(Component, ISerializable):
    """Tracks the number of years old that a GameObject is."""

    value: float = 0.0
    """The number of years old."""

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


@dataclass
class Lifespan(Component, ISerializable):
    """How long a GameObject lives on average."""

    value: float
    """The number of years."""

    def __str__(self) -> str:
        return str(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return self.value

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class Location(Component, ISerializable):
    """Anywhere GameObjects may be.

    Locations track what larger location they belong and any sub locations they are comprised of.
    """

    __slots__ = "parent", "children"

    children: OrderedSet[GameObject]
    """All the sub-locations at this location."""

    parent: Optional[GameObject]
    """The parent location of this location."""

    def __init__(self) -> None:
        super().__init__()
        self.parent = None
        self.children = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "parent": self.parent.uid if self.parent is not None else -1,
            "children": [entry.uid for entry in self.children],
        }

    def __repr__(self) -> str:
        return "{}(parent={}, children={})".format(
            self.__class__.__name__,
            self.parent.name if self.parent else "",
            [child.name for child in self.children],
        )


@dataclass
class Position2D(Component, ISerializable):
    """The 2-dimensional position of a GameObject."""

    x: float = 0.0
    """The x-position of the GameObject."""

    y: float = 0.0
    """The y-position of the GameObject."""

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y}


class FrequentedLocations(Component, ISerializable):
    """Tracks the locations that a character frequents."""

    __slots__ = "_locations"

    _locations: OrderedSet[GameObject]
    """A set of GameObject IDs of locations."""

    def __init__(self, locations: Optional[Iterable[GameObject]] = None) -> None:
        """
        Parameters
        ----------
        locations
            An iterable of GameObject IDs of locations.
        """
        super().__init__()
        self._locations = OrderedSet(locations) if locations else OrderedSet([])

    def add(self, location: GameObject) -> None:
        """Add a new location.

        Parameters
        ----------
        location
           A GameObject reference to a location.
        """
        self._locations.add(location)

    def remove(self, location: GameObject) -> None:
        """Remove a location.

        Parameters
        ----------
        location
            A GameObject reference to a location to remove.
        """
        self._locations.remove(location)

    def clear(self) -> None:
        """Remove all location IDs from the component."""
        self._locations.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"locations": [entry.uid for entry in self._locations]}

    def __contains__(self, item: GameObject) -> bool:
        return item in self._locations

    def __iter__(self) -> Iterator[GameObject]:
        return self._locations.__iter__()

    def __str__(self) -> str:
        return self.__repr__()

    def __len__(self) -> int:
        return len(self._locations)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._locations.__repr__()})"


class Building(Component, ISerializable):
    """A physical building in the settlement.

    Notes
    -----
    Building components are attached to structures like businesses and residences.
    """

    __slots__ = "building_type"

    building_type: str
    """What kind of building is this."""

    def __init__(self, building_type: str) -> None:
        super().__init__()
        self.building_type = building_type

    def to_dict(self) -> Dict[str, Any]:
        return {"building_type": self.building_type}

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}(building_type={})".format(
            self.__class__.__name__,
            self.building_type,
        )


@dataclass
class CurrentLot(Component, ISerializable):
    """Tracks the lot that a building belongs to."""

    lot: int
    """The ID of a lot within a SettlementMap."""

    def to_dict(self) -> Dict[str, Any]:
        return {"lot": self.lot}


class FrequentedBy(Component, ISerializable):
    """Tracks the characters that frequent a location."""

    __slots__ = "_characters"

    _characters: OrderedSet[GameObject]
    """GameObject IDs of characters that frequent the location."""

    def __init__(self) -> None:
        super().__init__()
        self._characters = OrderedSet([])

    def add(self, character: GameObject) -> None:
        """Add a character.

        Parameters
        ----------
        character
            The GameObject reference to a character.
        """
        self._characters.add(character)

    def remove(self, character: GameObject) -> None:
        """Remove a character.

        Parameters
        ----------
        character
            The GameObject reference to a character.
        """
        self._characters.remove(character)

    def clear(self) -> None:
        """Remove all characters from tracking."""
        self._characters.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": [entry.uid for entry in self._characters],
        }

    def __contains__(self, item: GameObject) -> bool:
        return item in self._characters

    def __iter__(self) -> Iterator[GameObject]:
        return self._characters.__iter__()

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            self._characters,
        )


@dataclass
class CurrentSettlement(Component, ISerializable):
    """Tracks the settlement that a GameObject belongs to."""

    settlement: GameObject
    """The GameObject ID of a settlement."""

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.settlement})"

    def to_dict(self) -> Dict[str, Any]:
        return {"settlement": self.settlement.uid}


@dataclass
class PrefabName(Component, ISerializable):
    """Tracks the name of the prefab used to instantiate a GameObject."""

    prefab: str
    """The name of a prefab."""

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.prefab})"

    def to_dict(self) -> Dict[str, Any]:
        return {"prefab": self.prefab}


class OwnedBy(Component, ISerializable):
    """Tags a GameObject as being owned by another."""

    __slots__ = "owner"

    owner: GameObject
    """GameObject that owns this GameObject."""

    def __init__(self, owner: GameObject) -> None:
        super().__init__()
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {"owner": self.owner.uid}
