"""Stat System.

This module contains an implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

The code for the stat class is based on Kryzarel's tutorial on YouTube:
https://www.youtube.com/watch?v=SH25f3cXBVc.

"""

from __future__ import annotations

import enum
import math
import sys
from typing import Any, Dict, List, Optional

import attrs

from neighborly.ecs import Component


class Stat:
    """A stat such as strength, reputation, or attraction.

    Parameters
    ----------
    base_value
        The value of the stat with no modifiers applied.
    bounds
        The min and max bounds for the stat.
    is_discrete
        Should the final calculated stat value be converted to an int.
    """

    __slots__ = (
        "_base_value",
        "_value",
        "_modifiers",
        "_is_dirty",
        "_min_value",
        "_max_value",
        "_is_bounded",
        "_is_discrete",
    )

    _base_value: float
    """The base score for this stat used by modifiers."""
    _value: float
    """The final score of the stat clamped between the min and max values."""
    _modifiers: List[StatModifier]
    """Active stat modifiers."""
    _min_value: float
    """The minimum score the overall stat is clamped to."""
    _max_value: float
    """The maximum score the overall stat is clamped to."""
    _is_discrete: bool
    """Should the final calculated stat value be converted to an int."""

    def __init__(
        self,
        base_value: float,
        bounds: Optional[tuple[float, float]] = None,
        is_discrete: bool = False,
    ) -> None:
        self._base_value = base_value
        self._value = base_value
        self._modifiers = []
        self._is_dirty = False
        self._is_discrete = is_discrete

        if bounds is None:
            self._min_value = sys.float_info.min
            self._max_value = sys.float_info.max
            self._is_bounded = False
        else:
            self._min_value, self._max_value = bounds
            self._is_bounded = True

    @property
    def base_value(self) -> float:
        """Get the base value of the relationship stat."""
        return self._base_value

    @base_value.setter
    def base_value(self, value: float) -> None:
        """Set the base value of the relationship stat."""
        self._base_value = value
        self._is_dirty = True

    @property
    def value(self) -> float:
        """Get the final calculated value of the stat."""
        if self._is_dirty:
            self.recalculate_value()
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
        """Serialize the stat to a dict for data analysis."""
        return {
            "value": self.value,
        }

    def recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""

        final_value: float = self._base_value
        sum_percent_add: float = 0.0

        for i, modifier in enumerate(self._modifiers):
            if modifier.modifier_type == StatModifierType.FLAT:
                final_value += modifier.value

            elif modifier.modifier_type == StatModifierType.PERCENT_ADD:
                sum_percent_add += modifier.value

                if (
                    i + 1 >= len(self._modifiers)
                    or self._modifiers[i + 1].modifier_type
                    != StatModifierType.PERCENT_ADD
                ):
                    final_value *= 1 + sum_percent_add
                    sum_percent_add = 0

            elif modifier.modifier_type == StatModifierType.PERCENT_MULTIPLY:
                final_value *= 1 + modifier.value

        self._value = final_value

        if self._is_bounded:
            self._value = max(self._min_value, min(self._max_value, self._value))

        if self._is_discrete:
            self._value = math.trunc(self._value)

        self._is_dirty = False

    def is_bounded(self) -> bool:
        """Returns True if the stat has min and max values."""
        return self._is_bounded

    @property
    def normalized(self) -> float:
        """Get the normalized value from 0.0 to 1.0."""
        if self.is_bounded():
            return (self.value - self._min_value) / (self._max_value - self._min_value)

        raise ValueError("Cannot calculate normalized value of an unbound stat.")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(value={self.value}, base={self.base_value}, "
            f"max={self._max_value}, min={self._min_value}, "
            f"modifiers={self._modifiers})"
        )


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    FLAT = 100
    """Adds a constant value to the base value."""

    PERCENT_ADD = 200
    """Additively stacks percentage increases on a modified stat."""

    PERCENT_MULTIPLY = 300
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

    def to_dict(self) -> dict[str, Any]:
        """Serialize the modifier to a dictionary."""
        return {
            "value": self.value,
            "modifier_type": self.modifier_type.name,
            "order": self.order,
            "source": str(self.source) if self.source is not None else "",
        }


class Stats(Component):
    """Tracks all the various stats for a GameObject."""

    __slots__ = ("_stats",)

    _stats: dict[str, Stat]
    """Map of Stat IDs to Stat instances."""

    def __init__(self) -> None:
        super().__init__()
        self._stats = {}

    def add_stat(self, stat_id: str, stat: Stat) -> None:
        """Add a new stat.

        Parameters
        ----------
        stat_id
            A string ID to associate with the stat.
        stat
            A stat instance.
        """
        self._stats[stat_id] = stat

    def has_stat(self, stat_id: str) -> bool:
        """Check if a stat exists.

        Parameters
        ----------
        stat_id
            A string ID associated with a stat.

        Returns
        -------
        bool
            True if the character has a stat mapped to the ID, False otherwise.
        """
        return stat_id in self._stats

    def get_stat(self, stat_id: str) -> Stat:
        """Get a stat.

        Parameters
        ----------
        stat_id
            A string ID associated with a stat.

        Returns
        -------
        Stat
            The Stat instance associated with the given ID.
        """
        return self._stats[stat_id]

    def remove_stat(self, stat_id: str) -> bool:
        """Remove a stat.

        Parameters
        ----------
        stat_id
            A string ID associated with a stat

        Returns
        -------
        bool
            True if the stat was removed successfully, False otherwise.
        """
        if stat_id in self._stats:
            del self._stats[stat_id]
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {stat_id: stat.value for stat_id, stat in self._stats.items()}
