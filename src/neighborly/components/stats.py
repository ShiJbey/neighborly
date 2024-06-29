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
from abc import ABC, abstractmethod
from typing import Any, ClassVar, Iterable, Optional, Protocol

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
    _modifiers: list[IStatModifier]
    """Active stat modifiers."""
    _min_value: float
    """The minimum score the overall stat is clamped to."""
    _max_value: float
    """The maximum score the overall stat is clamped to."""
    _is_discrete: bool
    """Should the final calculated stat value be converted to an int."""

    def __init__(
        self,
        base_value: float = 0,
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

    @property
    def is_bounded(self) -> bool:
        """Returns True if the stat has min and max values."""
        return self._is_bounded

    @property
    def bounds(self) -> tuple[float, float]:
        """Get the min and max values of this stat."""
        return self._min_value, self._max_value

    @property
    def is_discrete(self) -> bool:
        """Returns True if the stat has min and max values."""
        return self._is_discrete

    def add_modifier(self, modifier: IStatModifier) -> None:
        """Add a modifier to the stat."""
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.get_modifier_type())
        self._is_dirty = True

    def remove_modifier(self, modifier: IStatModifier) -> bool:
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
            if modifier.get_source() == source:
                self._is_dirty = True
                did_remove = True
                self._modifiers.remove(modifier)

        return did_remove

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stat to a dict for data analysis."""
        return {
            "value": self.value,
        }

    def recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""

        final_value: float = self._base_value
        sum_percent_add: float = 0.0

        for i, modifier in enumerate(self._modifiers):
            if modifier.get_modifier_type() == StatModifierType.FLAT:
                final_value += modifier.get_value()

            elif modifier.get_modifier_type() == StatModifierType.PERCENT:
                sum_percent_add += modifier.get_value()

                if (
                    i + 1 >= len(self._modifiers)
                    or self._modifiers[i + 1].get_modifier_type()
                    != StatModifierType.PERCENT
                ):
                    final_value *= 1 + sum_percent_add
                    sum_percent_add = 0

        self._value = final_value

        if self._is_bounded:
            self._value = max(self._min_value, min(self._max_value, self._value))

        if self._is_discrete:
            self._value = float(math.trunc(self._value))

        self._is_dirty = False

    @property
    def normalized(self) -> float:
        """Get the normalized value from 0.0 to 1.0."""
        if self.is_bounded:
            return (self.value - self._min_value) / (self._max_value - self._min_value)

        raise ValueError("Cannot calculate normalized value of an unbound stat.")

    def __str__(self) -> str:
        return (
            f"Stat(value={self.value!r}, base={self.base_value!r}, "
            f"max={self._max_value!r}, min={self._min_value!r}, "
            f"modifiers={self._modifiers!r})"
        )

    def __repr__(self) -> str:
        return (
            f"Stat(value={self.value!r}, base={self.base_value!r}, "
            f"max={self._max_value!r}, min={self._min_value!r}, "
            f"modifiers={self._modifiers!r})"
        )


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    FLAT = 100
    """Adds a constant value to the base value."""

    PERCENT = 200
    """Additively stacks percentage increases on a modified stat."""


class IStatModifier(Protocol):
    """Stat modifiers provide buffs and de-buffs to the value of stat components.

    Modifiers are applied to stats in ascending-priority-order. So, stats with lower
    orders are added first.
    """

    @abstractmethod
    def get_value(self) -> float:
        """Get the value of the modifier."""

        raise NotImplementedError()

    @abstractmethod
    def get_modifier_type(self) -> StatModifierType:
        """Get modifier type."""

        raise NotImplementedError()

    @abstractmethod
    def get_source(self) -> Optional[object]:

        raise NotImplementedError()


class StatComponent(Component, ABC):
    """A component that represents a numerical stat associated with a GameObject."""

    __stat_name__: ClassVar[str] = ""

    __slots__ = ("stat",)

    stat: Stat
    """stat data"""

    def __init__(
        self,
        base_value: float = 0,
        bounds: Optional[tuple[float, float]] = None,
        is_discrete: bool = False,
    ) -> None:
        super().__init__()

        if not self.__stat_name__:
            raise ValueError(
                f"Please specify __stat_name__ class attribute for {type(self)}."
            )

        self.stat = Stat(base_value=base_value, bounds=bounds, is_discrete=is_discrete)

    @property
    def stat_name(self) -> str:
        """The name associated with this stat."""
        return self.__stat_name__

    def on_add(self) -> None:
        self.gameobject.get_component(Stats).add_stat(self)

    def on_remove(self) -> None:
        if stats_comp := self.gameobject.try_component(Stats):
            stats_comp.remove_stat(self.stat_name)

    def to_dict(self) -> dict[str, Any]:
        return {"value": self.stat.value}


class Stats(Component):
    """Tracks all the various stats for a GameObject."""

    __slots__ = ("_stats",)

    _stats: dict[str, StatComponent]
    """Map of Stat IDs to Stat components."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self._stats = {}

    @property
    def stats(self) -> Iterable[StatComponent]:
        """Stat instances."""
        return self._stats.values()

    def add_stat(
        self,
        stat: StatComponent,
    ) -> None:
        """Add a new stat.

        Parameters
        ----------
        stat
            A stat component instance.
        """
        stat_id = stat.stat_name
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
        return self._stats[stat_id].stat

    def remove_stat(self, stat_id: str) -> bool:
        """Remove a stat.

        Parameters
        ----------
        stat_id
            A string ID associated with a stat.

        Returns
        -------
        bool
            True is successful, False otherwise.
        """
        if stat_id in self._stats:

            del self._stats[stat_id]

            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {}


class Lifespan(StatComponent):
    """Tracks a GameObject's lifespan."""

    __stat_name__ = "lifespan"

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, 999_999), True)


class Fertility(StatComponent):
    """Tracks a GameObject's fertility."""

    __stat_name__ = "fertility"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Stewardship(StatComponent):
    """Tracks a GameObject's stewardship."""

    __stat_name__ = "stewardship"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Sociability(StatComponent):
    """Tracks a GameObject's sociability."""

    __stat_name__ = "sociability"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Discipline(StatComponent):
    """Tracks a GameObject's discipline."""

    __stat_name__ = "discipline"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)
