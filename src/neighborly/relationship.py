"""Neighborly Relationship Module.

Relationships between agents are at the core of social simulation. Neighborly represents
relationships as independent GameObjects that collectively form a directed graph. This
means that each relationship has an owner and a target, and characters can have
asymmetrical feeling toward each other. All relationship GameObjects have a Relationship
component that tracks the owner and target of the relationships. They also have one or
more RelationshipStat components that track things like feelings of friendship, romance,
trust, and reputation.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, Iterator, List, Protocol, Type, Union

from ordered_set import OrderedSet

from neighborly.ecs import Component, GameObject, ISerializable, World
from neighborly.stats import ClampedStatComponent, StatComponent, Stats
from neighborly.statuses import Statuses
from neighborly.utils.event_emitter import EventEmitter


class Friendship(ClampedStatComponent):
    """Tracks platonic affinity from one character to another."""

    def __init__(self):
        super().__init__(base_value=0, max_value=100, min_value=-100)


class Romance(ClampedStatComponent):
    """Tracks romantic affinity from one character to another."""

    def __init__(self):
        super().__init__(base_value=0, max_value=100, min_value=-100)


class InteractionScore(ClampedStatComponent):
    """Tracks a score for how often characters interact in a year."""

    def __init__(self):
        super().__init__(base_value=0, max_value=100, min_value=0)


class RomanticCompatibility(StatComponent):
    def __init__(self) -> None:
        super().__init__(base_value=0)


class PlatonicCompatibility(StatComponent):
    def __init__(self) -> None:
        super().__init__(base_value=0)


class Relationship(Component, ISerializable):
    """Tags a GameObject as a relationship and tracks the owner and target."""

    __slots__ = ("_target", "_owner", "_active_rules", "_relationship_type")

    _owner: GameObject
    """Who owns this relationship."""

    _target: GameObject
    """Who is the relationship directed toward."""

    _active_rules: List[ISocialRule]
    """Social rules currently applied to this relationship."""

    _relationship_type: RelationshipType
    """Reference to the relationship type component"""

    def __init__(
        self,
        owner: GameObject,
        target: GameObject,
        relationship_type: RelationshipType,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target
        self._active_rules = []
        self._relationship_type = relationship_type

    @property
    def owner(self) -> GameObject:
        return self._owner

    @property
    def target(self) -> GameObject:
        return self._target

    @property
    def relationship_type(self):
        return self._relationship_type

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
        }

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(owner={}, target={})".format(
            self.__class__.__name__, self.owner.name, self.target.name
        )


class Relationships(Component, ISerializable):
    """Tracks all relationships associated with a GameObject.

    Notes
    -----
    This component helps build a directed graph structure within the ECS.
    """

    __slots__ = "_incoming", "_outgoing"

    _incoming: Dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""

    _outgoing: Dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""

    _on_relationship_created: EventEmitter[GameObject]
    """Emits events when a new relationship is created."""

    def __init__(self) -> None:
        super().__init__()
        self._incoming = {}
        self._outgoing = {}
        self._on_relationship_created = EventEmitter()

    @property
    def on_relationship_created(self) -> EventEmitter[GameObject]:
        return self._on_relationship_created

    def on_deactivate(self) -> None:
        # When this component's GameObject becomes inactive, deactivate all the incoming
        # and outgoing relationship GameObjects too.

        for _, relationship in self._outgoing.items():
            relationship.deactivate()

        for _, relationship in self._incoming.items():
            relationship.deactivate()

    def on_remove(self) -> None:
        # We need to destroy all incoming and outgoing relationships
        # and update the Relationship components on the owner/target
        # GameObjects.
        for target in self._outgoing.keys():
            self.remove_relationship(target)

        for owner in self._incoming.keys():
            owner.get_component(Relationships).remove_relationship(self.gameobject)

    def add_relationship(self, target: GameObject) -> GameObject:
        """
        Creates a new relationship from the subject to the target

        Parameters
        ----------
        target
            The GameObject that the Relationship is directed toward

        Returns
        -------
        GameObject
            The new relationship instance
        """
        if target in self._outgoing:
            return self._outgoing[target]

        world = self.gameobject.world

        relationship = BaseRelationship.instantiate(world, self.gameobject, target)

        self._outgoing[target] = relationship
        target.get_component(Relationships)._incoming[self.gameobject] = relationship

        self.on_relationship_created.dispatch(relationship)

        # Test all the rules in the library and apply those with passing preconditions
        social_rules = world.resource_manager.get_resource(SocialRuleLibrary)

        for rule in social_rules.iter_rules():
            if rule.check_preconditions(self.gameobject, target, relationship):
                rule.apply(self.gameobject, target, relationship)

        return relationship

    def remove_relationship(self, target: GameObject) -> bool:
        """Destroy the relationship GameObject to the target.

        Parameters
        ----------
        target
            The target of the relationship

        Returns
        -------
        bool
            Returns True if a relationship was removed. False otherwise.
        """
        if target in self._outgoing:
            relationship = self._outgoing[target]
            relationship.destroy()
            del self._outgoing[target]

            if target_relationships := target.try_component(Relationships):
                del target_relationships._incoming[self.gameobject]

            return True

        return False

    def get_relationship(
        self,
        target: GameObject,
    ) -> GameObject:
        """Get a relationship from one GameObject to another.

        This function will create a new relationship instance if one does not exist.

        Parameters
        ----------
        target
            The target of the relationship.

        Returns
        -------
        GameObject
            A relationship instance.
        """
        if target not in self._outgoing:
            return self.add_relationship(target)

        return self._outgoing[target]

    def has_relationship(self, target: GameObject) -> bool:
        """Check if there is an existing relationship from the owner to the target.

        Parameters
        ----------
        target
            The target of the relationship.

        Returns
        -------
        bool
            True if there is an existing Relationship between the GameObjects,
            False otherwise.
        """
        return target in self._outgoing

    def get_relationships_with_components(
        self, *component_types: Type[Component]
    ) -> List[GameObject]:
        """Get all the relationships with the given component types.

        Parameters
        ----------
        *component_types
            Component types to check for on relationship instances.

        Returns
        -------
        List[GameObject]
            Relationships with the given component types.
        """
        if len(component_types) == 0:
            return []

        matches: List[GameObject] = []

        for _, relationship in self._outgoing.items():
            if all([relationship.has_component(st) for st in component_types]):
                matches.append(relationship)

        return matches

    def iter_relationships(self) -> Iterator[tuple[GameObject, GameObject]]:
        return self._outgoing.items().__iter__()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outgoing": {str(k.uid): v.uid for k, v in self._outgoing.items()},
            "incoming": {str(k.uid): v.uid for k, v in self._incoming.items()},
        }

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "{}(outgoing={}, incoming={})".format(
            self.__class__.__name__, self._outgoing, self._incoming
        )


class ISocialRule(Protocol):
    """An interface for rules that define how characters feel about each other.

    Social rules check if characters and their relationship meet certain conditions.
    Then they apply stat modifiers and statuses to the relationship GameObject.
    """

    @property
    @abstractmethod
    def is_active(self) -> bool:
        """Return True if this rule is active."""
        raise NotImplementedError

    @abstractmethod
    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        """Check if a relationship passes the preconditions for this rule to apply.

        Parameters
        ----------
        owner
            The relationship's owner.
        target
            The relationship's target.
        relationship
            A relationship from one gameobject to another.

        Returns
        -------
        bool
            True if the relationship passes, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        """Apply the effects of this rule.

        Parameters
        ----------
        owner
            The relationship's owner.
        target
            The relationship's target.
        relationship
            A relationship from one gameobject to another.
        """
        raise NotImplementedError

    @abstractmethod
    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        """Remove the effects of this rule.

        Parameters
        ----------
        owner
            The relationship's owner.
        target
            The relationship's target.
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
    """Collection of all registered rule instances."""

    def __init__(self) -> None:
        self._rules = OrderedSet([])

    def add_rule(self, rule: ISocialRule) -> None:
        """Register a social rule.

        Parameters
        ----------
        rule
            The rule to register.
        """
        self._rules.append(rule)

    def iter_rules(self) -> Iterator[ISocialRule]:
        """Return an iterator to the registered social rules."""
        return self._rules.__iter__()


class RelationshipType(Component, ABC):
    @classmethod
    @abstractmethod
    def instantiate(
        cls, world: World, owner: GameObject, target: GameObject, **kwargs: Any
    ) -> GameObject:
        """Create new residence instance.

        Parameters
        ----------
        world
            The world instance to spawn into.
        owner
            The GameObject that owns the relationship
        target
            The GameObject that is the target of the relationship
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        GameObject
            The residence instance.
        """
        raise NotImplementedError


class BaseRelationship(RelationshipType):
    base_components: ClassVar[Dict[Union[str, Type[Component]], Dict[str, Any]]] = {
        Friendship: {},
        Romance: {},
        InteractionScore: {},
        PlatonicCompatibility: {},
        RomanticCompatibility: {},
    }

    @classmethod
    def instantiate(
        cls, world: World, owner: GameObject, target: GameObject, **kwargs: Any
    ) -> GameObject:
        relationship = world.gameobject_manager.spawn_gameobject(
            components={
                Stats: {},
                Statuses: {},
                **BaseRelationship.base_components,
            },
            name=f"Rel({owner.name} -> {target.name})",
        )

        relationship_type = relationship.add_component(cls)

        relationship.add_component(
            Relationship,
            owner=owner,
            target=target,
            relationship_type=relationship_type,
        )

        return relationship


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
    return owner.get_component(Relationships).add_relationship(target)


def get_relationship(
    owner: GameObject,
    target: GameObject,
) -> GameObject:
    """Get a relationship from one GameObject to another.

    This function will create a new instance of a relationship if one does not exist.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    GameObject
        A relationship instance.
    """
    return owner.get_component(Relationships).get_relationship(target)


def has_relationship(owner: GameObject, target: GameObject) -> bool:
    """Check if there is an existing relationship from the owner to the target.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    bool
        True if there is an existing Relationship between the GameObjects,
        False otherwise.
    """
    return owner.get_component(Relationships).has_relationship(target)


def get_relationships_with_components(
    gameobject: GameObject, *component_types: Type[Component]
) -> List[GameObject]:
    """Get all the relationships with the given component types.

    Parameters
    ----------
    gameobject
        The character to check for relationships on.
    *component_types
        Component types to check for on relationship instances.

    Returns
    -------
    List[GameObject]
        Relationships with the given component types.
    """
    return gameobject.get_component(Relationships).get_relationships_with_components(
        *component_types
    )
