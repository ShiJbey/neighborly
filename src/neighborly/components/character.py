from __future__ import annotations

import dataclasses
import enum
from abc import ABC
from inspect import isclass
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, Union

import numpy as np
from numpy import typing as npt

from neighborly.core.ecs import Component
from neighborly.core.relationship import RelationshipStatus
from neighborly.core.status import StatusComponent
from neighborly.core.time import SimDateTime
from neighborly.core.traits import TraitComponent


class GameCharacter(Component):
    """
    This component is attached to all GameObjects that are characters in the simulation

    Attributes
    ----------
    first_name: str
        The character's first name
    last_name: str
        The character's last or family name
    """

    __slots__ = "first_name", "last_name"

    def __init__(
        self,
        first_name: str,
        last_name: str,
    ) -> None:
        super().__init__()
        self.first_name: str = first_name
        self.last_name: str = last_name

    @property
    def full_name(self) -> str:
        """Returns the full name of the character"""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
        }

    def __repr__(self) -> str:
        return "{}(name={})".format(
            self.__class__.__name__,
            self.full_name,
        )

    def __str__(self) -> str:
        return self.full_name


class Departed(StatusComponent):
    """Tags a character as departed from the simulation"""

    is_persistent = True


class CanAge(TraitComponent):
    """
    Tags a GameObject as being able to change life stages as time passes
    """

    pass


class Mortal(StatusComponent):
    """
    Tags a GameObject as being able to die from natural causes
    """

    is_persistent = True


class CanGetPregnant(TraitComponent):
    """Tags a character as capable of giving birth"""

    pass


class Deceased(StatusComponent):
    """Tags a character as deceased"""

    is_persistent = True


class Retired(StatusComponent):
    """Tags a character as retired"""

    # is_persistent = True


class Virtue(enum.IntEnum):
    ADVENTURE = 0
    AMBITION = enum.auto()
    EXCITEMENT = enum.auto()
    COMMERCE = enum.auto()
    CONFIDENCE = enum.auto()
    CURIOSITY = enum.auto()
    FAMILY = enum.auto()
    FRIENDSHIP = enum.auto()
    WEALTH = enum.auto()
    HEALTH = enum.auto()
    INDEPENDENCE = enum.auto()
    KNOWLEDGE = enum.auto()
    LEISURE_TIME = enum.auto()
    LOYALTY = enum.auto()
    LUST = enum.auto()
    MATERIAL_THINGS = enum.auto()
    NATURE = enum.auto()
    PEACE = enum.auto()
    POWER = enum.auto()
    RELIABILITY = enum.auto()
    ROMANCE = enum.auto()
    SINGLE_MINDEDNESS = enum.auto()
    SOCIALIZING = enum.auto()
    SELF_CONTROL = enum.auto()
    TRADITION = enum.auto()
    TRANQUILITY = enum.auto()


class Virtues(Component):
    """
    Values are what an entity believes in. They are used
    for decision-making and relationship compatibility among
    other things.


    Individual values are integers on the range [-50,50], inclusive.

    This model of entity values is borrowed from Dwarf Fortress'
    model of entity beliefs/values outlined at the following link
    https://dwarffortresswiki.org/index.php/DF2014:Personality_trait
    """

    VIRTUE_MAX = 50
    VIRTUE_MIN = -50

    __slots__ = "_virtues"

    def __init__(self, overrides: Optional[Dict[str, int]] = None) -> None:
        super().__init__()
        self._virtues: npt.NDArray[np.int32] = np.zeros(  # type: ignore
            len(Virtue), dtype=np.int32
        )

        if overrides:
            for trait, value in overrides.items():
                self[Virtue[trait]] = value

    def compatibility(self, other: Virtues) -> int:
        """Calculates the similarity between two Virtue components

        Parameters
        ----------
        other : Virtues
            The other set of virtues to compare to

        Returns
        -------
        int
            Similarity score on the range [-100, 100]
        """
        # Cosine similarity is a value between -1 and 1
        norm_product: float = float(
            np.linalg.norm(self._virtues) * np.linalg.norm(other._virtues)  # type: ignore
        )

        if norm_product == 0:
            cosine_similarity = 0.0
        else:
            cosine_similarity = float(np.dot(self._virtues, other._virtues) / norm_product)  # type: ignore

        # Distance similarity is a value between -1 and 1
        max_distance = 509.9019513592785
        distance = float(np.linalg.norm(self._virtues - other._virtues))  # type: ignore
        distance_similarity = 2.0 * (1.0 - (distance / max_distance)) - 1.0

        similarity: int = round(100 * ((cosine_similarity + distance_similarity) / 2.0))

        return similarity

    def get_high_values(self, n: int = 3) -> List[Virtue]:
        """Return the virtues names associated with the n-highest values"""
        sorted_index_array = np.argsort(self._virtues)[-n:]  # type: ignore

        value_names = list(Virtue)

        return [value_names[i] for i in sorted_index_array]

    def get_low_values(self, n: int = 3) -> List[Virtue]:
        """Return the virtues names associated with the n-lowest values"""
        sorted_index_array = np.argsort(self._virtues)[:n]  # type: ignore

        value_names = list(Virtue)

        return [value_names[i] for i in sorted_index_array]

    def __getitem__(self, item: int) -> int:
        return int(self._virtues[item])

    def __setitem__(self, item: int, value: int) -> None:
        self._virtues[item] = max(Virtues.VIRTUE_MIN, min(Virtues.VIRTUE_MAX, value))

    def __str__(self) -> str:
        return str(self.to_dict())

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._virtues.__repr__())

    def __iter__(self) -> Iterator[Tuple[Virtue, int]]:
        virtue_dict = {
            virtue: int(self._virtues[i]) for i, virtue in enumerate(list(Virtue))
        }

        return virtue_dict.items().__iter__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            **{
                virtue.name: int(self._virtues[i])
                for i, virtue in enumerate(list(Virtue))
            },
        }


