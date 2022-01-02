from typing import List


class Location:
    """Anywhere where game characters may be"""

    __slots__ = "characters_present"

    def __ini__(self) -> None:
        self.characters_present: List[int] = []
