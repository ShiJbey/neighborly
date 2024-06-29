"""Built-in Effect Definitions.

This module contains class definitions for effects that may be applied by traits and
social rules.

"""

from __future__ import annotations

from typing import Any, Iterable

from neighborly.components.location import LocationPreference, LocationPreferences
from neighborly.components.relationship import Relationship
from neighborly.components.stats import StatModifierType, Stats
from neighborly.ecs import GameObject, World
from neighborly.effects.base_types import Effect
from neighborly.effects.modifiers import (
    RelationshipModifier,
    RelationshipModifierDir,
    StatModifier,
)
from neighborly.helpers.relationship import (
    add_relationship_modifier,
    remove_relationship_modifiers_from_source,
)
from neighborly.helpers.shared import add_modifier, remove_modifiers_from_source
from neighborly.helpers.skills import add_skill, get_skill, has_skill
from neighborly.libraries import EffectLibrary, PreconditionLibrary
from neighborly.preconditions.base_types import Precondition


class AddStatModifier(Effect):
    """Add a modifier to a stat."""

    __effect_name__ = "AddStatModifier"

    __slots__ = ("stat", "value", "modifier_type", "duration", "has_duration")

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__(reason=reason)
        self.stat = stat
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration

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
                reason=self.reason,
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

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
    )

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
    )

    skill: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool

    def __init__(
        self,
        skill: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__(reason=reason)
        self.skill = skill
        self.modifier_type = modifier_type
        self.value = value
        self.duration = duration

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
                reason=self.reason,
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

    __slots__ = (
        "location_preconditions",
        "character_preconditions",
        "value",
        "modifier_type",
        "source",
    )

    location_preconditions: list[Precondition]
    """Precondition to run against the location when scoring."""
    character_preconditions: list[Precondition]
    """Precondition to run against a character when scoring."""
    value: float
    """The amount to apply to the score."""
    modifier_type: StatModifierType
    """How to apply the modifier value."""

    def __init__(
        self,
        location_preconditions: list[Precondition],
        character_preconditions: list[Precondition],
        value: float,
        modifier_type: StatModifierType,
        reason: str = "",
    ) -> None:
        super().__init__(reason=reason)
        self.location_preconditions = location_preconditions
        self.character_preconditions = character_preconditions
        self.value = value
        self.modifier_type = modifier_type

    @property
    def description(self) -> str:
        location_precondition_descriptions = "; ".join(
            [p.description for p in self.location_preconditions]
        )

        character_precondition_descriptions = "; ".join(
            [p.description for p in self.character_preconditions]
        )

        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""

        return (
            f"Effect(s): Location preference {sign}{abs(self.value)}{percent_sign}\n"
            f"Location Precondition(s): {location_precondition_descriptions}\n"
            f"Character Precondition(s): {character_precondition_descriptions}\n"
        )

    def apply(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).add_preference(
            LocationPreference(
                location_preconditions=self.location_preconditions,
                character_preconditions=self.character_preconditions,
                value=self.value,
                modifier_type=self.modifier_type,
                reason=self.reason,
                source=self,
            )
        )

    def remove(self, target: GameObject) -> None:
        target.get_component(LocationPreferences).remove_from_source(self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        value: float = float(params["value"])
        modifier_name: str = params.get("modifier_type", "FLAT")
        modifier_type = StatModifierType[modifier_name.upper()]

        reason: str = params.get("reason", "")

        precondition_library = world.resources.get_resource(PreconditionLibrary)

        location_preconditions: list[Precondition] = []
        for entry in params.get("location_preconditions", []):
            location_preconditions.append(
                precondition_library.create_from_obj(world, entry)
            )

        character_preconditions: list[Precondition] = []
        for entry in params.get("character_preconditions", []):
            character_preconditions.append(
                precondition_library.create_from_obj(world, entry)
            )

        return cls(
            location_preconditions=location_preconditions,
            character_preconditions=character_preconditions,
            value=value,
            modifier_type=modifier_type,
            reason=reason,
        )


class AddRelationshipModifier(Effect):
    """Adds a relationship modifier to the GamObject."""

    __effect_name__ = "AddRelationshipModifier"

    __slots__ = ("direction", "_description", "preconditions", "effects")

    direction: RelationshipModifierDir
    _description: str
    preconditions: list[Precondition]
    effects: list[Effect]

    def __init__(
        self,
        direction: RelationshipModifierDir,
        description: str,
        preconditions: Iterable[Precondition],
        effects: Iterable[Effect],
        reason: str = "",
    ) -> None:
        super().__init__(reason=reason)
        self.direction = direction
        self._description = description
        self.preconditions = list(preconditions)
        self.effects = list(effects)

    @property
    def description(self) -> str:
        return self._description

    def apply(self, target: GameObject) -> None:
        add_relationship_modifier(
            target,
            RelationshipModifier(
                direction=self.direction,
                description=self.description,
                preconditions=self.preconditions,
                effects=self.effects,
                source=self,
                reason=self.reason,
            ),
        )

    def remove(self, target: GameObject) -> None:
        remove_relationship_modifiers_from_source(target, self)

    @classmethod
    def instantiate(cls, world: World, params: dict[str, Any]) -> Effect:
        modifier_dir = RelationshipModifierDir[str(params["direction"]).upper()]
        description = params.get("description", "")
        reason: str = params.get("reason", "")

        precondition_library = world.resources.get_resource(PreconditionLibrary)
        preconditions: list[Precondition] = []
        for entry in params.get("preconditions", []):
            preconditions.append(precondition_library.create_from_obj(world, entry))

        effect_library = world.resources.get_resource(EffectLibrary)
        effects: list[Effect] = []
        for entry in params.get("effects", []):
            effects.append(effect_library.create_from_obj(world, entry))

        return cls(
            direction=modifier_dir,
            description=description,
            preconditions=preconditions,
            effects=effects,
            reason=reason,
        )


class AddStatModifierToTarget(Effect):
    """Adds a stat modifier to the target of a relationship."""

    __effect_name__ = "AddStatModifierToTarget"

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
        "duration",
        "has_duration",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    has_duration: bool

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__()
        self.stat = stat
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
                reason=self.reason,
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

    __slots__ = ("stat", "value", "modifier_type", "duration", "has_duration")

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
        self.stat = stat
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
