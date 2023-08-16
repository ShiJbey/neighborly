"""Neighborly's Stat System.

This module contains Neighborly's implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

The code for the stat class is based on Kryzarel's tutorial on YouTube:
https://www.youtube.com/watch?v=SH25f3cXBVc.

"""

from __future__ import annotations

import enum
import math
from abc import ABC
from typing import Any, Dict, Iterator, List, Optional, Type, Generic, TypeVar

import attrs

from neighborly import Component
from neighborly.ecs import ISerializable

_ST = TypeVar("_ST", int, float)


class Stat(Generic[_ST]):
    """A stat such as strength, reputation, or attraction."""

    __slots__ = (
        "_base_value",
        "_value",
        "_modifiers",
        "_is_dirty",
    )

    _base_value: _ST
    """The base score for this stat used by modifiers."""

    _value: _ST
    """The final score of the stat clamped between the min and max values."""

    _modifiers: List[StatModifier]
    """Active stat modifiers."""

    def __init__(self, base_value: _ST = 0.0) -> None:
        self._base_value = base_value
        self._value = base_value
        self._modifiers = []
        self._is_dirty: bool = False

    @property
    def base_value(self) -> _ST:
        """Get the base value of the relationship stat."""
        return self._base_value

    @base_value.setter
    def base_value(self, value: _ST) -> None:
        """Set the base value of the relationship stat."""
        self._base_value = value
        self._is_dirty = True

    @property
    def value(self) -> _ST:
        """Get the final calculated value of the stat."""
        if self._is_dirty:
            self._recalculate_value()
        return self._value

    def add_modifier(self, modifier: StatModifier) -> None:
        """Add a modifier to the stat."""
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)
        self._is_dirty = True

    def remove_modifier(self, modifier: StatModifier) -> bool:
        """Remove a modifier from the stat.

        Parameters
        ----------
        modifier
            The modifier to remove.

        Returns
        -------
        bool
            True if the modifier was removed, False otherwise.
        """
        try:
            self._modifiers.remove(modifier)
            self._is_dirty = True
            return True
        except ValueError:
            return False

    def remove_modifiers_from_source(self, source: object) -> bool:
        """Remove all modifiers applied from the given source.

        Parameters
        ----------
        source
            A source to check for.

        Returns
        -------
        bool
            True if any modifiers were removed, False otherwise.
        """
        did_remove: bool = False

        for modifier in [*self._modifiers]:
            if modifier.source == source:
                self._is_dirty = True
                did_remove = True
                self._modifiers.remove(modifier)

        return did_remove

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    def _recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""

        final_value: _ST = self.base_value
        sum_percent_add: float = 0.0

        for i, modifier in enumerate(self._modifiers):
            if modifier.modifier_type == StatModifierType.Flat:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PercentAdd:
                sum_percent_add += modifier.value

                if (
                    i + 1 >= len(self._modifiers)
                    or self._modifiers[i + 1].modifier_type
                    != StatModifierType.PercentAdd
                ):
                    final_value *= 1 + sum_percent_add
                    sum_percent_add = 0

            elif modifier.modifier_type == StatModifierType.PercentMult:
                final_value *= 1 + modifier.value

        self._value = final_value

        self._is_dirty = False

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(value={}, base={}, modifiers={})".format(
            self.__class__.__name__,
            self.value,
            self.base_value,
            [m.__repr__() for m in self._modifiers],
        )