class Pregnant(StatusComponent):
    """
    Pregnant characters give birth to new child characters after the due_date

    Attributes
    ----------
    partner_id: int
        The GameObject ID of the character that impregnated this character
    due_date: SimDateTime
        The date that the baby is due
    """

    __slots__ = "partner_id", "due_date"

    def __init__(self, partner_id: int, due_date: SimDateTime) -> None:
        super().__init__()
        self.partner_id: int = partner_id
        self.due_date: SimDateTime = due_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "partner_id": self.partner_id,
            "due_date": self.due_date.to_iso_str(),
        }


class ParentOf(RelationshipStatus):
    pass


class ChildOf(RelationshipStatus):
    pass


class SiblingOf(RelationshipStatus):
    pass


class Married(RelationshipStatus):
    """Tags two characters as being married"""

    __slots__ = "years"

    def __init__(self, years: float = 0.0) -> None:
        super().__init__()
        self.years: float = years

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "years": self.years}


class Dating(RelationshipStatus):
    """Tags two characters as dating"""

    __slots__ = "years"

    def __init__(self, years: float = 0.0) -> None:
        super().__init__()
        self.years: float = years

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "years": self.years}


@dataclasses.dataclass()
class MarriageConfig(Component):
    spouse_prefabs: List[str] = dataclasses.field(default_factory=list)
    chance_spawn_with_spouse: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chance_spawn_with_spouse": self.chance_spawn_with_spouse,
            "spouse_prefabs": self.spouse_prefabs,
        }


@dataclasses.dataclass()
class AgingConfig(Component):
    adolescent_age: int
    young_adult_age: int
    adult_age: int
    senior_age: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adolescent_age": self.adolescent_age,
            "young_adult_age": self.young_adult_age,
            "adult_age": self.adult_age,
            "senior_age": self.senior_age,
        }


@dataclasses.dataclass()
class ReproductionConfig(Component):
    max_children_at_spawn: int = 3
    child_prefabs: List[str] = dataclasses.field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_children_at_spawn": self.max_children_at_spawn,
            "child_prefabs": self.child_prefabs,
        }


class Gender(TraitComponent, ABC):

    _value: int

    def __int__(self) -> int:
        return self.value()

    @classmethod
    def value(cls) -> int:
        return cls._value

    def __eq__(self, other: Union[object, Type[Gender]]) -> bool:
        if isinstance(other, Gender):
            return type(self) == type(other)
        if isclass(other) and issubclass(other, Gender):
            return type(self) == other
        raise TypeError(f"Expected type of Gender, but was {other}")


class Male(Gender):
    pass


class Female(Gender):
    pass


class NonBinary(Gender):
    pass


class LifeStage(StatusComponent, ABC):

    is_persistent = True
    _value: int

    def __int__(self) -> int:
        return self.value()

    @classmethod
    def value(cls) -> int:
        return cls._value

    def __eq__(self, other: Union[object, int, Type[LifeStage]]) -> bool:
        if isinstance(other, int):
            return self.value() == other
        if isinstance(other, LifeStage):
            return self.value() == other.value()
        if isclass(other) and issubclass(other, LifeStage):
            return self.value() == other.value()
        raise TypeError(f"Expected type of LifeStage or int, but was {other}")

    def __ge__(self, other: Union[object, int, Type[LifeStage]]) -> bool:
        if isinstance(other, int):
            return self.value() >= other
        if isinstance(other, LifeStage):
            return self.value() >= other.value()
        if isclass(other) and issubclass(other, LifeStage):
            return self.value() >= other.value()
        raise TypeError(f"Expected type of LifeStage or int, but was {other}")

    def __le__(self, other: Union[object, int, Type[LifeStage]]) -> bool:
        if isinstance(other, int):
            return self.value() <= other
        if isinstance(other, LifeStage):
            return self.value() <= other.value()
        if isclass(other) and issubclass(other, LifeStage):
            return self.value() <= other.value()
        raise TypeError(f"Expected type of LifeStage or int, but was {other}")

    def __gt__(self, other: Union[object, int, Type[LifeStage]]) -> bool:
        if isinstance(other, int):
            return self.value() > other
        if isinstance(other, LifeStage):
            return self.value() > other.value()
        if isclass(other) and issubclass(other, LifeStage):
            return self.value() > other.value()
        raise TypeError(f"Expected type of LifeStage ot int, but was {other}")

    def __lt__(self, other: Union[object, int, Type[LifeStage]]) -> bool:
        if isinstance(other, int):
            return self.value() < other
        if isinstance(other, LifeStage):
            return self.value() < other.value()
        if isclass(other) and issubclass(other, LifeStage):
            return self.value() < other.value()
        raise TypeError(f"Expected type of LifeStage or int, but was {other}")


class Child(LifeStage):

    _value = 0


class Adolescent(LifeStage):
    _value = 1


class YoungAdult(LifeStage):
    _value = 2


class Adult(LifeStage):
    _value = 3


class Senior(LifeStage):
    _value = 4
