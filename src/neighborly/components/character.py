from __future__ import annotations

from enum import Enum, IntEnum, auto
from typing import Any, Dict, List, Optional

import numpy as np
from numpy import typing as npt

from neighborly.core.ecs import Component


class Departed(Component):
    """Tags a character as departed from the simulation"""

    pass


class CanAge(Component):
    """
    Tags a GameObject as being able to change life stages as time passes
    """

    pass


class CanDie(Component):
    """
    Tags a GameObject as being able to die from natural causes
    """

    pass


class CanGetPregnant(Component):
    """Tags a character as capable of giving birth"""

    pass


class Deceased(Component):
    """Tags a character as deceased"""

    pass


class Retired(Component):
    """Tags a character as retired"""

    pass


class CollegeGraduate(Component):
    """Tags a character as having graduated from college"""

    pass


class PersonalValue(Enum):
    ADVENTURE = "adventure"
    AMBITION = "ambition"
    EXCITEMENT = "excitement"
    COMMERCE = "commerce"
    CONFIDENCE = "confidence"
    CURIOSITY = "curiosity"
    FAMILY = "family"
    FRIENDSHIP = "friendship"
    WEALTH = "wealth"
    HEALTH = "health"
    INDEPENDENCE = "independence"
    KNOWLEDGE = "knowledge"
    LEISURE_TIME = "leisure-time"
    LOYALTY = "loyalty"
    LUST = "lust"
    MATERIAL_THINGS = "material things"
    NATURE = "nature"
    PEACE = "peace"
    POWER = "power"
    RELIABILITY = "reliability"
    ROMANCE = "romance"
    SINGLE_MINDEDNESS = "single mindedness"
    SOCIAL = "social"
    SELF_CONTROL = "self-control"
    TRADITION = "tradition"
    TRANQUILITY = "tranquility"


_PERSONAL_VALUE_INDICES: Dict[str, int] = {
    str(value_trait.value): index for index, value_trait in enumerate(PersonalValue)
}


class PersonalValues(Component):
    """
    Values are what an entity believes in. They are used
    for decision-making and relationship compatibility among
    other things.

    Individual values are integers on the range [-50,50], inclusive.

    This model of entity values is borrowed from Dwarf Fortress'
    model of entity beliefs/values outlined at the following link
    https://dwarffortresswiki.org/index.php/DF2014:Personality_trait
    """

    TRAIT_MAX = 50
    TRAIT_MIN = -50

    __slots__ = "_traits"

    def __init__(
        self, overrides: Optional[Dict[str, int]] = None, default: int = 0
    ) -> None:
        super().__init__()
        self._traits: npt.NDArray[np.int32] = np.array(  # type: ignore
            [default] * len(_PERSONAL_VALUE_INDICES.keys()), dtype=np.int32
        )

        if overrides:
            for trait, value in overrides.items():
                self._traits[_PERSONAL_VALUE_INDICES[trait]] = max(
                    self.TRAIT_MIN, min(self.TRAIT_MAX, value)
                )

    @property
    def traits(self) -> npt.NDArray[np.int32]:
        return self._traits

    @staticmethod
    def compatibility(
        character_a: PersonalValues, character_b: PersonalValues
    ) -> float:
        # Cosine similarity is a value between -1 and 1
        cos_sim: float = np.dot(character_a.traits, character_b.traits) / (  # type: ignore
            np.linalg.norm(character_a.traits) * np.linalg.norm(character_b.traits)  # type: ignore
        )

        return cos_sim

    def get_high_values(self, n: int = 3) -> List[str]:
        """Return the value names associated with the n values"""
        # This code is adapted from https://stackoverflow.com/a/23734295

        ind = np.argpartition(self.traits, -n)[-n:]  # type: ignore

        value_names = list(_PERSONAL_VALUE_INDICES.keys())

        return [value_names[i] for i in ind]

    def __getitem__(self, trait: str) -> int:
        return self._traits[_PERSONAL_VALUE_INDICES[trait]]

    def __setitem__(self, trait: str, value: int) -> None:
        self._traits[_PERSONAL_VALUE_INDICES[trait]] = max(
            PersonalValues.TRAIT_MIN, min(PersonalValues.TRAIT_MAX, value)
        )

    def __str__(self) -> str:
        return f"Values Most: {self.get_high_values()}"

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._traits.__repr__())

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            **{
                trait.name: self._traits[i]
                for i, trait in enumerate(list(PersonalValue))
            },
        }


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
