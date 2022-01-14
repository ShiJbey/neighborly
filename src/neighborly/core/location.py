from typing import Dict, List, Optional

from neighborly.core.activity import get_activity_flags


class Location:
    """Anywhere where game characters may be"""

    __slots__ = "characters_present", "activities", "activity_flags", "max_capacity"

    def __init__(self, max_capacity: int = 9999, activities: Optional[List[str]] = None) -> None:
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

    def __repr__(self) -> str:
        return "{}(present={}, activities={}, max_capacity={})".format(
            self.__class__.__name__,
            self.characters_present,
            self.activities,
            self.max_capacity
        )
