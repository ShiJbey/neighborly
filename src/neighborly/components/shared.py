from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Optional, Set

from ordered_set import OrderedSet  # type: ignore

from neighborly.core.ecs import Component
from neighborly.core.status import StatusComponent


class Name(Component):
    """The name of the GameObject"""

    __slots__ = "value"

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value: str = value

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    def __str__(self) -> str:
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class Age(Component):
    """
    Tracks the number of years old that an entity is
    """

    __slots__ = "value"

    def __init__(self, value: float = 0.0) -> None:
        super().__init__()
        self.value: float = value

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


class Lifespan(Component):
    """Defines how long a GameObject lives on average"""

    __slots__ = "value"

    def __init__(self, value: float) -> None:
        super().__init__()
        self.value: float = value

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


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "entities"

    def __init__(self) -> None:
        super(Component, self).__init__()
        self.entities: OrderedSet[int] = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entities": list(self.entities),
        }

    def add_entity(self, entity: int) -> None:
        self.entities.append(entity)

    def remove_entity(self, entity: int) -> None:
        self.entities.remove(entity)

    def has_entity(self, entity: int) -> bool:
        return entity in self.entities

    def __repr__(self) -> str:
        return "{}(entities={})".format(
            self.__class__.__name__,
            self.entities,
        )


class MaxCapacity(Component):
    """
    Limits the number of characters that may be present at
    any one location
    """

    __slots__ = "value"

    def __init__(self, value: int) -> None:
        super().__init__()
        self.value: int = value

    def to_dict(self) -> Dict[str, Any]:
        return {"capacity": self.value}


class OpenToPublic(StatusComponent):
    """
    Tags a location as one that any character may travel to
    """

    pass


class CurrentLocation(Component):
    """Tracks the current location of a GameObject"""

    __slots__ = "location"

    def __init__(self, location: int) -> None:
        super(Component, self).__init__()
        self.location: int = location

    def to_dict(self) -> Dict[str, Any]:
        return {"location": self.location}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.location})"


class LocationAliases(Component):
    """
    Keeps record of strings mapped the IDs of locations in the world
    """

    __slots__ = "aliases"

    def __init__(self) -> None:
        super(Component, self).__init__()
        self.aliases: Dict[str, int] = {}

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
class Position2D(Component):
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y}


class FrequentedLocations(Component):
    """Tracks the locations that a character frequents"""

    __slots__ = "locations"

    def __init__(self, locations: Optional[Iterable[int]] = None) -> None:
        super().__init__()
        self.locations: Set[int] = set(locations) if locations else set()

    def add(self, location: int) -> None:
        self.locations.add(location)

    def remove(self, location: int) -> None:
        self.locations.remove(location)

    def clear(self) -> None:
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


class Building(Component):
    """
    Building components are attached to structures (like businesses and residences)
    that are currently present in the town.

    Attributes
    ----------
    building_type: str
        What kind of building is this
    """

    __slots__ = "building_type"

    def __init__(self, building_type: str) -> None:
        super().__init__()
        self.building_type: str = building_type

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
class CurrentLot(Component):
    """Tracks the lot that a building belongs to

    Attributes
    ----------
    lot: int
        The ID of a lot within a SettlementMap
    """

    lot: int

    def to_dict(self) -> Dict[str, Any]:
        return {"lot": self.lot}


class FrequentedBy(Component):
    """Tracks the characters that frequent a location"""

    __slots__ = "_characters"

    def __init__(self) -> None:
        super().__init__()
        self._characters: OrderedSet[int] = OrderedSet([])

    def add(self, character: int) -> None:
        self._characters.add(character)

    def remove(self, character: int) -> None:
        self._characters.remove(character)

    def clear(self) -> None:
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
class CurrentSettlement(Component):
    """Tracks the ID of the settlement that a GameObject is currently in

    Attributes
    ----------
    settlement: int
        The GameObject ID of a settlement
    """

    settlement: int

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.settlement})"

    def to_dict(self) -> Dict[str, Any]:
        return {"settlement": self.settlement}


@dataclass
class PrefabName(Component):
    """Tracks the ID of the settlement that a GameObject is currently in

    Attributes
    ----------
    prefab: str
        The name of the prefab used to construct this GameObject
    """

    prefab: str

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.prefab})"

    def to_dict(self) -> Dict[str, Any]:
        return {"prefab": self.prefab}
