from typing import List, Optional


class GameObject:
    __slots__ = "name", "description", "tags"

    def __init__(self, name: str, description: str = '', tags: Optional[List[str]] = None) -> None:
        self.name: str = name
        self.description: str = description
        self.tags: List[str] = tags if tags else []

    def __repr__(self) -> str:
        return "{}(name={}, description={}, tags={})".format(
            self.__class__.__name__,
            self.name,
            self.description,
            self.tags
        )
