"""Components for representing Characters.

"""

from __future__ import annotations

import enum
from typing import Any

from neighborly.components.traits import Trait
from neighborly.datetime import SimDate
from neighborly.ecs import Component, GameObject


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


class Species(Component):
    """Configuration information about a character's species."""

    __slots__ = (
        "adolescent_age",
        "young_adult_age",
        "adult_age",
        "senior_age",
        "lifespan",
        "can_physically_age",
    )

    def __init__(
        self,
        adolescent_age: int,
        young_adult_age: int,
        adult_age: int,
        senior_age: int,
        lifespan: int,
        can_physically_age: bool,
    ) -> None:
        super().__init__()
        self.adolescent_age = adolescent_age
        self.young_adult_age = young_adult_age
        self.adult_age = adult_age
        self.senior_age = senior_age
        self.lifespan = lifespan
        self.can_physically_age = can_physically_age

    def to_dict(self) -> dict[str, Any]:
        return {}


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
    species: GameObject
    """The character's species"""

    def __init__(
        self, first_name: str, last_name: str, sex: Sex, species: GameObject
    ) -> None:
        super().__init__()
        self._first_name = first_name
        self._last_name = last_name
        self._sex = sex
        self._age = 0
        self._life_stage = LifeStage.CHILD
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

        if self._first_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.first_name!{self._first_name}"
            )

    @property
    def last_name(self) -> str:
        """The character's last name."""
        return self._last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        """Set the character's last name."""
        self._last_name = value
        self.gameobject.name = self.full_name

        if self._last_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.last_name!{self._last_name}"
            )

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self._first_name} {self._last_name}"

    @property
    def age(self) -> float:
        """Get the character's age."""
        return self._age

    @age.setter
    def age(self, value: float) -> None:
        """Set the character's age."""
        self._age = value

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.character.age")

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.age!{self.age}"
        )

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

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.life_stage!{self._life_stage.name}"
        )

    def on_add(self) -> None:
        if self.first_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.first_name!{self.first_name}"
            )
        if self.last_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.last_name!{self.last_name}"
            )

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.sex!{self.sex.name}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.age!{self.age}"
        )
        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.life_stage!{self.life_stage.name}"
        )

        if self.species:
            species_id = self.species.get_component(Trait).definition_id
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.species!{species_id}"
            )

    def on_remove(self) -> None:
        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.character")

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self._first_name,
            "last_name": self._last_name,
            "sex": self.sex.name,
            "age": int(self.age),
            "life_stage": self.life_stage.name,
            "species": self.species.get_component(Trait).definition_id,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(name={self.full_name}, sex={self.sex}, "
            f"age={self.age}({self.life_stage}), species={self.species.name})"
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

    def on_add(self) -> None:
        if self.partner:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.pregnant.partner!{self.partner.uid}"
            )
        if self.due_date:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.pregnant.due_date!{self.due_date}"
            )

    def on_remove(self) -> None:
        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.pregnant")

    def __str__(self) -> str:
        return f"{type(self).__name__}(partner={self.partner.name})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}(partner={self.partner.name})"

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "partner": self.partner.uid,
            "due_date": str(self.due_date),
        }
