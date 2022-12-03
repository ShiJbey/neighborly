from __future__ import annotations

from enum import Enum, IntEnum, auto
from typing import Any, Dict

from neighborly.core.ecs import Component


class GameCharacter(Component):
    __slots__ = "first_name", "last_name"

    def __init__(self, first_name: str, last_name: str) -> None:
        super().__init__()
        self.first_name: str = first_name
        self.last_name: str = last_name

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "first_name": self.last_name,
            "last_name": self.last_name,
        }

    def __repr__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class CharacterAgingConfig(Component):
    """
    Defines settings for how LifeStage changes as a function of age
    as well as settings for the character's lifespan
    """

    __slots__ = (
        "lifespan",
        "child_age",
        "adolescent_age",
        "young_adult_age",
        "adult_age",
        "senior_age",
    )

    def __init__(
        self,
        lifespan: int,
        child_age: int,
        adolescent_age: int,
        young_adult_age: int,
        adult_age: int,
        senior_age: int,
    ) -> None:
        super().__init__()
        self.lifespan: int = lifespan
        self.child_age: int = child_age
        self.adolescent_age: int = adolescent_age
        self.young_adult_age: int = young_adult_age
        self.adult_age: int = adult_age
        self.senior_age: int = senior_age

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "lifespan": self.lifespan,
            "child_age": self.child_age,
            "adolescent_age": self.adolescent_age,
            "young_adult_age": self.young_adult_age,
            "adult_age": self.adult_age,
            "senior_age": self.senior_age,
        }


class LifeStageValue(IntEnum):
    Child = auto()
    Adolescent = auto()
    YoungAdult = auto()
    Adult = auto()
    Senior = auto()


class LifeStage(Component):
    """Tracks what stage of life a character is in"""

    __slots__ = "stage"

    def __init__(self, stage: LifeStageValue) -> None:
        super().__init__()
        self.stage: LifeStageValue = stage

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "stage": self.stage.name}

    def __str__(self) -> str:
        return self.stage.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.stage.name})"


class GenderValue(Enum):
    Male = auto()
    Female = auto()
    NonBinary = auto()


class Gender(Component):
    """Tracks the gender expression of a character"""

    __slots__ = "value"

    def __init__(self, value: GenderValue) -> None:
        super().__init__()
        self.value: GenderValue = value

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "value": self.value}

    def __str__(self) -> str:
        return self.value.name

    def __repr__(self) -> str:
        return f"Gender({self.value})"
