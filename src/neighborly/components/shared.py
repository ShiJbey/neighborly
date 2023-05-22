from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional

from ordered_set import OrderedSet  # type: ignore

from neighborly.core.ecs.ecs import Component, ISerializable
from neighborly.core.status import StatusComponent


@dataclass
class Name(Component, ISerializable):
    """The name of the GameObject."""

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
    """Tracks the number of years old that an GameObject is."""

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
    """Defines how long a GameObject lives on average."""

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
    """Anywhere where game characters may be."""

    __slots__ = "entities"

    entities: OrderedSet[int]
    """All the GameObjects currently at this location."""

    def __init__(self) -> None:
        super().__init__()
        self.entities = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": list(self.entities),
        }

    def add_entity(self, entity: int) -> None:
        """Add an entity to the location.

        Parameters
        ----------
        entity
            The GameObject ID of the entity to add.
        """
        self.entities.append(entity)

    def remove_entity(self, entity: int) -> None:
        """Remove an entity from the location.

        Parameters
        ----------
        entity
            The GameObject ID of the entity to remove.
        """
        self.entities.remove(entity)

    def has_entity(self, entity: int) -> bool:
        """Check if an entity is at the location.

        Parameters
        ----------
        entity
            The GameObject ID of the entity to check for.

        Returns
        -------
        bool
            True if the GameObject is present, False otherwise.
        """
        return entity in self.entities

    def __repr__(self) -> str:
        return "{}(entities={})".format(
            self.__class__.__name__,
            self.entities,
        )


@dataclass
class MaxCapacity(Component, ISerializable):
    """Limits the number of characters that may be present at a location."""

    value: int
    """The number of characters."""

    def to_dict(self) -> Dict[str, Any]:
        return {"capacity": self.value}


class OpenToPublic(StatusComponent, ISerializable):
    """Tags a location as being eligible to travel to."""

    pass


@dataclass
class CurrentLocation(Component, ISerializable):
    """Tracks the current location of a GameObject."""

    location: int
    """The GameObjectID of the location."""

    def to_dict(self) -> Dict[str, Any]:
        return {"location": self.location}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.location})"


class LocationAliases(Component, ISerializable):
    """A record of strings mapped the IDs of locations in the world.

    Notes
    -----
    This component allows us to use ID-agnostic location aliases for places like
    home and work.
    """

    __slots__ = "aliases"

    aliases: Dict[str, int]
    """The aliases of locations mapped to their GameObject ID."""

    def __init__(self) -> None:
        super().__init__()
        self.aliases = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"aliases": {**self.aliases}}

    def __contains__(self, item: str) -> bool:
        return item in self.aliases

    def __getitem__(self, item: str) -> int:
        return self.aliases[item]

    def __setitem__(self, key: str, value: int) -> None:
        self.aliases[key] = value

    def __delitem__(self, key: str) -> None:
        del self.aliases[key]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.aliases})"


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

    __slots__ = "locations"

    locations: OrderedSet[int]
    """A set of GameObject IDs of locations."""

    def __init__(self, locations: Optional[Iterable[int]] = None) -> None:
        """
        Parameters
        ----------
        locations
            An iterable of GameObject IDs of locations.
        """
        super().__init__()
        self.locations = OrderedSet(locations) if locations else OrderedSet()

    def add(self, location: int) -> None:
        """Add a new location.

        Parameters
        ----------
        location
            The GameObject ID of a location.
        """
        self.locations.add(location)

    def remove(self, location: int) -> None:
        """Remove a location.

        Parameters
        ----------
        location
            The GamerObject ID of the location to remove.
        """
        self.locations.remove(location)

    def clear(self) -> None:
        """Remove all location IDs from the component."""
        self.locations.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {"locations": list(self.locations)}

    def __contains__(self, item: int) -> bool:
        return item in self.locations

    def __iter__(self) -> Iterator[int]:
        return self.locations.__iter__()

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.locations.__repr__()})"


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

    _characters: OrderedSet[int]
    """GameObject IDs of characters that frequent the location."""

    def __init__(self) -> None:
        super().__init__()
        self._characters = OrderedSet([])

    def add(self, character: int) -> None:
        """Add a character.

        Parameters
        ----------
        character
            The GameObject ID of a character.
        """
        self._characters.add(character)

    def remove(self, character: int) -> None:
        """Remove a character.

        Parameters
        ----------
        character
            The GameObject ID of a character.
        """
        self._characters.remove(character)

    def clear(self) -> None:
        """Remove all characters from tracking."""
        self._characters.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "characters": list(self._characters),
        }

    def __contains__(self, item: int) -> bool:
        return item in self._characters

    def __iter__(self) -> Iterator[int]:
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
    """Tracks the ID of the settlement that a GameObject is currently in."""

    settlement: int
    """The GameObject ID of a settlement."""

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.settlement})"

    def to_dict(self) -> Dict[str, Any]:
        return {"settlement": self.settlement}


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
