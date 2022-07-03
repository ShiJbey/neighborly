from typing import Any, Dict, List, Optional, Set

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, World
from neighborly.core.engine import AbstractFactory, ComponentDefinition


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "characters_present", "max_capacity", "name", "whitelist", "is_private"

    def __init__(
        self,
        max_capacity: int,
        name: str = "",
        whitelist: Optional[List[int]] = None,
        is_private: bool = False,
    ) -> None:
        super().__init__()
        self.name: str = name
        self.max_capacity: int = max_capacity
        self.characters_present: OrderedSet[int] = OrderedSet([])
        self.whitelist: Set[int] = set(whitelist if whitelist else [])
        self.is_private: bool = is_private

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "max_capacity": self.max_capacity,
            "characters_present": list(self.characters_present),
            "whitelist": list(self.whitelist),
            "is_private": self.is_private,
        }

    def can_enter(self, character_id: int) -> bool:
        """Return true if the given character is allowed to enter this location"""
        if self.is_private is False:
            return True

        return character_id in self.whitelist

    def add_character(self, character: int) -> None:
        self.characters_present.append(character)

    def remove_character(self, character: int) -> None:
        self.characters_present.remove(character)

    def has_character(self, character: int) -> bool:
        return character in self.characters_present

    def __repr__(self) -> str:
        return "{}(name={}, present={}, max_capacity={}, whitelist={}, is_private={})".format(
            self.__class__.__name__,
            self.name,
            self.characters_present,
            self.max_capacity,
            self.whitelist,
            self.is_private,
        )


class LocationFactory(AbstractFactory):
    def __init__(self):
        super().__init__("Location")

    def create(self, world: World, **kwargs) -> Location:
        return Location(max_capacity=kwargs.get("max capacity", 9999))
