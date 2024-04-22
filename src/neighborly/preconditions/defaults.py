"""Default implementations of preconditions.

"""

from typing import Any

from repraxis.query import DBQuery

from neighborly.components.character import Character, LifeStage
from neighborly.components.relationship import Relationship
from neighborly.ecs import GameObject, World
from neighborly.helpers.db_helpers import preprocess_query_string
from neighborly.helpers.skills import get_skill, has_skill
from neighborly.helpers.stats import get_stat, has_stat
from neighborly.helpers.traits import has_trait
from neighborly.preconditions.base_types import Precondition


class HasTrait(Precondition):
    """A precondition that check if a GameObject has a given trait."""

    __precondition_name__ = "HasTrait"

    __slots__ = ("trait_id",)

    trait_id: str
    """The ID of the trait to check for."""

    def __init__(self, trait: str) -> None:
        super().__init__()
        self.trait_id = trait

    @property
    def description(self) -> str:
        return f"Requires trait {self.trait_id!r}"

    def check(self, target: GameObject) -> bool:
        return has_trait(target, self.trait_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait)


class TargetHasTrait(Precondition):
    """A precondition that checks if a relationship's target has a given trait."""

    __precondition_name__ = "TargetHasTrait"

    __slots__ = ("trait_id",)

    trait_id: str
    """The ID of the trait to check for."""

    def __init__(self, trait: str) -> None:
        super().__init__()
        self.trait_id = trait

    @property
    def description(self) -> str:
        return f"Requires relationship target to have {self.trait_id!r} trait"

    def check(self, target: GameObject) -> bool:
        return has_trait(target.get_component(Relationship).target, self.trait_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        trait = params["trait"]
        return cls(trait)


class SkillRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain level skill."""

    __precondition_name__ = "SkillRequirement"

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
        return f"Requires {self.skill_id} skill level of at least {self.skill_level}"

    def check(self, target: GameObject) -> bool:
        if has_skill(target, self.skill_id):
            skill_stat = get_skill(target, self.skill_id)
            return skill_stat.value >= self.skill_level

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        skill = params["skill"]
        level = params["level"]

        return cls(skill=skill, level=level)


class StatRequirement(Precondition):
    """A precondition that requires a GameObject to have a certain stat value."""

    __precondition_name__ = "StatRequirement"

    __slots__ = "stat_name", "required_value"

    stat_name: str
    """The name of the stat to check."""
    required_value: float
    """The skill level to check for"""

    def __init__(self, stat: str, required_value: float) -> None:
        super().__init__()
        self.stat_name = stat
        self.required_value = required_value

    @property
    def description(self) -> str:
        return f"Requires {self.stat_name} stat value of at least {self.required_value}"

    def check(self, target: GameObject) -> bool:
        if has_stat(target, self.stat_name):
            stat = get_stat(target, self.stat_name)
            return stat.value >= self.required_value

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        stat = params["stat"]
        value = params["value"]

        return cls(stat=stat, required_value=value)


class AtLeastLifeStage(Precondition):
    """A precondition that requires a character to be at least a given life stage."""

    __precondition_name__ = "AtLeaseLifeStage"

    __slots__ = ("life_stage",)

    life_stage: LifeStage
    """The life stage to check for."""

    def __init__(self, life_stage: LifeStage) -> None:
        super().__init__()
        self.life_stage = life_stage

    @property
    def description(self) -> str:
        return f"Requires a lide stage of at least {self.life_stage.name}"

    def check(self, target: GameObject) -> bool:
        if character := target.try_component(Character):
            return character.life_stage >= self.life_stage

        return False

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        life_stage = LifeStage[params["life_stage"]]

        return cls(life_stage)


class RePraxisPrecondition(Precondition):
    """Requires that a given RePraxis query succeeds."""

    __precondition_name__ = "RePraxisQuery"

    __slots__ = ("query", "_description")

    query: DBQuery
    """The query to run."""
    _description: str
    """A description of the query."""

    def __init__(self, query: DBQuery, description: str) -> None:
        super().__init__()
        self.query = query
        self._description = description

    @property
    def description(self) -> str:
        return self._description

    def check(self, target: GameObject) -> bool:
        result = self.query.run(target.world.rp_db, bindings=[{"?target": target.uid}])

        return result.success

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Precondition:
        query = DBQuery(preprocess_query_string(params["query"]))
        description = params.get("description", "")
        return cls(query=query, description=description)
