"""Neighborly Stats Model.

This module contains Neighborly's implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Neighborly provides class
interfaces to implement various statuses as components, as well as modifiers that change
stat values based on things like active traits and statuses.

"""
from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, List, Optional, Protocol

import attrs

from neighborly import Component
from neighborly.core.ecs import ISerializable


class StatComponent(Component, ISerializable, ABC):
    """A stat such as strength, reputation, or attraction."""

    __slots__ = (
        "_min_value",
        "_max_value",
        "_base_value",
        "_value",
        "_modifiers",
        "_is_dirty",
    )

    _min_value: int
    """The minimum score the overall stat is clamped to."""

    _max_value: int
    """The maximum score the overall stat is clamped to."""

    _base_value: int
    """The base score for this stat used by modifiers."""

    _raw_Value: int
    """The non-clamped score of this stat with all modifiers applied."""

    _value: int
    """The final score of the stat clamped between the min and max values."""

    _modifiers: List[IStatModifier]
    """Active stat modifiers."""

    def __init__(self, base_value: int, min_value: int, max_value: int) -> None:
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value
        self._base_value = base_value
        self._raw_value = base_value
        self._value = base_value
        self._modifiers = []
        self._is_dirty: bool = False

    @property
    def base_value(self) -> int:
        """Get the base value of the relationship stat."""
        return self._base_value

    @base_value.setter
    def base_value(self, value: int) -> None:
        """Set the base value of the relationship stat."""
        self._base_value = value
        self._is_dirty = True

    @property
    def value(self) -> int:
        """Get the final calculated value of the stat."""
        if self._is_dirty:
            self._recalculate_value()
        return self._value

    def add_modifier(self, modifier: IStatModifier) -> None:
        """Add a modifier to the stat."""
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)

    def remove_modifier(self, modifier: IStatModifier) -> None:
        """Remove a modifier from the stat."""
        self._modifiers.remove(modifier)

    def remove_modifiers_from_source(self, source: object) -> None:
        """Remove all modifiers applied from the given source."""
        self._modifiers = [
            modifier for modifier in self._modifiers if modifier.source != source
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
        }

    def _recalculate_value(self) -> None:
        """Recalculate the stat's value due to a previous change."""

        self._raw_value: int = self.base_value

        for modifier in self._modifiers:
            if modifier.modifier_type == StatModifierType.Flat:
                self._raw_value += modifier.value
            elif modifier.modifier_type == StatModifierType.Percent:
                self._raw_value = round(self._raw_value * (1 + modifier.value))

        self._raw_value = math.ceil(
            max(self._min_value, min(self._max_value, self._raw_value))
        )

        self._is_dirty = False

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(value={}, base={}, max={}, min={})".format(
            self.__class__.__name__,
            self.value,
            self.base_value,
            self._max_value,
            self._min_value,
        )


class StatModifierType(IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    Flat = 0
    Percent = 1


class IStatModifier(Protocol):
    """Protocol specifying methods for stat modifiers."""

    @property
    @abstractmethod
    def value(self) -> int:
        """Get the value of this modifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def modifier_type(self) -> StatModifierType:
        """Get how the modifier value is applied."""
        raise NotImplementedError

    @property
    @abstractmethod
    def order(self) -> int:
        """Get the priority of the modifier when calculating final stat values."""
        raise NotImplementedError

    @property
    @abstractmethod
    def source(self) -> Optional[object]:
        """Get source of the modifier."""
        raise NotImplementedError


@attrs.define(frozen=True, slots=True)
class StatModifier(IStatModifier):
    """A stat modifier.

    Stat modifiers provide buffs and de-buffs to stat components.
    """

    _value: int
    """The amount to modify the stat."""

    _modifier_type: StatModifierType
    """How the modifier value is applied."""

    _order: int
    """The priority of this modifier when calculating final stat values."""

    _source: Optional[object]
    """The source of the modifier (for debugging purposes)."""

    @property
    def value(self) -> int:
        """Get the value of this modifier."""
        return self._value

    @property
    def modifier_type(self) -> StatModifierType:
        """Get how the modifier value is applied."""
        return self._modifier_type

    @property
    def order(self) -> int:
        """Get the priority of the modifier when calculating final stat values."""
        return self._order

    @property
    def source(self) -> Optional[object]:
        """Get source of the modifier."""
        return self._source

    @classmethod
    def create(
        cls,
        value: int,
        modifier_type: StatModifierType,
        order: Optional[int] = None,
        source: Optional[object] = None
    ) -> StatModifier:
        return cls(
            value=value,
            modifier_type=modifier_type,
            order=order if order is not None else int(modifier_type),
            source=source
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "modifier_type": self.modifier_type.name,
            "order": self.order,
            "source": str(self.source) if self.source is not None else ""
        }
