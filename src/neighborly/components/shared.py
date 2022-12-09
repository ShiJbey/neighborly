from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ordered_set import OrderedSet

from neighborly.core.ecs import Component


class Age(Component):
    """
    Tracks the number of years old that an entity is
    """

    __slots__ = "value"

    def __init__(self, age: float = 0.0) -> None:
        super(Component, self).__init__()
        self.value: float = age

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class Lifespan(Component):
    """Defines how long a character lives on average"""

    __slots__ = "value"

    def __init__(self, lifespan: float) -> None:
        super(Component, self).__init__()
        self.value: float = lifespan

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class Building(Component):
    """
    Building components are attached to structures (like businesses and residences)
    that are currently present in the town.

    Attributes
    ----------
    building_type: str
        What kind of building is this
    lot: int
        ID of the lot this building is on
    """

    __slots__ = "building_type", "lot"

    def __init__(self, building_type: str, lot: int) -> None:
        super(Component, self).__init__()
        self.building_type: str = building_type
        self.lot: int = lot

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "building_type": self.building_type}


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "entities"

    def __init__(self) -> None:
        super(Component, self).__init__()
        self.entities: OrderedSet[int] = OrderedSet([])

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
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

    __slots__ = "capacity"

    def __init__(self, capacity: int) -> None:
        super(Component, self).__init__()
        self.capacity: int = capacity

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "capacity": self.capacity}


class OpenToPublic(Component):
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
        return {**super().to_dict(), "location": self.location}

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
        return {**super().to_dict(), "aliases": {**self.aliases}}

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
        return {**super().to_dict(), "x": self.x, "y": self.y}


class Active(Component):
    """Tags a GameObject as active within the simulation"""

    pass
