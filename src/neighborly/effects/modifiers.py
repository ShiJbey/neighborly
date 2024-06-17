import enum
from typing import Optional

from neighborly.components.shared import Modifier
from neighborly.components.skills import Skills
from neighborly.components.stats import StatModifierType, Stats
from neighborly.ecs import GameObject
from neighborly.effects.base_types import Effect
from neighborly.helpers.relationship import reevaluate_relationships
from neighborly.preconditions.base_types import Precondition


class StatModifier(Modifier):
    """Adds a modifier to a stat."""

    __slots__ = (
        "stat",
        "value",
        "modifier_type",
        "duration",
        "_has_duration",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    _has_duration: bool

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        source: Optional[object] = None,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__(source=source, reason=reason)
        self.stat = stat
        self.value = value
        self.modifier_type = modifier_type
        self.duration = duration
        self._has_duration = duration > 0

    def get_value(self) -> float:
        """Get the value of the modifier."""

        return self.value

    def get_modifier_type(self) -> StatModifierType:
        """Get the operation used to calculate the final stat value."""

        return self.modifier_type

    def get_description(self) -> str:
        """Get a description of what the modifier does."""
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""

        if self._has_duration:
            return (
                f"{sign}{abs(self.value)}{percent_sign} {self.stat} "
                f"for the next {self.duration} time steps"
            )

        return f"{sign}{abs(self.value)}{percent_sign} {self.stat}"

    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        return self._has_duration and self.duration <= 0

    def apply(self, target: GameObject) -> None:
        """Apply the effects of the modifier.."""

        target.get_component(Stats).get_stat(self.stat).add_modifier(self)

    def remove(self, target: GameObject) -> None:
        """Remove the effects of this modifier."""

        target.get_component(Stats).get_stat(self.stat).remove_modifier(self)

    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        if self._has_duration:
            self.duration -= 1


class SkillModifier(Modifier):
    """Adds a modifier to a skill."""

    __slots__ = (
        "skill",
        "value",
        "modifier_type",
        "duration",
        "_has_duration",
    )

    skill: str
    value: float
    modifier_type: StatModifierType
    duration: int
    _has_duration: bool

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        source: Optional[object] = None,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__(source=source, reason=reason)
        self.skill = stat
        self.value = value
        self.modifier_type = modifier_type
        self.duration = duration
        self._has_duration = duration > 0
        self.reason = reason

    def get_value(self) -> float:
        """Get the value of the modifier."""

        return self.value

    def get_modifier_type(self) -> StatModifierType:
        """Get the operation used to calculate the final skill value."""

        return self.modifier_type

    def get_description(self) -> str:
        """Get a description of what the modifier does."""
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""

        if self._has_duration:
            return (
                f"{sign}{abs(self.value)}{percent_sign} {self.skill} "
                f"for the next {self.duration} time steps"
            )

        return f"{sign}{abs(self.value)}{percent_sign} {self.skill}"

    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        return self._has_duration and self.duration <= 0

    def apply(self, target: GameObject) -> None:
        """Apply the effects of the modifier.."""

        target.get_component(Stats).get_stat(self.skill).add_modifier(self)

    def remove(self, target: GameObject) -> None:
        """Remove the effects of this modifier."""

        target.get_component(Stats).get_stat(self.skill).remove_modifier(self)

    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        if self._has_duration:
            self.duration -= 1


class RecurringAddToSkill(Modifier):
    """Repeatedly add to the base value of a skill at regular intervals."""

    __slots__ = (
        "skill",
        "value",
        "duration",
        "modifier_type",
        "interval",
        "_cool_down",
        "_has_duration",
    )

    skill: str
    value: float
    modifier_type: StatModifierType
    duration: int
    _has_duration: bool
    interval: int
    _cool_down: int

    def __init__(
        self,
        skill: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        interval: int = 1,
        source: Optional[object] = None,
        reason: str = "",
    ) -> None:
        super().__init__(source, reason)
        self.skill = skill
        self.value = value
        self.modifier_type = modifier_type
        self.duration = duration
        self._has_duration = duration > 0
        self._cool_down = 0
        self.interval = interval

    def get_description(self) -> str:
        """Get a description of what the modifier does."""
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return (
            f"{sign}{abs(self.value)}{percent_sign} {self.skill} "
            f"every {self.interval} time steps "
            f"for the next {self.duration} time steps"
        )

    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        return self._has_duration and self.duration <= 0

    def apply(self, target: GameObject) -> None:
        """Apply the effects of the modifier.."""

        stat = target.get_component(Skills).get_skill(self.skill).stat

        if self.modifier_type == StatModifierType.FLAT:
            stat.base_value += self.value

        else:
            stat.base_value += stat.base_value * (1.0 + self.value)

        self._cool_down = self.interval

    def remove(self, target: GameObject) -> None:
        """Remove the effects of this modifier."""

        return

    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        if self._has_duration:
            self.duration -= 1

        self.interval -= 1

        if self.interval <= 0:
            self.apply(target)


class RecurringAddToStat(Modifier):
    """Repeatedly add to the base value of a stat at regular intervals."""

    __slots__ = (
        "stat",
        "value",
        "duration",
        "modifier_type",
        "interval",
        "_cool_down",
        "_has_duration",
    )

    stat: str
    value: float
    modifier_type: StatModifierType
    duration: int
    _has_duration: bool
    interval: int
    _cool_down: int

    def __init__(
        self,
        stat: str,
        value: float,
        modifier_type: StatModifierType,
        duration: int = -1,
        interval: int = 1,
        source: Optional[object] = None,
        reason: str = "",
    ) -> None:
        super().__init__(source, reason)
        self.stat = stat
        self.value = value
        self.modifier_type = modifier_type
        self.duration = duration
        self._has_duration = duration > 0
        self._cool_down = 0
        self.interval = interval

    def get_description(self) -> str:
        """Get a description of what the modifier does."""
        sign = "+" if self.value > 0 else "-"
        percent_sign = "%" if self.modifier_type == StatModifierType.PERCENT else ""
        return (
            f"{sign}{abs(self.value)}{percent_sign} {self.stat} "
            f"every {self.interval} time steps "
            f"for the next {self.duration} time steps"
        )

    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        return self._has_duration and self.duration <= 0

    def apply(self, target: GameObject) -> None:
        """Apply the effects of the modifier.."""

        stat = target.get_component(Stats).get_stat(self.stat)

        if self.modifier_type == StatModifierType.FLAT:
            stat.base_value += self.value

        else:
            stat.base_value += stat.base_value * (1.0 + self.value)

        self._cool_down = self.interval

    def remove(self, target: GameObject) -> None:
        """Remove the effects of this modifier."""

        return

    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        if self._has_duration:
            self.duration -= 1

        self.interval -= 1

        if self.interval <= 0:
            self.apply(target)


class RelationshipModifierDir(enum.Enum):

    OUTGOING = enum.auto()
    INCOMING = enum.auto()


class RelationshipModifier(Modifier):
    """Conditionally modifies a GameObject's relationships."""

    __slots__ = (
        "direction",
        "description",
        "preconditions",
        "effects",
        "duration",
        "_has_duration",
    )

    direction: RelationshipModifierDir
    """A unique ID for the belief."""
    description: str
    """A text description of this belief."""
    preconditions: list[Precondition]
    """Preconditions checked against a relationship GameObject."""
    effects: list[Effect]
    """Effects to apply to a relationship GameObject."""
    duration: int
    _has_duration: bool

    def __init__(
        self,
        direction: RelationshipModifierDir,
        description: str,
        preconditions: list[Precondition],
        effects: list[Effect],
        source: Optional[object] = None,
        duration: int = -1,
        reason: str = "",
    ) -> None:
        super().__init__(source=source, reason=reason)
        self.direction = direction
        self.description = description
        self.preconditions = preconditions
        self.effects = effects
        self.duration = duration
        self._has_duration = duration > 0

    def get_description(self) -> str:
        """Get a description of what the modifier does."""
        return self.description

    def is_expired(self) -> bool:
        """Return true if the modifier is no longer valid."""

        return self._has_duration and self.duration <= 0

    def update(self, target: GameObject) -> None:
        """Update the modifier for every time step that it is not expired."""

        if self._has_duration:
            self.duration -= 1

    def check_preconditions(self, relationship: GameObject) -> bool:
        """Check the preconditions against the given relationship."""

        return all(p.check(relationship) for p in self.preconditions)

    def apply(self, target: GameObject) -> None:

        reevaluate_relationships(target)

    def remove(self, target: GameObject) -> None:

        reevaluate_relationships(target)

    def apply_to_relationship(self, relationship: GameObject) -> None:
        """Apply this modifier's effects to the given relationship."""

        for effect in self.effects:
            effect.apply(relationship)

    def remove_from_relationship(self, relationship: GameObject) -> None:
        """Remove this modifier's effects from the given relationship."""

        for effect in self.effects:
            effect.remove(relationship)
