from __future__ import annotations

import dataclasses
import math
from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional, Protocol, Tuple, Type, TypeVar

from neighborly.core.ecs import Active, Component, GameObject, GameObjectFactory
from neighborly.core.ecs.ecs import ISerializable
from neighborly.core.status import (
    StatusComponent,
    StatusManager,
    add_status,
    has_status,
    remove_status,
)
from neighborly.core.time import SimDateTime


def lerp(a: float, b: float, f: float) -> float:
    return (a * (1.0 - f)) + (b * f)


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


class Relationship(Component, ISerializable):
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


class RelationshipManager(Component, ISerializable):
    """Tracks all relationships associated with a GameObject.

    Notes
    -----
    This component helps build a directed graph structure within the ECS.
    """

    __slots__ = "incoming", "outgoing"

    incoming: Dict[int, int]
    """GameObject ID of relationship owners mapped to the Relationship's ID."""

    outgoing: Dict[int, int]
    """GameObject ID of relationship owners mapped to the Relationship's ID."""

    def __init__(self) -> None:
        super().__init__()
        self.incoming = {}
        self.outgoing = {}

    def add_incoming(self, owner: int, relationship: int) -> None:
        """
        Add a new incoming relationship

        Parameters
        ----------
        owner
            The ID of the owner of the relationship
        relationship
            The ID of the relationship
        """
        self.incoming[owner] = relationship

    def add_outgoing(self, target: int, relationship: int) -> None:
        """
        Add a new outgoing relationship

        Parameters
        ----------
        target
            The ID of the target of the relationship
        relationship
            The ID of the relationship
        """
        self.outgoing[target] = relationship

    def to_dict(self) -> Dict[str, Any]:
        return {str(k): v for k, v in self.outgoing.items()}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(outgoing={}, incoming={})".format(
            self.__class__.__name__, self.outgoing, self.incoming
        )


class ISocialRule(Protocol):
    """SocialRules define how characters should treat each other"""

    def __call__(
        self, subject: GameObject, target: GameObject
    ) -> Optional[Dict[Type[RelationshipFacet], int]]:
        """
        Calculate relationship modifiers of a subject toward a target

        Parameters
        ----------
        subject
            The owner of the relationship
        target
            The GameObject that we are evaluating the subjects feelings toward

        Returns
        -------
        Dict[Type[RelationshipFacet], int] or None
            Optionally returns a dict mapping relationship facet types to int modifiers
            that should be applied to those facets based on some precondition(s)
        """
        raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class SocialRuleInfo:
    """Information about a social rule."""

    rule: ISocialRule
    """The callable function that implements the rule."""

    description: str = ""
    """A text description of the rule."""


class SocialRules:
    """Repository of social rules to use during the simulation."""

    _rules: List[SocialRuleInfo] = []

    @classmethod
    def add(cls, rule: ISocialRule, description: str) -> None:
        """
        Register a social rule

        Parameters
        ----------
        rule
            The rule to register
        description
            A text description of the rule
        """
        cls._rules.append(SocialRuleInfo(rule, description))

    @classmethod
    def iter_rules(cls) -> Iterator[SocialRuleInfo]:
        """Return an iterator to the registered social rules"""
        return cls._rules.__iter__()


_RST = TypeVar("_RST", bound=RelationshipStatus)


def add_relationship(owner: GameObject, target: GameObject) -> GameObject:
    """
    Creates a new relationship from the subject to the target

    Parameters
    ----------
    owner
        The GameObject that owns the relationship
    target
        The GameObject that the Relationship is directed toward

    Returns
    -------
    GameObject
        The new relationship instance
    """
    relationship_manager = owner.get_component(RelationshipManager)
    world = owner.world

    if target.uid in relationship_manager.outgoing:
        return world.get_gameobject(relationship_manager.outgoing[target.uid])

    relationship = GameObjectFactory.instantiate(world, "relationship")
    relationship.add_component(Relationship(owner.uid, target.uid))
    relationship.add_component(StatusManager())
    relationship.add_component(Active())

    relationship.name = f"Rel({owner} -> {target})"

    owner.get_component(RelationshipManager).outgoing[target.uid] = relationship.uid

    target.get_component(RelationshipManager).incoming[owner.uid] = relationship.uid

    owner.add_child(relationship)

    evaluate_social_rules(relationship, owner, target)

    return relationship


