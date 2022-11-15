from typing import Any, Dict

from neighborly.core.character import LifeStageAges
from neighborly.core.ecs import Component, component_info
from neighborly.core.time import SimDateTime


class Departed(Component):

    pass


class Vacant(Component):
    """A tag component for residences that do not currently have any one living there"""

    pass


class Human(Component):
    """Marks an entity as a Human"""

    pass


class MaxCapacity(Component):

    __slots__ = "capacity"

    def __init__(self, capacity: int) -> None:
        super().__init__()
        self.capacity = capacity

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "capacity": self.capacity}

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tcapacity: {self.capacity}")


class Name(Component):
    """
    The string name of an entity
    """

    __slots__ = "value"

    def __init__(self, name: str = "") -> None:
        super().__init__()
        self.value = name

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tvalue: {self.value}")


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

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tvalue: {self.value}")


class CanAge(Component):
    """
    This component flags an entity as being able to age when time passes.
    """

    pass


class Mortal(Component):
    pass


class Immortal(Component):
    pass


class OpenToPublic(Component):
    """
    This is an empty component that flags a location as one that characters
    may travel to when they don't have somewhere to be in the Routine component
    """

    pass


class CurrentLocation(Component):
    """Tracks the current location of this game object"""

    __slots__ = "location"

    def __init__(self, location: int) -> None:
        super().__init__()
        self.location: int = location

    def to_dict(self) -> Dict[str, Any]:
        return {"location": self.location}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.location})"

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tlocation: {self.location}")


class Lifespan(Component):
    """How long this entity usually lives"""

    __slots__ = "value"

    def __init__(self, lifespan: float) -> None:
        super().__init__()
        self.value: float = lifespan

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.value})"

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tvalue: {self.value}")


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

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\taliases: {self.aliases}")


class LifeStages(Component):
    """Tracks what stage of life an entity is in"""

    __slots__ = "stages"

    def __init__(self, stages: LifeStageAges) -> None:
        super().__init__()
        self.stages: LifeStageAges = stages

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "stages": {**self.stages}}

    def __repr__(self):
        return f"{self.__class__.__name__}({self.stages})"


class CanGetPregnant(Component):
    """Indicates that an entity is capable of giving birth"""

    pass


@component_info("Child", "Character is seen as a child in the eyes of society")
class Child(Component):
    pass


@component_info(
    "Adolescent",
    "Character is seen as an adolescent in the eyes of society",
)
class Teen(Component):
    pass


@component_info(
    "Young Adult",
    "Character is seen as a young adult in the eyes of society",
)
class YoungAdult(Component):
    pass


@component_info(
    "Adult",
    "Character is seen as an adult in the eyes of society",
)
class Adult(Component):
    pass


@component_info(
    "Senior",
    "Character is seen as a senior in the eyes of society",
)
class Elder(Component):
    pass


@component_info(
    "Deceased",
    "This entity is dead",
)
class Deceased(Component):
    pass


@component_info("Retired", "This entity retired from their last occupation")
class Retired(Component):
    pass


@component_info("Dependent", "This entity is dependent on their parents")
class Dependent(Component):
    pass


class CanDate(Component):
    pass


class CanGetMarried(Component):
    pass


class IsSingle(Component):
    pass


class Pregnant(Component):

    __slots__ = "partner_name", "partner_id", "due_date"

    def __init__(
        self, partner_name: str, partner_id: int, due_date: SimDateTime
    ) -> None:
        super().__init__()
        self.partner_name: str = partner_name
        self.partner_id: int = partner_id
        self.due_date: SimDateTime = due_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "partner_name": self.partner_name,
            "partner_id": self.partner_id,
            "due_date": self.partner_id,
        }

    def pprint(self) -> None:
        print(
            f"{self.__class__.__name__}:\n"
            f"\tpartner: {self.partner_name}({self.partner_id})"
            f"\tdue date: {self.due_date.to_date_str()}"
        )


@component_info("Male", "This entity is perceived as masculine.")
class Male(Component):
    pass


@component_info("Female", "This entity is perceived as feminine.")
class Female(Component):
    pass


@component_info("NonBinary", "This entity is perceived as non-binary.")
class NonBinary(Component):
    pass


@component_info("College Graduate", "This entity graduated from college.")
class CollegeGraduate(Component):
    pass


@component_info("Active", "This entity is in the town and active in the simulation")
class Active(Component):
    pass
