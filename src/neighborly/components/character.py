"""Components for representing Characters.

"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy.orm import Mapped, mapped_column

from neighborly.datetime import SimDate
from neighborly.defs.base_types import SpeciesDef
from neighborly.ecs import Component, GameData, GameObject


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

    __slots__ = ("definition",)

    definition: SpeciesDef
    """The definition data for this species"""

    def __init__(self, gameobject: GameObject, definition: SpeciesDef) -> None:
        super().__init__(gameobject)
        self.definition = definition

    @property
    def definition_id(self) -> str:
        """The definition ID of this species."""
        return self.definition.definition_id

    def __str__(self) -> str:
        return f"Species(definition_id={self.definition.definition_id!r})"

    def __repr__(self) -> str:
        return f"Species(definition_id={self.definition.definition_id!r})"

    def to_dict(self) -> dict[str, Any]:
        return {"definition_id": self.definition.definition_id}


class CharacterData(GameData):
    """Data associated with a character component."""

    __tablename__ = "characters"

    uid: Mapped[int] = mapped_column(primary_key=True, unique=True)
    first_name: Mapped[str] = mapped_column(default="")
    last_name: Mapped[str] = mapped_column(default="")
    age: Mapped[float] = mapped_column(default=0)
    sex: Mapped[Sex] = mapped_column(default=Sex.NOT_SPECIFIED)
    life_stage: Mapped[LifeStage] = mapped_column(default=LifeStage.CHILD)
    species: Mapped[int]


class Character(Component):
    """A character within the story world."""

    __slots__ = (
        "data",
        "species",
    )

    data: CharacterData
    """SQL queryable component data."""
    species: GameObject
    """The character's species"""

    def __init__(
        self,
        gameobject: GameObject,
        first_name: str,
        last_name: str,
        sex: Sex,
        species: GameObject,
    ) -> None:
        super().__init__(gameobject)
        self.data = CharacterData(
            uid=gameobject.uid,
            first_name=first_name,
            last_name=last_name,
            age=0,
            sex=sex,
            species=species.uid,
            life_stage=LifeStage.CHILD,
        )
        self.species = species

    @property
    def first_name(self) -> str:
        """The character's first name."""
        return self.data.first_name

    @first_name.setter
    def first_name(self, value: str) -> None:
        """Set the character's first name."""

        with self.gameobject.world.session.begin() as session:
            self.data.first_name = value
            session.add(self.data)

        self.gameobject.name = self.full_name

        if self.data.first_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.first_name!{self.data.first_name}"
            )

    @property
    def last_name(self) -> str:
        """The character's last name."""
        return self.data.last_name

    @last_name.setter
    def last_name(self, value: str) -> None:
        """Set the character's last name."""

        with self.gameobject.world.session.begin() as session:
            self.data.last_name = value
            session.add(self.data)

        self.gameobject.name = self.full_name

        if self.data.last_name:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.last_name!{self.data.last_name}"
            )

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.data.last_name}"

    @property
    def age(self) -> float:
        """Get the character's age."""
        return self.data.age

    @age.setter
    def age(self, value: float) -> None:
        """Set the character's age."""

        with self.gameobject.world.session.begin() as session:
            self.data.age = value
            session.add(self.data)

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.character.age")

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.age!{self.age}"
        )

    @property
    def sex(self) -> Sex:
        """Get the characters sex."""
        return self.data.sex

    @property
    def life_stage(self) -> LifeStage:
        """Get the character's life stage."""
        return self.data.life_stage

    @life_stage.setter
    def life_stage(self, value: LifeStage) -> None:
        """Set the character's life stage."""

        with self.gameobject.world.session.begin() as session:
            self.data.life_stage = value
            session.add(self.data)

        self.gameobject.world.rp_db.insert(
            f"{self.gameobject.uid}.character.life_stage!{self.data.life_stage.name}"
        )

    def on_add(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.add(self.data)

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
            species_id = self.species.get_component(Species).definition_id
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.character.species!{species_id}"
            )

    def on_remove(self) -> None:
        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.character")

        with self.gameobject.world.session.begin() as session:
            session.delete(self.data)

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "sex": self.sex.name,
            "age": int(self.age),
            "life_stage": self.life_stage.name,
            "species": self.species.get_component(Species).definition_id,
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

    def __init__(
        self, gameobject: GameObject, partner: GameObject, due_date: SimDate
    ) -> None:
        super().__init__(gameobject)
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
