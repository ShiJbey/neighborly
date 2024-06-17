"""Default implementations of preconditions.

"""

import enum
from typing import Any

from neighborly.components.character import Character, LifeStage, Sex
from neighborly.components.relationship import Relationship
from neighborly.ecs import GameObject, World
from neighborly.helpers.skills import get_skill, has_skill
from neighborly.helpers.stats import get_stat, has_stat
from neighborly.helpers.traits import has_trait
from neighborly.preconditions.base_types import Precondition


class HasTrait(Precondition):
    """A precondition that check if a GameObject has a given trait."""

    __precondition_name__ = "HasTrait"

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject, self.trait)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait=trait)


class OwnerHasTrait(Precondition):
    """A precondition that check if a relationship's owner has a given trait."""

    __precondition_name__ = "OwnerHasTrait"

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires relationship owner to have a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject.get_component(Relationship).owner, self.trait)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait=trait)


class TargetHasTrait(Precondition):
    """A precondition that check if a relationship's target has a given trait."""

    __precondition_name__ = "TargetHasTrait"

    __slots__ = ("trait",)

    trait: str
    """The ID of the trait to check for."""

    def __init__(
        self,
        trait: str,
    ) -> None:
        super().__init__()
        self.trait = trait

    @property
    def description(self) -> str:
        return f"requires relationship target to have a(n) {self.trait!r} trait"

    def check(self, gameobject: GameObject) -> bool:
        return has_trait(gameobject.get_component(Relationship).target, self.trait)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait=trait)


class AreSameSex(Precondition):
    """Checks if the owner and target of a relationship belong to the dame sex."""

    __precondition_name__ = "AreSameSex"

    def __init__(self) -> None:
        super().__init__()

    @property
    def description(self) -> str:
        return f"owner and target of the relationship are the same sex"

    def check(self, gameobject: GameObject) -> bool:
        relationship = gameobject.get_component(Relationship)

        owner_sex = relationship.owner.get_component(Character).sex
        target_sex = relationship.target.get_component(Character).sex

        return owner_sex == target_sex

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        return cls()


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

    __slots__ = ("skill_id", "skill_level", "comparator")

    skill_id: str
    """The ID of the skill to check for."""
    skill_level: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(self, skill: str, level: float, comparator: ComparatorOp) -> None:
        super().__init__()
        self.skill_id = skill
        self.skill_level = level
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.skill_id} skill level of {self.comparator}"
            f" {self.skill_level}."
        )

    def check(self, gameobject: GameObject) -> bool:
        if has_skill(gameobject, self.skill_id):
            skill_instance = get_skill(gameobject, self.skill_id)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(skill=skill, level=level, comparator=comparator)


class OwnerSkillRequirement(Precondition):
    """Checks a relationship owner has a certain level skill."""

    __precondition_name__ = "OwnerSkillRequirement"

    __slots__ = ("skill_id", "skill_level", "comparator")

    skill_id: str
    """The ID of the skill to check for."""
    skill_level: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(self, skill: str, level: float, comparator: ComparatorOp) -> None:
        super().__init__()
        self.skill_id = skill
        self.skill_level = level
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.skill_id} skill level of {self.comparator}"
            f" {self.skill_level}."
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).owner

        if has_skill(character, self.skill_id):
            skill_instance = get_skill(character, self.skill_id)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(skill=skill, level=level, comparator=comparator)


class TargetSkillRequirement(Precondition):
    """Checks a relationship target has a certain level skill."""

    __precondition_name__ = "TargetSkillRequirement"

    __slots__ = ("skill_id", "skill_level", "comparator")

    skill_id: str
    """The ID of the skill to check for."""
    skill_level: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(self, skill: str, level: float, comparator: ComparatorOp) -> None:
        super().__init__()
        self.skill_id = skill
        self.skill_level = level
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.skill_id} skill level of {self.comparator}"
            f" {self.skill_level}."
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).target

        if has_skill(character, self.skill_id):
            skill_instance = get_skill(character, self.skill_id)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(skill=skill, level=level, comparator=comparator)


class StatRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain stat value."""

    __precondition_name__ = "StatRequirement"

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:

        if has_stat(gameobject, self.stat_name):
            stat = get_stat(gameobject, self.stat_name)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class OwnerStatRequirement(Precondition):
    """Check a relationship owner has a certain stat value."""

    __precondition_name__ = "OwnerStatRequirement"

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).owner

        if has_stat(character, self.stat_name):
            stat = get_stat(character, self.stat_name)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class TargetStatRequirement(Precondition):
    """Check a relationship target has a certain stat value."""

    __precondition_name__ = "TargetStatRequirement"

    __slots__ = ("stat_name", "required_value", "comparator")

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for."""
    comparator: ComparatorOp
    """Comparison for the skill level."""

    def __init__(
        self,
        stat: str,
        required_value: float,
        comparator: ComparatorOp,
    ) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value
        self.comparator = comparator

    @property
    def description(self) -> str:
        return (
            f"requires a(n) {self.stat_name} stat value of {self.comparator}"
            f" {self.required_value}"
        )

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).target

        if has_stat(character, self.stat_name):
            stat = get_stat(character, self.stat_name)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(
            stat=stat,
            required_value=value,
            comparator=comparator,
        )


class LifeStageRequirement(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __precondition_name__ = "LifeStageRequirement"

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Character)

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
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(life_stage=life_stage, comparator=comparator)


class OwnerLifeStageRequirement(Precondition):
    """A precondition that requires a relationship owner to be a given life stage."""

    __precondition_name__ = "OwnerLifeStageRequirement"

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).owner.get_component(
            Character
        )

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

        else:
            return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(life_stage=life_stage, comparator=comparator)


class TargetLifeStageRequirement(Precondition):
    """A precondition that requires a relationship target to be a given life stage."""

    __precondition_name__ = "TargetLifeStageRequirement"

    __slots__ = ("life_stage", "comparator")

    life_stage: LifeStage
    """The life stage to check for."""
    comparator: ComparatorOp
    """Comparison for the life stage."""

    def __init__(self, life_stage: LifeStage, comparator: ComparatorOp) -> None:
        super().__init__()
        self.life_stage = life_stage
        self.comparator = comparator

    @property
    def description(self) -> str:
        return f"requires a life stage {self.comparator} {self.life_stage.name}"

    def check(self, gameobject: GameObject) -> bool:
        character = gameobject.get_component(Relationship).target.get_component(
            Character
        )

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

        else:
            return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        comparator = ComparatorOp[params.get("op", "gte").upper()]
        return cls(life_stage=life_stage, comparator=comparator)


class IsSex(Precondition):
    """A precondition that requires a character to belong to given sex."""

    __precondition_name__ = "IsSex"

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Character must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return gameobject.get_component(Character).sex == self.sex

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return cls(sex=sex)


class OwnerIsSex(Precondition):
    """A precondition that requires a relationship owner to belong to given sex."""

    __precondition_name__ = "OwnerIsSex"

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Relationship owner must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return (
            gameobject.get_component(Relationship).owner.get_component(Character).sex
            == self.sex
        )

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return cls(sex=sex)


class TargetIsSex(Precondition):
    """A precondition that requires a relationship target to belong to given sex."""

    __precondition_name__ = "TargetIsSex"

    __slots__ = ("sex",)

    sex: Sex

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"Relationship target must be of the {self.sex.name} sex"

    def check(self, gameobject: GameObject) -> bool:
        return (
            gameobject.get_component(Relationship).target.get_component(Character).sex
            == self.sex
        )

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"].upper()]
        return cls(sex=sex)
