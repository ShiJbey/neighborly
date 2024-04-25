"""Built-in Effect Definitions.

This module contains class definitions for effects that may be applied by traits and
social rules.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.location import LocationPreferences
from neighborly.components.stats import StatModifier, StatModifierType
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.helpers.relationship import add_belief, remove_belief
from neighborly.helpers.skills import add_skill, get_skill, has_skill
from neighborly.helpers.stats import get_stat


class AddStatBuff(Effect):
    """Add a buff to a stat."""

    __effect_name__ = "AddStatBuff"

    __slots__ = ("modifier_type", "amount", "stat_id")

    modifier_type: StatModifierType
    """The how the modifier amount should be applied to the stat."""
    amount: float
    """The amount of buff to apply to the stat."""
    stat_id: str
    """The definition ID of the stat to modify."""

    def __init__(
        self,
        stat_id: str,
        amount: float,
        modifier_type: StatModifierType,
    ) -> None:
        super().__init__()
        self.stat_id = stat_id
        self.modifier_type = modifier_type
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.stat_id}: add buff {self.amount}({self.modifier_type.name})."

    def apply(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).add_modifier(
            StatModifier(
                modifier_type=self.modifier_type,
                value=self.amount,
                source=self,
            )
        )

    def remove(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).remove_modifiers_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        amount: float = float(params["amount"])
        stat_id: str = str(params["stat"])

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(stat_id=stat_id, amount=amount, modifier_type=modifier_type)


class AddStatDebuff(Effect):
    """Add a debuff to a stat."""

    __effect_name__ = "AddStatDebuff"

    __slots__ = "modifier_type", "amount", "stat_id"

    modifier_type: StatModifierType
    """The how the modifier amount should be applied to the stat."""
    amount: float
    """The amount of buff to apply to the stat."""
    stat_id: str
    """The definition ID of the stat to modify."""

    def __init__(
        self,
        stat_id: str,
        amount: float,
        modifier_type: StatModifierType,
    ) -> None:
        super().__init__()
        self.stat_id = stat_id
        self.modifier_type = modifier_type
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.stat_id}: add buff {-self.amount}({self.modifier_type.name})."

    def apply(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).add_modifier(
            StatModifier(
                modifier_type=self.modifier_type,
                value=-self.amount,
                source=self,
            )
        )

    def remove(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).remove_modifiers_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_name: str = params.get("modifier_type", "FLAT")
        amount: float = float(params["amount"])
        stat_id: str = str(params["stat"])

        modifier_type = StatModifierType[modifier_name.upper()]

        return cls(stat_id=stat_id, amount=amount, modifier_type=modifier_type)


class IncreaseBaseStat(Effect):
    """Permanently increase the base value of a stat."""

    __effect_name__ = "IncreaseBaseStat"

    __slots__ = ("amount", "stat_id")

    amount: float
    """The amount of buff to apply to the stat."""
    stat_id: str
    """The definition ID of the stat to modify."""

    def __init__(
        self,
        stat_id: str,
        amount: float,
    ) -> None:
        super().__init__()
        self.stat_id = stat_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.stat_id}: base value {self.amount}."

    def apply(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).base_value += self.amount

    def remove(self, target: GameObject) -> None:
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        amount: float = float(params["amount"])
        stat_id: str = str(params["stat"])

        return cls(stat_id=stat_id, amount=amount)


class DecreaseBaseStat(Effect):
    """Permanently decrease the base value of a stat."""

    __effect_name__ = "DecreaseBaseStat"

    __slots__ = ("amount", "stat_id")

    amount: float
    """The amount of buff to apply to the stat."""
    stat_id: str
    """The definition ID of the stat to modify."""

    def __init__(
        self,
        stat_id: str,
        amount: float,
    ) -> None:
        super().__init__()
        self.stat_id = stat_id
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.stat_id}: base value {-self.amount}."

    def apply(self, target: GameObject) -> None:
        get_stat(target, self.stat_id).base_value -= self.amount

    def remove(self, target: GameObject) -> None:
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        amount: float = float(params["amount"])
        stat_id: str = str(params["stat"])

        return cls(stat_id=stat_id, amount=amount)


class AddSkillDebuff(Effect):
    """Adds a debuff modifier to a skill."""

    __effect_name__ = "AddSkillDebuff"

    __slots__ = ("skill_name", "amount")

    skill_name: str
    """The skill to increase the base value of"""
    amount: float
    """The amount of buff to apply to the stat."""

    def __init__(self, skill_name: str, amount: float) -> None:
        super().__init__()
        self.skill_name = skill_name
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.skill_name}: add debuff {-self.amount}"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill_name):
            add_skill(target, self.skill_name)
        get_skill(target, self.skill_name).add_modifier(
            StatModifier(
                value=-self.amount, modifier_type=StatModifierType.FLAT, source=self
            )
        )

    def remove(self, target: GameObject) -> None:
        get_skill(target, self.skill_name).remove_modifiers_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        skill_name: str = params["skill"]
        amount: float = float(params["amount"])

        return cls(
            skill_name=skill_name,
            amount=amount,
        )


class AddSkillBuff(Effect):
    """Adds a stat buff modifier to a skill."""

    __effect_name__ = "AddSkillBuff"

    __slots__ = ("skill_name", "amount")

    skill_name: str
    """The skill to increase the base value of"""
    amount: float
    """The amount of buff to apply to the stat."""

    def __init__(self, skill_name: str, amount: float) -> None:
        super().__init__()
        self.skill_name = skill_name
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.skill_name}: add buff {self.amount}"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill_name):
            add_skill(target, self.skill_name)
        get_skill(target, self.skill_name).add_modifier(
            StatModifier(
                value=self.amount, modifier_type=StatModifierType.FLAT, source=self
            )
        )

    def remove(self, target: GameObject) -> None:
        get_skill(target, self.skill_name).remove_modifiers_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        skill_name: str = params["skill"]
        amount: float = float(params["amount"])

        return cls(
            skill_name=skill_name,
            amount=amount,
        )


class DecreaseBaseSkill(Effect):
    """Permanently decreases the base value of a skill."""

    __effect_name__ = "DecreaseBaseSkill"

    __slots__ = ("skill_name", "amount")

    skill_name: str
    """The skill to increase the base value of"""
    amount: float
    """The amount of buff to apply to the stat."""

    def __init__(self, skill_name: str, amount: float) -> None:
        super().__init__()
        self.skill_name = skill_name
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.skill_name}: base value {-self.amount}"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill_name):
            add_skill(target, self.skill_name)
        get_skill(target, self.skill_name).base_value -= self.amount

    def remove(self, target: GameObject) -> None:
        # This effect cannot be undone.
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        skill_name: str = params["skill"]
        amount: float = float(params["amount"])

        return cls(
            skill_name=skill_name,
            amount=amount,
        )


class IncreaseBaseSkill(Effect):
    """Permanently increases the base value of a skill."""

    __effect_name__ = "IncreaseBaseSkill"

    __slots__ = ("skill_name", "amount")

    skill_name: str
    """The skill to increase the base value of"""
    amount: float
    """The amount of buff to apply to the stat."""

    def __init__(self, skill_name: str, amount: float) -> None:
        super().__init__()
        self.skill_name = skill_name
        self.amount = amount

    @property
    def description(self) -> str:
        return f"{self.skill_name}: base value {self.amount}"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill_name):
            add_skill(target, self.skill_name)
        get_skill(target, self.skill_name).base_value += self.amount

    def remove(self, target: GameObject) -> None:
        # This effect cannot be undone
        return

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        skill_name: str = params["skill"]
        amount: float = float(params["amount"])

        return cls(
            skill_name=skill_name,
            amount=amount,
        )


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
