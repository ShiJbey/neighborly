"""Components definitions used by multiple types of GameObjects.

"""

from __future__ import annotations

from typing import Any, Dict, Iterator, Tuple

from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject, ISerializable, TagComponent
from neighborly.tracery import Tracery


class Name(Component, ISerializable):
    """The name of a GameObject.

    Parameters
    ----------
    value
        The name value.
    """

    value: str
    """The GameObject's name."""

    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value}

    def __str__(self) -> str:
        return self.value

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    @classmethod
    def create(cls, gameobject: GameObject, **kwargs: Any) -> Name:
        tracery = gameobject.world.resource_manager.get_resource(Tracery)
        value: str = kwargs.get("value", "")
        return Name(tracery.generate(value))


class Age(Component, ISerializable):
    """Tracks the number of years old that a GameObject is.

    Parameters
    ----------
    value
        The age value.
    """

    value: int = 0
    """The number of years old."""

    def __init__(self, value: int = 0) -> None:
        super().__init__()
        self.value = value

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


class Lifespan(Component, ISerializable):
    """How long a GameObject lives on average.

    Parameters
    ----------
    value
        A number of years.
    """

    value: int
    """The number of years."""

    def __init__(self, value: int) -> None:
        super().__init__()
        self.value = value

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


class Location(TagComponent, ISerializable):
    """Anywhere GameObjects may be."""

    pass


class Position2D(Component, ISerializable):
    """The 2-dimensional position of a GameObject.

    Parameters
    ----------
    x
        The x-position of the GameObject.
    y
        The y-position of the GameObject.
    """

    x: int
    """The x-position of the GameObject."""

    y: int
    """The y-position of the GameObject."""

    def __init__(self, x: int = 0, y: int = 0) -> None:
        super().__init__()
        self.x = x
        self.y = y

    def as_tuple(self) -> Tuple[int, int]:
        return self.x, self.y

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y}

    def __repr__(self):
        return f"{self.__class__.__name__}(x:{self.x}, y:{self.y})"


class FrequentedLocations(Component, ISerializable):
    """Tracks the locations that a character frequents."""

    __slots__ = "_locations"

    _locations: OrderedSet[GameObject]
    """A set of GameObject IDs of locations."""

    def __init__(self) -> None:
        super().__init__()
        self._locations = OrderedSet([])

    def add_location(self, location: GameObject) -> None:
        """Add a new location.

        Parameters
        ----------
        location
           A GameObject reference to a location.
        """
        self._locations.add(location)
        if frequented_by := location.try_component(FrequentedBy):
            if self.gameobject not in frequented_by:
                frequented_by.add_character(self.gameobject)

    def remove_location(self, location: GameObject) -> bool:
        """Remove a location.

        Parameters
        ----------
        location
            A GameObject reference to a location to remove.

        Returns
        -------
        bool
            Returns True of a location was removed. False otherwise.
        """
        if location in self._locations:
            self._locations.remove(location)
            if frequented_by := location.try_component(FrequentedBy):
                if self.gameobject in frequented_by:
                    frequented_by.remove_character(self.gameobject)
            return True
        return False

    def clear(self) -> None:
        """Remove all location IDs from the component."""
        for location in reversed(self._locations):
            self.remove_location(location)
        self._locations.clear()

    def on_deactivate(self) -> None:
        self.clear()

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
    """A physical building in the settlement."""

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


class FrequentedBy(Component, ISerializable):
    """Tracks the characters that frequent a location."""

    __slots__ = "_characters"

    _characters: OrderedSet[GameObject]
    """GameObject IDs of characters that frequent the location."""

    def __init__(self) -> None:
        super().__init__()
        self._characters = OrderedSet([])

    def on_deactivate(self) -> None:
        self.clear()

    def add_character(self, character: GameObject) -> None:
        """Add a character.

        Parameters
        ----------
        character
            The GameObject reference to a character.
        """
        self._characters.add(character)
        if frequented_locations := character.try_component(FrequentedLocations):
            if self.gameobject not in frequented_locations:
                frequented_locations.add_location(self.gameobject)

    def remove_character(self, character: GameObject) -> bool:
        """Remove a character.

        Parameters
        ----------
        character
            The character to remove.

        Returns
        -------
        bool
            Returns True if a character was removed. False otherwise.
        """
        if character in self._characters:
            self._characters.remove(character)
            if frequented_locations := character.try_component(FrequentedLocations):
                if self.gameobject in frequented_locations:
                    frequented_locations.remove_location(self.gameobject)
            return True

        return False

    def clear(self) -> None:
        """Remove all characters from tracking."""
        for character in reversed(self._characters):
            self.remove_character(character)
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


class Owner(Component, ISerializable):
    """Tags a GameObject as being owned by another."""

    __slots__ = "owner"

    owner: GameObject
    """GameObject that owns this GameObject."""

    def __init__(self, owner: GameObject) -> None:
        super().__init__()
        self.owner = owner

    def to_dict(self) -> Dict[str, Any]:
        return {"owner": self.owner.uid}

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.owner.name})"
