"""Neighborly Relationship Module.

Relationships between agents are at the core of social simulation. Neighborly represents relationships as independent
GameObjects that collectively form a directed graph. This means that each relationship has an owner and a target, and
characters can have asymmetrical feeling toward each other. All relationship GameObjects have a Relationship component
that tracks the owner and target of the relationships. They also have one or more RelationshipStat components that
track things like feelings of friendship, romance, trust, and reputation.

"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from enum import IntEnum
from typing import Any, Dict, Iterator, List, Optional, Protocol, Type, TypeVar

import attrs
from ordered_set import OrderedSet

from neighborly.core.ecs import Active, Component, GameObject, ISerializable
from neighborly.core.status import (
    IStatus,
    Statuses,
    add_status,
    has_status,
    remove_status,
)


class RelationshipStat(Component, ISerializable, ABC):
    """A scalar value representing a facet of a relationship such as reputation, trust, or attraction."""

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

    _modifiers: List[IRelationshipModifier]
    """Active stat modifiers."""

    def __init__(self, base_value: int = 0, min_value: int = -100, max_value: int = 100) -> None:
        super().__init__()
        self._min_value = min_value
        self._max_value = max_value
        self._base_value = base_value
        self._raw_value = 0
        self._value = 0
        self._modifiers = []
        self._is_dirty: bool = True

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
        if self._is_dirty:
            self._recalculate_value()
        return self._value

    def add_modifier(self, modifier: IRelationshipModifier) -> None:
        """Add a modifier to the stat."""
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)

    def remove_modifier(self, modifier: IRelationshipModifier) -> None:
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
        """Recalculate the various values since the last change"""

        self._raw_value: int = self.base_value

        for modifier in self._modifiers:
            if modifier.modifier_type == ModifierType.Flat:
                self._raw_value += modifier.value
            elif modifier.modifier_type == ModifierType.Percent:
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


class Friendship(RelationshipStat):
    pass


class Romance(RelationshipStat):
    pass


class InteractionScore(RelationshipStat):
    def __init__(self):
        super().__init__(max_value=100, min_value=0)


class IRelationshipStatus(IStatus, ABC):
    pass


class ModifierType(IntEnum):
    Flat = 0
    Percent = 1


class IRelationshipModifier(Protocol):

    @property
    @abstractmethod
    def value(self) -> int:
        """Get the value of this modifier."""
        raise NotImplementedError

    @property
    @abstractmethod
    def modifier_type(self) -> ModifierType:
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
class RelationshipModifier(IRelationshipModifier):
    """Stat modifiers applied to relationship stat components."""

    _value: int
    """The amount to modify the stat."""

    _modifier_type: ModifierType
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
    def modifier_type(self) -> ModifierType:
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
        modifier_type: ModifierType,
        order: Optional[int] = None,
        source: Optional[object] = None
    ) -> RelationshipModifier:
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


class Relationship(Component, ISerializable):
    __slots__ = (
        "_target",
        "_owner",
        "_active_rules"
    )

    _owner: GameObject
    """Who owns this relationship."""

    _target: GameObject
    """Who is the relationship directed toward."""

    _active_rules: List[ISocialRule]
    """Social rules currently applied to this relationship."""

    def __init__(self, owner: GameObject, target: GameObject) -> None:
        super().__init__()
        self._owner = owner
        self._target = target
        self._active_rules = []

    @property
    def owner(self) -> GameObject:
        return self._owner

    @property
    def target(self) -> GameObject:
        return self._target

    def add_rule(self, rule: ISocialRule) -> None:
        """Apply a social rule to the relationship."""
        self._active_rules.append(rule)

    def remove_rule(self, rule: ISocialRule) -> None:
        """Remove a social rule from the relationship."""
        self._active_rules.remove(rule)

    def iter_active_rules(self) -> Iterator[ISocialRule]:
        """Return iterator to active rules."""
        return self._active_rules.__iter__()

    def clear_active_rules(self) -> None:
        """Clear all active rules."""
        self._active_rules.clear()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "owner": self.owner.uid,
            "target": self.target.uid,
            "rules": [str(rule) for rule in self._active_rules],
        }

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(owner={}, target={}, modifiers={})".format(
            self.__class__.__name__,
            self.owner,
            self.target,
            self._active_rules,
        )


class RelationshipManager(Component, ISerializable):
    """Tracks all relationships associated with a GameObject.

    Notes
    -----
    This component helps build a directed graph structure within the ECS.
    """

    __slots__ = "incoming", "outgoing"

    incoming: Dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""

    outgoing: Dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""

    def __init__(self) -> None:
        super().__init__()
        self.incoming = {}
        self.outgoing = {}

    def add_incoming(self, owner: GameObject, relationship: GameObject) -> None:
        """
        Add a new incoming relationship

        Parameters
        ----------
        owner
            The ID of the owner
        relationship
            The ID of the relationship
        """
        self.incoming[owner] = relationship

    def add_outgoing(self, target: GameObject, relationship: GameObject) -> None:
        """
        Add a new outgoing relationship

        Parameters
        ----------
        target
            The ID of the target
        relationship
            The ID of the relationship
        """
        self.outgoing[target] = relationship

    def to_dict(self) -> Dict[str, Any]:
        return {str(k.uid): v.uid for k, v in self.outgoing.items()}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(outgoing={}, incoming={})".format(
            self.__class__.__name__, self.outgoing, self.incoming
        )


class ISocialRule(Protocol):
    """An interface for rules that define how characters feel about each other using status effects and modifiers."""

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Return True if this rule is active."""
        raise NotImplementedError

    @abstractmethod
    def check_preconditions(self, owner: GameObject, target: GameObject, relationship: GameObject) -> bool:
        """Check if a relationship passes the preconditions for this rule to apply.

        Parameters
        ----------
        owner
            The relationship's owner
        target
            The relationship's target
        relationship
            A relationship from one gameobject to another.

        Returns
        -------
        bool
            True if the relationship passes, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def apply(self, owner: GameObject, target: GameObject, relationship: GameObject) -> None:
        """Apply the effects of this rule.

        Parameters
        ----------
        owner
            The relationship's owner
        target
            The relationship's target
        relationship
            A relationship from one gameobject to another.
        """
        raise NotImplementedError

    @abstractmethod
    def remove(self, owner: GameObject, target: GameObject, relationship: GameObject) -> None:
        """Remove the effects of this rule.

        Parameters
        ----------
        owner
            The relationship's owner
        target
            The relationship's target
        relationship
            A relationship from one gameobject to another.
        """
        raise NotImplementedError


class SocialRule(ISocialRule, ABC):
    """An abstract base class for social rules to inherit from."""

    __slots__ = "_active"

    _active: bool
    """Is this rule active."""

    @property
    def is_active(self) -> bool:
        return self._active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._active = value


class SocialRuleLibrary:
    """Repository of social rules to use during the simulation."""

    __slots__ = "_rules"

    _rules: OrderedSet[ISocialRule]
    """Collection of all registered rule instances"""

    def __init__(self) -> None:
        self._rules = OrderedSet([])

    def add_rule(self, rule: ISocialRule) -> None:
        """
        Register a social rule

        Parameters
        ----------
        rule
            The rule to register
        """
        self._rules.append(rule)

    def iter_rules(self) -> Iterator[ISocialRule]:
        """Return an iterator to the registered social rules"""
        return self._rules.__iter__()


_RST = TypeVar("_RST", bound=IRelationshipStatus)


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
    rule_library = owner.world.resource_manager.get_resource(SocialRuleLibrary)

    if target in relationship_manager.outgoing:
        return relationship_manager.outgoing[target]

    relationship = owner.world.gameobject_manager.instantiate_prefab("relationship")
    relationship.add_component(Relationship(owner, target))
    relationship.add_component(Statuses())
    relationship.add_component(Active())

    relationship.name = f"Rel({owner} -> {target})"

    owner.get_component(RelationshipManager).outgoing[target] = relationship

    target.get_component(RelationshipManager).incoming[owner] = relationship

    owner.add_child(relationship)

    # Test all the rules in the library and apply those with passing preconditions
    for rule in rule_library.iter_rules():
        if rule.check_preconditions(owner, target, relationship):
            rule.apply(owner, target, relationship)

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
    if target not in subject.get_component(RelationshipManager).outgoing:
        return add_relationship(subject, target)

    return subject.get_component(RelationshipManager).outgoing[target]


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
    return target in subject.get_component(RelationshipManager).outgoing


def add_relationship_status(
    subject: GameObject, target: GameObject, status: IRelationshipStatus
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
    status_type: Type[IRelationshipStatus],
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
    *status_type: Type[IRelationshipStatus],
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
    subject: GameObject, *status_types: Type[IRelationshipStatus]
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
    relationship_manager = subject.get_component(RelationshipManager)
    matches: List[GameObject] = []
    for _, relationship in relationship_manager.outgoing.items():
        if all([relationship.has_component(st) for st in status_types]):
            matches.append(relationship)
    return matches
