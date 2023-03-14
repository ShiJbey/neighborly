from __future__ import annotations

import math
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type, Union

from neighborly.core.ecs import Component, GameObject
from neighborly.core.status import StatusComponent


def lerp(a: float, b: float, f: float) -> float:
    return (a * (1.0 - f)) + (b * f)


class RelationshipNotFound(Exception):
    """Exception raised when trying to access a relationship that does not exist"""

    __slots__ = "subject", "target", "message"

    def __init__(self, subject: str, target: str) -> None:
        super(Exception, self).__init__(target)
        self.subject: str = subject
        self.target: str = target
        self.message: str = (
            f"Could not find relationship between ({self.subject}) and ({self.target})"
        )

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return "{}(subject={}, target={})".format(
            self.__class__.__name__, self.subject, self.target
        )


class IncrementCounter:
    def __init__(self, value: Tuple[int, int] = (0, 0)) -> None:
        self._value: Tuple[int, int] = value

        if self._value[0] < 0 or self._value[1] < 0:
            raise ValueError("Values of an IncrementTuple may not be less than zero.")

    @property
    def increments(self) -> int:
        """Return the number of increments"""
        return self._value[0]

    @property
    def decrements(self) -> int:
        """Return the number of decrements"""
        return self._value[1]

    def __iadd__(self, value: int) -> IncrementCounter:
        """Overrides += operator for relationship stats"""
        if value > 0:
            self._value = (self._value[0] + value, self._value[1])
        if value < 0:
            self._value = (self._value[0], self._value[1] + abs(value))
        return self

    def __add__(self, other: IncrementCounter) -> IncrementCounter:
        return IncrementCounter(
            (self.increments + other.increments, self.decrements + other.decrements)
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "({}, {})".format(self.increments, self.decrements * -1)


class RelationshipFacet(Component, ABC):
    """
    A scalar value quantifying a relationship facet from one entity to another
    """

    __slots__ = (
        "_min_value",
        "_max_value",
        "_raw_value",
        "_clamped_value",
        "_normalized_value",
        "_base",
        "_from_modifiers",
        "_is_dirty",
    )

    def __init__(self, min_value: int = -100, max_value: int = 100) -> None:
        super().__init__()
        self._min_value: int = min_value
        self._max_value: int = max_value
        self._raw_value: int = 0
        self._clamped_value: int = 0
        self._normalized_value: float = 0.5
        self._base: IncrementCounter = IncrementCounter()
        self._from_modifiers: IncrementCounter = IncrementCounter()
        self._is_dirty: bool = False

    def get_base(self) -> IncrementCounter:
        """Return the base value for increments on this relationship stat"""
        return self._base

    def set_base(self, value: Tuple[int, int]) -> None:
        """Set the base value for decrements on this relationship stat"""
        self._base = IncrementCounter(value)

    def set_modifier(self, modifier: Optional[IncrementCounter]) -> None:
        if modifier is None:
            self._from_modifiers = IncrementCounter()
        else:
            self._from_modifiers = modifier
        self._is_dirty = True

    def get_raw_value(self) -> int:
        """Return the raw value of this relationship stat"""
        if self._is_dirty:
            self._recalculate_values()
        return self._raw_value

    def get_value(self) -> int:
        """Return the scaled value of this relationship stat between the max and min values"""
        if self._is_dirty:
            self._recalculate_values()
        return self._clamped_value

    def get_normalized_value(self) -> float:
        """Return the normalized value of this relationship stat on the interval [0.0, 1.0]"""
        if self._is_dirty:
            self._recalculate_values()
        return self._normalized_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw": self.get_raw_value(),
            "scaled": self.get_value(),
            "normalized": self.get_normalized_value(),
        }

    def _recalculate_values(self) -> None:
        """Recalculate the various values since the last change"""
        combined_increments = self._base + self._from_modifiers

        self._raw_value = (
            combined_increments.increments - combined_increments.decrements
        )

        total_changes = combined_increments.increments + combined_increments.decrements

        if total_changes == 0:
            self._normalized_value = 0.5
        else:
            self._normalized_value = (
                float(combined_increments.increments) / total_changes
            )

        self._clamped_value = math.ceil(
            max(self._min_value, min(self._max_value, self._raw_value))
        )

        self._is_dirty = False

    def increment(self, value: int) -> None:
        self._base += value
        self._is_dirty = True

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(value={}, norm={}, raw={},  max={}, min={})".format(
            self.__class__.__name__,
            self.get_value(),
            self.get_normalized_value(),
            self.get_raw_value(),
            self._max_value,
            self._min_value,
        )


class Friendship(RelationshipFacet):
    pass


class Romance(RelationshipFacet):
    pass


class InteractionScore(RelationshipFacet):
    pass


class RelationshipStatus(StatusComponent, ABC):
    pass


@dataclass
class RelationshipModifier:
    description: str
    values: Dict[Type[RelationshipFacet], int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "values": {rs_type.__name__: val for rs_type, val in self.values.items()},
        }


class Relationship(Component):
    __slots__ = (
        "_modifiers",
        "_target",
        "_owner",
    )

    def __init__(self, owner: int, target: int) -> None:
        super().__init__()
        self._owner: int = owner
        self._target: int = target
        self._modifiers: List[RelationshipModifier] = []

    @property
    def owner(self) -> int:
        return self._owner

    @property
    def target(self) -> int:
        return self._target

    def add_modifier(self, modifier: RelationshipModifier) -> None:
        self._modifiers.append(modifier)

    def iter_modifiers(self) -> Iterator[RelationshipModifier]:
        return self._modifiers.__iter__()

    def clear_modifiers(self) -> None:
        self._modifiers.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner,
            "target": self.target,
            "modifiers": [m.to_dict() for m in self._modifiers],
        }

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, modifiers={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self._modifiers,
        )


class RelationshipManager(Component):
    """Tracks all relationships associated with a GameObject

    Attributes
    ----------
    relationships: Dict[int, int]
        GameObject ID of relationship targets mapped to the ID of the
        GameObjects with the relationship data
    """

    __slots__ = "relationships"

    def __init__(self) -> None:
        super().__init__()
        self.relationships: Dict[int, int] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {str(k): v for k, v in self.relationships.items()}

    def targets(self) -> Iterator[int]:
        return self.relationships.__iter__()

    def __setitem__(
        self, key: Union[int, GameObject], value: Union[int, GameObject]
    ) -> None:
        self.relationships[int(key)] = int(value)

    def __getitem__(self, key: Union[int, GameObject]) -> int:
        return self.relationships[int(key)]

    def __contains__(self, item: Union[int, GameObject]):
        return int(item) in self.relationships

    def __iter__(self) -> Iterator[int]:
        return self.relationships.values().__iter__()

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self.relationships)
