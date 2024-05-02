"""Components for representing Characters.

"""

from __future__ import annotations

import enum
from typing import Any, Iterable

from neighborly.components.traits import Trait, TraitType
from neighborly.datetime import SimDate
from neighborly.defs.base_types import SpeciesDef
from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect


class LifeStage(enum.IntEnum):
    """An enumeration of all the various life stages aging characters pass through."""

    CHILD = 0
    ADOLESCENT = 1
    YOUNG_ADULT = 2
    ADULT = 3
    SENIOR = 4


class Sex(enum.IntEnum):
    """The characters current sex."""

    MALE = enum.auto()
    FEMALE = enum.auto()
    NOT_SPECIFIED = enum.auto()


class Species(Trait):
    """Configuration information about a character's species."""

    __slots__ = (
        "adolescent_age",
        "young_adult_age",
        "adult_age",
        "senior_age",
        "lifespan",
        "can_physically_age",
    )

    definition_id: str
    adolescent_age: int
    young_adult_age: int
    adult_age: int
    senior_age: int
    lifespan: str
    can_physically_age: bool

    def __init__(
        self,
        definition_id: str,
        name: str,
        description: str,
        effects: list[Effect],
        conflicting_traits: Iterable[str],
        adolescent_age: int,
        young_adult_age: int,
        adult_age: int,
        senior_age: int,
        lifespan: str,
        can_physically_age: bool,
    ) -> None:
        super().__init__(
            definition_id=definition_id,
            name=name,
            trait_type=TraitType.AGENT,
            description=description,
            effects=effects,
            conflicting_traits=conflicting_traits,
            target_effects=[],
            owner_effects=[],
            outgoing_relationship_effects=[],
            incoming_relationship_effects=[],
        )
        self.adolescent_age = adolescent_age
        self.young_adult_age = young_adult_age
        self.adult_age = adult_age
        self.senior_age = senior_age
        self.lifespan = lifespan
        self.can_physically_age = can_physically_age


class Character(Component):
    """A character within the story world."""

    __slots__ = ("_first_name", "_last_name", "_sex", "_age", "_life_stage", "species")

    _first_name: str
    """The character's first name."""
    _last_name: str
    """The character's last name or family name."""
    _age: float
    """the character's current age."""
    _sex: Sex
    """The physical sex of the character."""
    _life_stage: LifeStage
    """The character's current life stage."""
    species: SpeciesDef
    """The character's species"""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        sex: Sex,
        species: SpeciesDef,
    ) -> None:
        super().__init__()
        self._first_name = first_name
        self._last_name = last_name
        self._sex = sex
        self._age = 0
        self._life_stage = LifeStage.CHILD
        self.species = species
        self.species = species

    @property
    def first_name(self) -> str:
        """The character's first name."""
        return self._first_name

    @first_name.setter
    def first_name(self, value: str) -> None:
        """Set the character's first name."""

        self._first_name = value

        self.gameobject.name = self.full_name

    @property
    def last_name(self) -> str:
        """The character's last name."""
        return self._last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        """Set the character's last name."""
        self._last_name = value

        self.gameobject.name = self.full_name

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self._first_name} {self._last_name}"

    @property
    def sex(self) -> Sex:
        """Get the characters sex."""
        return self._sex

    @property
    def life_stage(self) -> LifeStage:
        """Get the character's life stage."""
        return self._life_stage

    @life_stage.setter
    def life_stage(self, value: LifeStage) -> None:
        """Set the character's life stage."""

        self._life_stage = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "sex": self.sex.name,
            "life_stage": self.life_stage.name,
            "species": self.species.definition_id,
        }

    def __repr__(self) -> str:
        return (
            f"Character(name={self.full_name!r}, sex={self.sex!r}, "
            f"life_stage={self.life_stage!r}, species={self.species.name!r})"
        )

    def __str__(self) -> str:
        return self.full_name


class Pregnant(Component):
    """Tags a character as pregnant and tracks relevant information."""

    __slots__ = "partner", "due_date"

    partner: GameObject
    """The GameObject ID of the character that impregnated this character."""
    due_date: SimDate
    """The date the baby is due."""

    def __init__(self, partner: GameObject, due_date: SimDate) -> None:
        super().__init__()
        self.partner = partner
        self.due_date = due_date.copy()

    def __str__(self) -> str:
        return f"Pregnant(partner={self.partner.name!r}, due_date={self.due_date})"

    def __repr__(self) -> str:
        return f"Pregnant(partner={self.partner.name!r}, due_date={self.due_date})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner": self.partner.uid,
            "due_date": str(self.due_date),
        }
