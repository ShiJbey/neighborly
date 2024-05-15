"""Default implementations of preconditions.

"""

import enum
from typing import Any

from neighborly.components.character import Character, LifeStage, Sex
from neighborly.ecs import GameObject, World
from neighborly.helpers.skills import get_skill, has_skill
from neighborly.helpers.stats import get_stat, has_stat
from neighborly.helpers.traits import has_trait
from neighborly.preconditions.base_types import Precondition


class HasTrait(Precondition):
    """A precondition that check if a GameObject has a given trait."""

    __precondition_name__ = "HasTrait"

    __slots__ = (
        "target_key",
        "trait_id",
    )

    target_key: str
    """The blackboard key of the target of this precondition"""
    trait_id: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        target_key: str,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait_id = trait
        self.target_key = target_key

    @property
    def description(self) -> str:
        return f"requires a(n) {self.trait_id!r} trait"

    def check(self, blackboard: dict[str, Any]) -> bool:
        target: GameObject = blackboard[self.target_key]

        return has_trait(target, self.trait_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        target_key = params.get("target", "target")
        return cls(target_key=target_key, trait=trait)


class ComparatorOp(enum.Enum):
    """Comparator Operators."""

    EQ = enum.auto()
    """Equal to."""
    NEQ = enum.auto()
    """Not equal to."""
    LT = enum.auto()
    """Less than."""
    GT = enum.auto()
    """Greater than."""
    LTE = enum.auto()
    """Less than or equal to."""
    GTE = enum.auto()
    """Greater than or equal to."""

    def __str__(self) -> str:
        if self.value == ComparatorOp.EQ:
            return "equal to"

        elif self.value == ComparatorOp.NEQ:
            return "not equal to"

        elif self.value == ComparatorOp.LT:
            return "less than"

        elif self.value == ComparatorOp.GT:
            return "greater than"

        elif self.value == ComparatorOp.LTE:
            return "less than or equal to"

        elif self.value == ComparatorOp.GTE:
            return "greater than or equal to"

        else:
            return self.name


class SkillRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain level skill."""

    __precondition_name__ = "SkillRequirement"

    __slots__ = ("target_key", "skill_id", "skill_level", "comparator")

    target_key: str
    """Key of the target of this precondition in the blackboard."""
    skill_id: str
    """The ID of the skill to check for."""
    skill_level: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self, target_key: str, skill: str, level: float, comparator: ComparatorOp
    ) -> None:
        super().__init__()
        self.target_key = target_key
        self.skill_id = skill
        self.skill_level = level
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.skill_id} skill level of {self.comparator}"
            f" {self.skill_level}."
        )

    def check(self, blackboard: dict[str, Any]) -> bool:
        target: GameObject = blackboard[self.target_key]

        if has_skill(target, self.skill_id):
            skill_instance = get_skill(target, self.skill_id)

            if self.comparator == ComparatorOp.EQ:
                return skill_instance.stat.value == self.skill_level

            elif self.comparator == ComparatorOp.NEQ:
                return skill_instance.stat.value != self.skill_level

            elif self.comparator == ComparatorOp.LT:
                return skill_instance.stat.value < self.skill_level

            elif self.comparator == ComparatorOp.GT:
                return skill_instance.stat.value > self.skill_level

            elif self.comparator == ComparatorOp.LTE:
                return skill_instance.stat.value <= self.skill_level

            elif self.comparator == ComparatorOp.GTE:
                return skill_instance.stat.value >= self.skill_level

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        skill = params["skill"]
        level = params["level"]
        target_key = params.get("target", "target")
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(
            target_key=target_key, skill=skill, level=level, comparator=comparator
        )


class StatRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain stat value."""

    __precondition_name__ = "StatRequirement"

    __slots__ = ("target_key", "stat_name", "required_value", "comparator")

    target_key: str
    """Key of the target of this precondition in the blackboard."""
    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        target_key: str,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.target_key = target_key
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, blackboard: dict[str, Any]) -> bool:
        target: GameObject = blackboard[self.target_key]
        if has_stat(target, self.stat_name):
            stat = get_stat(target, self.stat_name)

            if self.comparator == ComparatorOp.EQ:
                return stat.value == self.required_value

            elif self.comparator == ComparatorOp.NEQ:
                return stat.value != self.required_value

            elif self.comparator == ComparatorOp.LT:
                return stat.value < self.required_value

            elif self.comparator == ComparatorOp.GT:
                return stat.value > self.required_value

            elif self.comparator == ComparatorOp.LTE:
                return stat.value <= self.required_value

            elif self.comparator == ComparatorOp.GTE:
                return stat.value >= self.required_value

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        stat = params["stat"]
        value = params["value"]
        target_key = params.get("target", "target")
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(
            target_key=target_key,
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class LifeStageRequirement(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __precondition_name__ = "LifeStageRequirement"

    __slots__ = ("target_key", "life_stage", "comparator")

    target_key: str
    """Key of the target of this precondition in the blackboard."""
    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(
        self, target_key: str, life_stage: LifeStage, comparator: ComparatorOp
    ) -> None:
        super().__init__()
        self.target_key = target_key
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, blackboard: dict[str, Any]) -> bool:
        target: GameObject = blackboard[self.target_key]

        if character := target.try_component(Character):
            if self.comparator == ComparatorOp.EQ:
                return character.life_stage == self.life_stage

            elif self.comparator == ComparatorOp.NEQ:
                return character.life_stage != self.life_stage

            elif self.comparator == ComparatorOp.LT:
                return character.life_stage < self.life_stage

            elif self.comparator == ComparatorOp.GT:
                return character.life_stage > self.life_stage

            elif self.comparator == ComparatorOp.LTE:
                return character.life_stage <= self.life_stage

            elif self.comparator == ComparatorOp.GTE:
                return character.life_stage >= self.life_stage

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        target_key = params.get("target", "target")
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(target_key=target_key, life_stage=life_stage, comparator=comparator)


class GenderRequirement(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __precondition_name__ = "GenderRequirement"

    __slots__ = ("target_key", "gender")

    target_key: str
    """Key of the target of this precondition in the blackboard."""
    gender: Sex
    """The gender to check for."""

    def __init__(self, target_key: str, gender: Sex) -> None:
        super().__init__()
        self.target_key = target_key
        self.gender = gender

    @property
    def description(self) -> str:
        return f"requires a gender of {self.gender.name}"

    def check(self, blackboard: dict[str, Any]) -> bool:
        target: GameObject = blackboard[self.target_key]

        if character := target.try_component(Character):
            return character.sex == self.gender

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        gender = Sex[params["gender"].upper()]
        target_key = params.get("target", "target")
        return cls(target_key=target_key, gender=gender)
