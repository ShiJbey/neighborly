"""Built-in Effect Definitions.

This module contains class definitions for effects that may be applied by traits and
social rules.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.location import LocationPreferences
from neighborly.components.relationship import Relationship
from neighborly.components.stats import StatModifierType, Stats
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.helpers.relationship import add_belief, remove_belief
from neighborly.helpers.shared import (
    add_modifier,
    remove_modifiers_from_source,
)
from neighborly.helpers.skills import add_skill, get_skill, has_skill
from neighborly.effects.modifiers import StatModifier


class AddStatModifier(Effect):
    """Add a modifier to a stat."""

    __effect_name__ = "AddStatModifier"

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
        "duration",
        "has_duration",
        "reason",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool
    reason: str

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__()
        self.stat_id = stat
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration
        self.reason = reason

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.stat}"

    def apply(self, target: GameObject) -> None:
        add_modifier(
            target,
            StatModifier(
                stat=self.stat,
                value=self.value,
                modifier_type=self.modifier_type,
                source=self,
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_modifiers_from_source(target, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        value: float = float(params["value"])
        stat: str = str(params["stat"])
        duration: int = int(params.get("duration", -1))
        reason: str = params.get("reason", "")

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(
            stat=stat,
            value=value,
            modifier_type=modifier_type,
            duration=duration,
            reason=reason,
        )


class AddToBaseStat(Effect):
    """Permanently increases the base value of a skill."""

    __effect_name__ = "AddToBaseStat"

    __slots__ = ("stat", "value", "modifier_type")

    stat: str
    value: float
    modifier_type: StatModifierType

    def __init__(
        self, stat: str, value: float, modifier_type: StatModifierType
    ) -> None:
        super().__init__()
        self.stat = stat
        self.value = value
        self.modifier_type = modifier_type

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.stat}"

    def apply(self, target: GameObject) -> None:
        stat = target.get_component(Stats).get_stat(self.stat)

        if self.modifier_type == StatModifierType.FLAT:
            stat.base_value += self.value

        else:
            stat.base_value += stat.base_value * (1.0 + self.value)

    def remove(self, target: GameObject) -> None:
        # This effect cannot be undone
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        stat: str = params["stat"]
        value: float = float(params["value"])
        modifier_name: str = params.get("modifier_type", "FLAT")
        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(stat=stat, value=value, modifier_type=modifier_type)


class AddSkillModifier(Effect):
    """Add a modifier to a skill."""

    __effect_name__ = "AddSkillModifier"

    __slots__ = (
        "skill",
        "value",
        "modifier_type",
        "duration",
        "has_duration",
        "reason",
    )

    skill: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool
    reason: str

    def __init__(
        self,
        skill: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__()
        self.stat_id = skill
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration
        self.reason = reason

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.skill}"

    def apply(self, target: GameObject) -> None:
        add_modifier(
            target,
            StatModifier(
                stat=self.skill,
                value=self.value,
                modifier_type=self.modifier_type,
                source=self,
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_modifiers_from_source(target, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        value: float = float(params["value"])
        skill: str = str(params["skill"])
        duration: int = int(params.get("duration", -1))
        reason: str = params.get("reason", "")

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(
            skill=skill,
            value=value,
            modifier_type=modifier_type,
            duration=duration,
            reason=reason,
        )


class AddToBaseSkill(Effect):
    """Permanently increases the base value of a skill."""

    __effect_name__ = "IncreaseBaseSkill"

    __slots__ = ("skill", "value", "modifier_type")

    skill: str
    value: float
    modifier_type: StatModifierType

    def __init__(
        self, skill: str, value: float, modifier_type: StatModifierType
    ) -> None:
        super().__init__()
        self.skill = skill
        self.value = value
        self.modifier_type = modifier_type

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.skill}"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill):
            add_skill(target, self.skill)

        stat = get_skill(target, self.skill).stat

        if self.modifier_type == StatModifierType.FLAT:
            stat.base_value += self.value

        else:
            stat.base_value += stat.base_value * (1.0 + self.value)

    def remove(self, target: GameObject) -> None:
        # This effect cannot be undone
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        skill: str = params["skill"]
        value: float = float(params["value"])
        modifier_name: str = params.get("modifier_type", "FLAT")
        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(skill=skill, value=value, modifier_type=modifier_type)


class AddLocationPreference(Effect):
    """Add a new location preference rule."""

    __effect_name__ = "AddLocationPreference"

    __slots__ = ("rule_id",)

    rule_id: str
    """The ID of a location preference rule."""

    def __init__(self, rule_id: str) -> None:
        super().__init__()
        self.rule_id = rule_id

    @property
    def description(self) -> str:
        return f"Gains location preference {self.rule_id!r}"

    def apply(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).add_rule(self.rule_id)

    def remove(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).remove_rule(self.rule_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        rule_id = params["rule_id"]
        return cls(rule_id=rule_id)


class AddBelief(Effect):
    """Add a belief to an agent."""

    __effect_name__ = "AddBelief"

    __slots__ = ("belief_id",)

    belief_id: str
    """The ID of a belief."""

    def __init__(self, rule_id: str) -> None:
        super().__init__()
        self.belief_id = rule_id

    @property
    def description(self) -> str:
        return f"Gains belief: {self.belief_id!r}"

    def apply(self, target: GameObject) -> None:
        add_belief(target, self.belief_id)

    def remove(self, target: GameObject) -> None:
        remove_belief(target, self.belief_id)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        belief_id = params["belief_id"]
        return cls(rule_id=belief_id)


class AddRelationshipModifier(Effect):
    """Adds a relationship modifier to the GamObject."""

    __effect_name__ = "AddRelationshipModifier"


class AddStatModifierToTarget(Effect):
    """Adds a stat modifier to the target of a relationship."""

    __effect_name__ = "AddStatModifierToTarget"

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
        "duration",
        "has_duration",
        "reason",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool
    reason: str

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__()
        self.stat_id = stat
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration
        self.reason = reason

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.stat}"

    def apply(self, target: GameObject) -> None:
        add_modifier(
            target.get_component(Relationship).target,
            StatModifier(
                stat=self.stat,
                value=self.value,
                modifier_type=self.modifier_type,
                source=self,
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_modifiers_from_source(target.get_component(Relationship).target, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        value: float = float(params["value"])
        stat: str = str(params["stat"])
        duration: int = int(params.get("duration", -1))
        reason: str = params.get("reason", "")

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(
            stat=stat,
            value=value,
            modifier_type=modifier_type,
            duration=duration,
            reason=reason,
        )


class AddStatModifierToOwner(Effect):
    """Adds a stat modifier to the owner of a relationship."""

    __effect_name__ = "AddStatModifierToOwner"

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
        "duration",
        "has_duration",
        "reason",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool
    reason: str

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__()
        self.stat_id = stat
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration
        self.reason = reason

    @property
    def description(self) -> str:
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return f"{sign}{abs(self.value)}{percent_sign} {self.stat}"

    def apply(self, target: GameObject) -> None:
        add_modifier(
            target.get_component(Relationship).owner,
            StatModifier(
                stat=self.stat,
                value=self.value,
                modifier_type=self.modifier_type,
                source=self,
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_modifiers_from_source(target.get_component(Relationship).owner, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        value: float = float(params["value"])
        stat: str = str(params["stat"])
        duration: int = int(params.get("duration", -1))
        reason: str = params.get("reason", "")

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(
            stat=stat,
            value=value,
            modifier_type=modifier_type,
            duration=duration,
            reason=reason,
        )
