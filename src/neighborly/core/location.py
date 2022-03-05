from typing import List, Optional

from neighborly.core.activity import get_activity_flags
from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


class Location(Component):
    """Anywhere where game characters may be"""

    __slots__ = "characters_present", "activities", "activity_flags", "max_capacity"

    def __init__(
            self, max_capacity: int = 9999, activities: Optional[List[str]] = None
    ) -> None:
        super().__init__()
        self.max_capacity: int = max_capacity
        self.characters_present: List[int] = []
        self.activities: List[str] = activities if activities else []
        self.activity_flags: int = 0

        for activity in self.activities:
            self.activity_flags |= get_activity_flags(activity)[0]

    def has_flags(self, *flag_strs: str) -> bool:
        flags = get_activity_flags(*flag_strs)
        for flag in flags:
            if self.activity_flags & flag == 0:
                return False
        return True

    def add_character(self, character: int) -> None:
        self.characters_present.append(character)

    def remove_character(self, character: int) -> None:
        self.characters_present.remove(character)

    def __repr__(self) -> str:
        return "{}(present={}, activities={}, max_capacity={})".format(
            self.__class__.__name__,
            self.characters_present,
            self.activities,
            self.max_capacity,
        )


class LocationFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Location")

    def create(self, spec: ComponentSpec) -> Location:
        return Location(max_capacity=spec.get_attributes().get("max capacity", 9999), activities=spec["activities"])