def get_relationship(
    subject: GameObject,
    target: GameObject,
) -> GameObject:
    """
    Get a relationship toward another entity

    Parameters
    ----------
    subject
        The owner of the relationship
    target
        The character the relationship is directed toward

    Returns
    -------
    GameObject
        The relationship instance toward the other entity
    """
    if target.uid not in subject.get_component(RelationshipManager).outgoing:
        return add_relationship(subject, target)

    return subject.world.get_gameobject(
        subject.get_component(RelationshipManager).outgoing[target.uid]
    )


def has_relationship(subject: GameObject, target: GameObject) -> bool:
    """
    Check if there is an existing relationship from the subject to the target

    Parameters
    ----------
    subject
        The GameObject to check for a relationship instance on
    target
        The GameObject to check is the target of an existing relationship instance

    Returns
    -------
    bool
        True if there is an existing Relationship instance with the
        target as the target, False otherwise.
    """
    return target.uid in subject.get_component(RelationshipManager).outgoing


def add_relationship_status(
    subject: GameObject, target: GameObject, status: RelationshipStatus
) -> None:
    """
    Add a relationship status to the given character

    Parameters
    ----------
    subject
        The character to add the relationship status to
    target
        The character the relationship status is directed toward
    status
        The core component of the status
    """
    relationship = get_relationship(subject, target)
    status.set_created(subject.world.get_resource(SimDateTime))
    add_status(relationship, status)


def get_relationship_status(
    subject: GameObject,
    target: GameObject,
    status_type: Type[_RST],
) -> _RST:
    """
    Get a relationship status from the subject to the target
    of a given type

    Parameters
    ----------
    subject
        The character to add the relationship status to
    target
        The character that is the target of the status
    status_type
        The type of the status
    """

    relationship = get_relationship(subject, target)
    return relationship.get_component(status_type)


def remove_relationship_status(
    subject: GameObject,
    target: GameObject,
    status_type: Type[RelationshipStatus],
) -> None:
    """
    Remove a relationship status to the given character

    Parameters
    ----------
    subject
        The character to add the relationship status to
    target
        The character that is the target of the status
    status_type
        The type of the relationship status to remove
    """

    relationship = get_relationship(subject, target)
    remove_status(relationship, status_type)


def has_relationship_status(
    subject: GameObject,
    target: GameObject,
    *status_type: Type[RelationshipStatus],
) -> bool:
    """
    Check if a relationship between characters has a certain status type

    Parameters
    ----------
    subject
        The character to add the relationship status to
    target
        The character that is the target of the status
    *status_type
        The type of the relationship status to remove

    Returns
    -------
    bool
        True if relationship has a given status, False otherwise.
    """

    relationship = get_relationship(subject, target)
    return all([has_status(relationship, s) for s in status_type])


def get_relationships_with_statuses(
    subject: GameObject, *status_types: Type[RelationshipStatus]
) -> List[GameObject]:
    """Get all the relationships with the given status types

    Parameters
    ----------
    subject
        The character to check for relationships on
    *status_types
        Status types to check for on relationship instances

    Returns
    -------
    List[GameObject]
        Relationships with the given status types
    """
    world = subject.world
    relationship_manager = subject.get_component(RelationshipManager)
    matches: List[GameObject] = []
    for _, rel_id in relationship_manager.outgoing.items():
        relationship = world.get_gameobject(rel_id)
        if all([relationship.has_component(st) for st in status_types]):
            matches.append(relationship)
    return matches


def evaluate_social_rules(
    relationship: GameObject, owner: GameObject, target: GameObject
) -> None:
    """
    Modify the relationship to reflect active social rules

    Parameters
    ----------
    relationship
        The relationship to modify
    owner
        The owner of the relationship
    target
        The target of the relationship
    """

    relationship.get_component(Relationship).clear_modifiers()

    for rule_info in SocialRules.iter_rules():
        modifier = rule_info.rule(owner, target)
        if modifier:
            relationship.get_component(Relationship).add_modifier(
                RelationshipModifier(description=rule_info.description, values=modifier)
            )
