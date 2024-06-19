"""Components for representing Characters.

"""

from __future__ import annotations

import enum
from typing import Any, Optional

import attrs

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


@attrs.define
class SpeciesType:
    """Configuration information about a character's species."""

    definition_id: str
    """The unique ID of this species definition."""
    name: str
    """The name of this species."""
    description: str
    """A short text description."""
    adolescent_age: int
    """The age when this species is considered an adolescent."""
    young_adult_age: int
    """The age when this species is considered a young adult."""
    adult_age: int
    """The age when this species is considered an adult."""
    senior_age: int
    """The age when this species is considered a senior."""
    lifespan: tuple[int, int]
    """A lifespan interval for characters of this species."""
    can_physically_age: bool
    """Can characters of this species age."""
    traits: list[str]
    """IDs of traits characters of this species get at creation."""
    adolescent_male_fertility: int
    """Max fertility for adolescent males."""
    young_adult_male_fertility: int
    """Max fertility for young adult males."""
    adult_male_fertility: int
    """Max fertility for adult males."""
    senior_male_fertility: int
    """Max fertility for senior males."""
    adolescent_female_fertility: int
    """Max fertility for adolescent females."""
    young_adult_female_fertility: int
    """Max fertility for young adult females."""
    adult_female_fertility: int
    """Max fertility for adult females."""
    senior_female_fertility: int
    """Max fertility for senior females."""
    fertility_cost_per_child: int
    """Fertility reduction each time a character births a child."""

    def get_life_stage_for_age(self, age: int) -> LifeStage:
        """Get the life stage for a character with a given species and age."""

        if age >= self.senior_age:
            return LifeStage.SENIOR
        elif age >= self.adult_age:
            return LifeStage.ADULT
        elif age >= self.young_adult_age:
            return LifeStage.YOUNG_ADULT
        elif age >= self.adolescent_age:
            return LifeStage.ADOLESCENT

        return LifeStage.CHILD


class Character(Component):
    """A character within the story world."""

    __slots__ = ("first_name", "last_name", "sex", "life_stage")

    first_name: str
    """The character's first name."""
    last_name: str
    """The character's last name or family name."""
    sex: Sex
    """The physical sex of the character."""
    life_stage: LifeStage
    """The character's current life stage."""

    def __init__(
        self,
        first_name: str,
        last_name: str,
        sex: Sex,
    ) -> None:
        super().__init__()
        self.first_name = first_name
        self.last_name = last_name
        self.sex = sex
        self.life_stage = LifeStage.CHILD

    @property
    def full_name(self) -> str:
        """The combined full name of the character."""
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "sex": self.sex.name,
            "life_stage": self.life_stage.name,
        }

    def __repr__(self) -> str:
        return (
            f"Character(name={self.full_name!r}, sex={self.sex!r}, "
            f"life_stage={self.life_stage!r})"
        )

    def __str__(self) -> str:
        return self.full_name


class Species(Component):
    """Tracks the species a character belongs to."""

    __slots__ = ("species",)

    species: SpeciesType
    """The species the character belongs to."""

    def __init__(self, species: SpeciesType) -> None:
        super().__init__()
        self.species = species

    def to_dict(self) -> dict[str, Any]:
        return {"species": self.species.definition_id}


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


class Household(Component):
    """A collection of characters that all live together."""

    __slots__ = ("head", "members")

    head: Optional[GameObject]
    """The head of the household."""
    members: list[GameObject]
    """Other members of the household."""

    def __init__(self) -> None:
        super().__init__()
        self.head = None
        self.members = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "head": self.head.uid if self.head is not None else -1,
            "members": [m.uid for m in self.members],
        }


class MemberOfHousehold(Component):
    """Marks a GameObject as being a member of a household."""

    __slots__ = ("household",)

    household: GameObject
    """The household they belong to."""

    def __init__(self, household: GameObject) -> None:
        super().__init__()
        self.household = household

    def to_dict(self) -> dict[str, Any]:
        return {"household": self.household.uid}


class HeadOfHousehold(Component):
    """Marks a character as being the head of a household."""

    __slots__ = ("household",)

    household: GameObject
    """The household they are the head of."""

    def __init__(self, household: GameObject) -> None:
        super().__init__()
        self.household = household

    def to_dict(self) -> dict[str, Any]:
        return {"household": self.household.uid}


class ResidentOf(Component):
    """A Component attached to characters that tracks where they live."""

    __slots__ = ("settlement",)

    settlement: GameObject
    """The settlement they live in."""

    def __init__(self, settlement: GameObject) -> None:
        super().__init__()
        self.settlement = settlement

    def to_dict(self) -> dict[str, Any]:
        return {"settlement": self.settlement.uid}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(settlement={self.settlement.name!r})"

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(settlement={self.settlement.name!r})"
