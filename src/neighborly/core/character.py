from __future__ import annotations

from typing import Any, Dict

from typing_extensions import TypedDict

from neighborly.core.ecs import Component, World


class LifeStageAges(TypedDict):
    """Ages when characters are in certain stages of their lives"""

    child: int
    teen: int
    young_adult: int
    adult: int
    elder: int


class CharacterName(Component):
    __slots__ = "firstname", "surname"

    def __init__(self, firstname: str, surname: str) -> None:
        super().__init__()
        self.firstname: str = firstname
        self.surname: str = surname

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "firstname": self.firstname,
            "surname": self.surname,
        }

    def __repr__(self) -> str:
        return f"{self.firstname} {self.surname}"

    def __str__(self) -> str:
        return f"{self.firstname} {self.surname}"

    def pprint(self) -> None:
        print(f"{self.__class__.__name__}:\n" f"\tname: {str(self)}")

    @classmethod
    def create(cls, world: World, **kwargs) -> Component:
        first_name, surname = kwargs.get(
            "name_format", "#first_name# #family_name#"
        ).split(" ")
        return cls(first_name, surname)


class GameCharacter(Component):
    pass
