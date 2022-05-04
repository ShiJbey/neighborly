from typing import Dict, Any

from ordered_set import OrderedSet

from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "characters_present", "max_capacity"

    def __init__(self, max_capacity: int) -> None:
        super().__init__()
        self.max_capacity: int = max_capacity
        self.characters_present: OrderedSet[int] = OrderedSet()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "max_capacity": self.max_capacity,
            "characters_present": list(self.characters_present),
        }

    def add_character(self, character: int) -> None:
        self.characters_present.append(character)

    def remove_character(self, character: int) -> None:
        self.characters_present.remove(character)

    def has_character(self, character: int) -> bool:
        return character in self.characters_present

    def __repr__(self) -> str:
        return "{}(present={}, max_capacity={})".format(
            self.__class__.__name__,
            self.characters_present,
            self.max_capacity,
        )


class LocationFactory(AbstractFactory):
    def __init__(self):
        super().__init__("Location")

    def create(self, spec: ComponentSpec, **kwargs) -> Location:
        return Location(max_capacity=spec.get_attribute("max capacity", 9999))
