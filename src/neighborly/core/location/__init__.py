from typing import Dict, List, Optional
from neighborly.core.activity import get_activity_flags


class Location:
    """Anywhere where game characters may be"""

    __slots__ = "characters_present", "activities", "activity_flags"

    def __init__(self, activities: Optional[List[str]] = None) -> None:
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
