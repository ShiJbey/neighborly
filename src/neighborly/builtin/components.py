from typing import Any, Dict

from neighborly.core.ecs import Component


class Departed(Component):
    """Tags a character as departed from the simulation"""

    pass


class Vacant(Component):
    """Tags a residence that does not currently have anyone living there"""

    pass


class MaxCapacity(Component):
    """
    Limits the number of characters that may be present at
    any one location
    """

    __slots__ = "capacity"

    def __init__(self, capacity: int) -> None:
        super().__init__()
        self.capacity: int = capacity

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "capacity": self.capacity}


class Age(Component):
    """
    Tracks the number of years old that an entity is
    """

    __slots__ = "value"

    def __init__(self, age: float = 0.0) -> None:
        super().__init__()
        self.value: float = age

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class CanAge(Component):
    """
    Tags a GameObject as being able to change life stages as time passes
    """

    pass


class CanDie(Component):
    """
    Tags a GameObject as being able to die from natural causes
    """

    pass


class OpenToPublic(Component):
    """
    Tags a location as one that any character may travel to
    """

    pass


class CurrentLocation(Component):
    """Tracks the current location of a GameObject"""

    __slots__ = "location"

    def __init__(self, location: int) -> None:
        super().__init__()
        self.location: int = location

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "location": self.location}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.location})"


class Lifespan(Component):
    """Defines how long a character lives on average"""

    __slots__ = "value"

    def __init__(self, lifespan: float) -> None:
        super().__init__()
        self.value: float = lifespan

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"


class LocationAliases(Component):
    """
    Keeps record of strings mapped the IDs of locations in the world
    """

    __slots__ = "aliases"

    def __init__(self) -> None:
        super().__init__()
        self.aliases: Dict[str, int] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "aliases": {**self.aliases}}

    def __contains__(self, item: str) -> bool:
        return item in self.aliases

    def __getitem__(self, item: str) -> int:
        return self.aliases[item]

    def __setitem__(self, key: str, value: int) -> None:
        self.aliases[key] = value

    def __delitem__(self, key) -> None:
        del self.aliases[key]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.aliases})"


class CanGetPregnant(Component):
    """Tags a character as capable of giving birth"""

    pass


class Deceased(Component):
    """Tags a character as deceased"""

    pass


class Retired(Component):
    """Tags a character as retired"""

    pass


class CollegeGraduate(Component):
    """Tags a character as having graduated from college"""

    pass


class Active(Component):
    """Tags a character as active within the simulation"""

    pass
