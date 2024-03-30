"""Components for representing Characters.

"""

from __future__ import annotations

import enum
from typing import Any

from sqlalchemy import ForeignKey, delete
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


class CharacterData(GameData):
    """Data associated with a character component."""

    __tablename__ = "characters"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    first_name: Mapped[str] = mapped_column(default="")
    last_name: Mapped[str] = mapped_column(default="")
    sex: Mapped[Sex] = mapped_column(default=Sex.NOT_SPECIFIED)
    life_stage: Mapped[LifeStage] = mapped_column(default=LifeStage.CHILD)
    species: Mapped[str]


class Character(Component):
    """A character within the story world."""

    __slots__ = (
        "data",
        "species",
    )

    data: CharacterData
    """SQL queryable component data."""
    species: SpeciesDef
    """The character's species"""

    def __init__(
        self,
        gameobject: GameObject,
        first_name: str,
        last_name: str,
        sex: Sex,
        species: SpeciesDef,
    ) -> None:
        super().__init__(gameobject)
        self.data = CharacterData(
            uid=gameobject.uid,
            first_name=first_name,
            last_name=last_name,
            sex=sex,
            species=species.definition_id,
            life_stage=LifeStage.CHILD,
        )
        self.species = species
        gameobject.name = self.full_name

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
            f"{self.gameobject.uid}.character.life_stage!{self.life_stage.name}"
        )

        if self.species:
            species_id = self.species.definition_id
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


class PregnancyData(GameData):
    """SQL Queryable data about a pregnancy."""

    __tablename__ = "pregnancy"

    uid: Mapped[int] = mapped_column(
        ForeignKey("gameobjects.uid"), primary_key=True, unique=True
    )
    first_name: Mapped[int] = mapped_column(ForeignKey("gameobjects.uid"))
    due_date: Mapped[str]


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
        with self.gameobject.world.session.begin() as session:
            session.add(
                PregnancyData(
                    uid=self.gameobject.uid,
                    partner_id=self.partner.uid,
                    due_date=self.due_date.to_iso_str(),
                )
            )

        if self.partner:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.pregnant.partner!{self.partner.uid}"
            )
        if self.due_date:
            self.gameobject.world.rp_db.insert(
                f"{self.gameobject.uid}.pregnant.due_date!{self.due_date}"
            )

    def on_remove(self) -> None:
        with self.gameobject.world.session.begin() as session:
            session.execute(
                delete(PregnancyData).where(PregnancyData.uid == self.gameobject.uid)
            )

        self.gameobject.world.rp_db.delete(f"{self.gameobject.uid}.pregnant")

    def __str__(self) -> str:
        return f"Pregnant(partner={self.partner.name!r}, due_date={self.due_date})"

    def __repr__(self) -> str:
        return f"Pregnant(partner={self.partner.name!r}, due_date={self.due_date})"

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner": self.partner.uid,
            "due_date": str(self.due_date),
        }