class StatComponent(Component, ISerializable, Generic[_ST], ABC):
    """A stat such as strength, reputation, or attraction."""

    __slots__ = (
        "_base_value",
        "_value",
        "_modifiers",
        "_is_dirty",
    )

    _base_value: _ST
    """The base score for this stat used by modifiers."""

    _value: _ST
    """The final score of the stat clamped between the min and max values."""

    _modifiers: List[StatModifier]
    """Active stat modifiers."""

    def __init__(self, base_value: _ST = 0.0) -> None:
        super().__init__()
        self._base_value = base_value
        self._value = base_value
        self._modifiers = []
        self._is_dirty: bool = False

    @property
    def base_value(self) -> _ST:
        """Get the base value of the relationship stat."""
        return self._base_value

    @base_value.setter
    def base_value(self, value: _ST) -> None:
        """Set the base value of the relationship stat."""
        self._base_value = value
        self._is_dirty = True

    @property
    def value(self) -> _ST:
        """Get the final calculated value of the stat."""
        if self._is_dirty:
            self._recalculate_value()
        return self._value

    def add_modifier(self, modifier: StatModifier) -> None:
        """Add a modifier to the stat."""
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)
        self._is_dirty = True

    def remove_modifier(self, modifier: StatModifier) -> bool:
        """Remove a modifier from the stat.

        Parameters
        ----------
        modifier
            The modifier to remove.

        Returns
        -------
        bool
            True if the modifier was removed, False otherwise.
        """
        try:
            self._modifiers.remove(modifier)
            self._is_dirty = True
            return True
        except ValueError:
            return False

    def remove_modifiers_from_source(self, source: object) -> bool:
        """Remove all modifiers applied from the given source.

        Parameters
        ----------
        source
            A source to check for.

        Returns
        -------
        bool
            True if any modifiers were removed, False otherwise.
        """
        did_remove: bool = False

        for modifier in [*self._modifiers]:
            if modifier.source == source:
                self._is_dirty = True
                did_remove = True
                self._modifiers.remove(modifier)

        return did_remove

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    def _recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""

        final_value: float = self.base_value
        sum_percent_add: float = 0.0

        for i, modifier in enumerate(self._modifiers):
            if modifier.modifier_type == StatModifierType.Flat:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PercentAdd:
                sum_percent_add += modifier.value

                if (
                    i + 1 >= len(self._modifiers)
                    or self._modifiers[i + 1].modifier_type
                    != StatModifierType.PercentAdd
                ):
                    final_value *= 1 + sum_percent_add
                    sum_percent_add = 0

            elif modifier.modifier_type == StatModifierType.PercentMult:
                final_value *= 1 + modifier.value

        self._value = final_value

        self._is_dirty = False

    def on_add(self) -> None:
        self.gameobject.get_component(Stats).add_stat(self)

    def on_remove(self) -> None:
        self.gameobject.get_component(Stats).remove_stat(self)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(value={}, base={}, modifiers={})".format(
            self.__class__.__name__,
            self.value,
            self.base_value,
            [m.__repr__() for m in self._modifiers],
        )


class ClampedStatComponent(StatComponent[_ST], ABC):
    """A stat component with a value clamped between maximum and minimum values."""

    __slots__ = (
        "_min_value",
        "_max_value",
    )

    _min_value: _ST
    """The minimum score the overall stat is clamped to."""

    _max_value: _ST
    """The maximum score the overall stat is clamped to."""

    def __init__(
        self,
        base_value: _ST,
        min_value: _ST,
        max_value: _ST,
    ) -> None:
        super().__init__(base_value=base_value)
        self._min_value = min_value
        self._max_value = max_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    def _recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""
        super()._recalculate_value()

        self._value = math.ceil(max(self._min_value, min(self._max_value, self._value)))

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(value={}, base={}, max={}, min={}, modifiers={})".format(
            self.__class__.__name__,
            self.value,
            self.base_value,
            self._max_value,
            self._min_value,
            [m.__repr__() for m in self._modifiers],
        )


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    Flat = 100
    """Adds a constant value to the base value."""

    PercentAdd = 200
    """Additively stacks percentage increases on a modified stat."""

    PercentMult = 300
    """Multiplicatively stacks percentage increases on a modified stat."""


@attrs.define(slots=True)
class StatModifier:
    """Stat modifiers provide buffs and de-buffs to the value of stat components.

    Modifiers are applied to stats in ascending-priority-order. So, stats with lower
    orders are added first.
    """

    value: float
    """The amount to modify the stat."""

    modifier_type: StatModifierType
    """How the modifier value is applied."""

    order: int = -1
    """The priority of this modifier when calculating final stat values."""

    source: Optional[object] = None
    """The source of the modifier (for debugging purposes)."""

    def __attrs_post_init__(self) -> None:
        if self.order == -1:
            self.order = int(self.modifier_type)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "modifier_type": self.modifier_type.name,
            "order": self.order,
            "source": str(self.source) if self.source is not None else "",
        }


class Stats(Component, ISerializable):
    """Tracks the current stat components attached to a GameObject.

    Notes
    -----
    The entries in this component are updated automatically when stat components
    are added/removed form a GameObject
    """

    __slots__ = "_stats"

    _stats: Dict[Type[StatComponent], StatComponent]

    def __init__(self) -> None:
        super().__init__()
        self._stats = {}

    def iter_stats(self) -> Iterator[StatComponent]:
        """Get an iterator to the collection of stat components."""
        return self._stats.values().__iter__()

    def add_stat(self, stat: StatComponent) -> None:
        """Add a new stat to the Stats component.

        Parameters
        ----------
        stat
            The stat component that was added to the GameObject
        """
        self._stats[type(stat)] = stat

    def remove_stat(self, stat: StatComponent) -> None:
        """Remove stat from the Stats component.

        Parameters
        ----------
        stat
            The component to remove
        """
        del self._stats[type(stat)]

    def to_dict(self) -> Dict[str, Any]:
        return {"stats": [s.__name__ for s in self._stats.keys()]}
