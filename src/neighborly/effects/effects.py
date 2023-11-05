"""Built-in Effect Definitions.

This module contains class definitions for effects that may be applied by traits and
social rules.

"""

from __future__ import annotations

from typing import Any

from neighborly.components.location import LocationPreferenceRule, LocationPreferences
from neighborly.components.relationship import SocialRule
from neighborly.components.stats import StatModifier, StatModifierType
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.helpers.relationship import (
    add_social_rule,
    remove_all_social_rules_from_source,
)
from neighborly.helpers.skills import add_skill, get_skill, has_skill
from neighborly.helpers.stats import get_stat
from neighborly.libraries import EffectLibrary, PreconditionLibrary
from neighborly.preconditions.base_types import Precondition


class StatBuff(Effect):
    """Add a buff to a stat."""

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
        return (
            f"add {self.amount}({self.modifier_type.name}) modifier to {self.stat_id}"
        )

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


class IncreaseSkill(Effect):
    """Permanently increases a skill stat."""

    __slots__ = "skill_name", "amount"

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
        return f"add {self.amount} to the {self.skill_name} skill"

    def apply(self, target: GameObject) -> None:
        if not has_skill(target, self.skill_name):
            add_skill(target, self.skill_name)
        get_skill(target, self.skill_name).base_value += self.amount

    def remove(self, target: GameObject) -> None:
        # Skill increases the skill stat. Cannot be removed.
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

    __slots__ = "preconditions", "probability"

    preconditions: list[Precondition]
    """Preconditions that need to pass to apply the preference rule."""
    probability: float
    """A probability of the character frequenting the location."""

    def __init__(
        self,
        preconditions: list[Precondition],
        probability: float,
    ) -> None:
        super().__init__()
        self.preconditions = preconditions
        self.probability = probability

    @property
    def description(self) -> str:
        output = "(Location Preference): "

        if self.preconditions:
            output += "if location "
            output += " and ".join(p.description for p in self.preconditions)
            output += ", then "

        output += f"apply an {self.probability*100}% consideration score."

        return output

    def apply(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).add_rule(
            LocationPreferenceRule(
                preconditions=self.preconditions,
                probability=self.probability,
                source=self,
            )
        )

    def remove(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).remove_rules_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        preconditions_data: list[dict[str, Any]] = params.get("preconditions", [])
        probability: float = float(params["probability"])

        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)

        preconditions: list[Precondition] = [
            precondition_library.create_from_obj(world, entry)
            for entry in preconditions_data
        ]

        return cls(
            preconditions=preconditions,
            probability=probability,
        )


class AddSocialRule(Effect):
    """Add a new social rule."""

    __slots__ = "preconditions", "effects"

    preconditions: list[Precondition]
    """Preconditions that need to pass to apply the preference rule."""
    effects: list[Effect]
    """Effects applied if the relationship passes the preconditions."""

    def __init__(
        self, preconditions: list[Precondition], effects: list[Effect]
    ) -> None:
        super().__init__()
        self.preconditions = preconditions
        self.effects = effects

    @property
    def description(self) -> str:
        output = "(Social Rule): "

        if self.preconditions:
            output += "if "
            output += " and ".join(p.description for p in self.preconditions)
            output += ", then "

        output += " and ".join(e.description for e in self.effects)

        return output

    def apply(self, target: GameObject) -> None:
        add_social_rule(
            target,
            SocialRule(
                preconditions=self.preconditions, effects=self.effects, source=self
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_all_social_rules_from_source(target, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        preconditions_data: list[dict[str, Any]] = params.get("preconditions", [])
        effects_data: list[dict[str, Any]] = params.get("effects", [])

        precondition_library = world.resource_manager.get_resource(PreconditionLibrary)
        effect_library = world.resource_manager.get_resource(EffectLibrary)

        preconditions: list[Precondition] = [
            precondition_library.create_from_obj(world, entry)
            for entry in preconditions_data
        ]

        effects: list[Effect] = [
            effect_library.create_from_obj(world, entry) for entry in effects_data
        ]

        return cls(
            preconditions=preconditions,
            effects=effects,
        )
