"""Default implementations of preconditions.

"""

from typing import Any

from neighborly.components.character import Character, LifeStage, Sex
from neighborly.components.relationship import Relationship
from neighborly.ecs import GameObject, World
from neighborly.helpers.skills import get_skill, has_skill
from neighborly.helpers.traits import has_trait
from neighborly.preconditions.base_types import Precondition


class HasTrait(Precondition):
    """A precondition that check if a GameObject has a given trait."""

    __slots__ = ("trait_id",)

    trait_id: str
    """The ID of the trait to check for."""

    def __init__(self, trait: str) -> None:
        super().__init__()
        self.trait_id = trait

    @property
    def description(self) -> str:
        return f"has the trait {self.trait_id}"

    def __call__(self, target: GameObject) -> bool:
        return has_trait(target, self.trait_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait)


class TargetHasTrait(Precondition):
    """A precondition that checks if a relationship's target has a given trait."""

    __slots__ = ("trait_id",)

    trait_id: str
    """The ID of the trait to check for."""

    def __init__(self, trait: str) -> None:
        super().__init__()
        self.trait_id = trait

    @property
    def description(self) -> str:
        return f"relationship target has the {self.trait_id} trait"

    def __call__(self, target: GameObject) -> bool:
        return has_trait(target.get_component(Relationship).target, self.trait_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait)


class SkillRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain level skill."""

    __slots__ = "skill_id", "skill_level"

    skill_id: str
    """The ID of the skill to check for."""
    skill_level: float
    """The skill level to check for"""

    def __init__(self, skill: str, level: float = 0.0) -> None:
        super().__init__()
        self.skill_id = skill
        self.skill_level = level

    @property
    def description(self) -> str:
        return f"has {self.skill_id} skill  level of at least {self.skill_level}"

    def __call__(self, target: GameObject) -> bool:
        if has_skill(target, self.skill_id):
            skill_stat = get_skill(target, self.skill_id)
            return skill_stat.value >= self.skill_level

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        skill = params["skill"]
        level = params["level"]

        return cls(skill=skill, level=level)


class AtLeastLifeStage(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __slots__ = ("life_stage",)

    life_stage: LifeStage
    """The life stage to check for."""

    def __init__(self, life_stage: LifeStage) -> None:
        super().__init__()
        self.life_stage = life_stage

    @property
    def description(self) -> str:
        return f"is at least the {self.life_stage.name} life stage"

    def __call__(self, target: GameObject) -> bool:
        if character := target.try_component(Character):
            return character.life_stage >= self.life_stage

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]

        return cls(life_stage)


class TargetIsSex(Precondition):
    """Requires that the target of the relationship be of a specific sex."""

    __slots__ = ("sex",)

    sex: Sex
    """The sex to check for."""

    def __init__(self, sex: Sex) -> None:
        super().__init__()
        self.sex = sex

    @property
    def description(self) -> str:
        return f"relationship target is a {self.sex.name}"

    def __call__(self, target: GameObject) -> bool:
        relationship_target = target.get_component(Relationship).target
        return relationship_target.get_component(Character).sex == self.sex

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        sex = Sex[params["sex"]]
        return cls(sex)


class TargetLifeStageLT(Precondition):
    """Requires that the target of the relationship be less than a given life stage."""

    __slots__ = ("life_stage",)

    life_stage: LifeStage
    """The life stage to check for."""

    def __init__(self, life_stage: LifeStage) -> None:
        super().__init__()
        self.life_stage = life_stage

    @property
    def description(self) -> str:
        return f"relationship target is at least the {self.life_stage.name} life stage"

    def __call__(self, target: GameObject) -> bool:
        relationship_target = target.get_component(Relationship).target
        return relationship_target.get_component(Character).life_stage < self.life_stage

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]
        return cls(life_stage)
