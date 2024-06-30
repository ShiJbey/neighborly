"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ordered_set import OrderedSet

from neighborly.components.stats import StatComponent
from neighborly.ecs import Component, GameObject, TagComponent
from neighborly.effects.modifiers import RelationshipModifier


class Relationship(Component):
    """Tags a GameObject as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner", "active_rules"

    _owner: GameObject
    """Who owns this relationship."""
    _target: GameObject
    """Who is the relationship directed toward."""

    def __init__(
        self,
        owner: GameObject,
        target: GameObject,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target

    @property
    def owner(self) -> GameObject:
        """Get the owner of the relationship."""
        return self._owner

    @property
    def target(self) -> GameObject:
        """Get the target of the relationship."""
        return self._target

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner.uid,
            "target": self.target.uid,
        }

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(owner={self.owner.name}, "
            f"target={self.target.name})"
        )


class Relationships(Component):
    """Tracks all relationships associated with a GameObject.

    Notes
    -----
    This component helps build a directed graph structure within the ECS.
    """

    __slots__ = (
        "incoming",
        "outgoing",
    )

    incoming: dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""
    outgoing: dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.incoming = {}
        self.outgoing = {}

    def add_outgoing_relationship(
        self, target: GameObject, relationship: GameObject
    ) -> None:
        """Add a new relationship to a target.

        Parameters
        ----------
        target
            The GameObject that the Relationship is directed toward.
        relationship
            The relationship.
        """
        if target in self.outgoing:
            raise ValueError(
                f"{self.gameobject.name} has existing outgoing relationship to "
                "target: {target.name}"
            )

        self.outgoing[target] = relationship

    def remove_outgoing_relationship(self, target: GameObject) -> bool:
        """Remove the relationship GameObject to the target.

        Parameters
        ----------
        target
            The target of the relationship

        Returns
        -------
        bool
            Returns True if a relationship was removed. False otherwise.
        """
        if target in self.outgoing:
            del self.outgoing[target]
            return True

        return False

    def add_incoming_relationship(
        self, owner: GameObject, relationship: GameObject
    ) -> None:
        """Add a new relationship to a target.

        Parameters
        ----------
        owner
            The GameObject owns the relationship.
        relationship
            The relationship.
        """
        if owner in self.incoming:
            raise ValueError(
                f"{self.gameobject.name} has existing incoming relationship from "
                "target: {target.name}"
            )

        self.incoming[owner] = relationship

    def remove_incoming_relationship(self, owner: GameObject) -> bool:
        """Remove the relationship GameObject to the owner.

        Parameters
        ----------
        owner
            The owner of the relationship

        Returns
        -------
        bool
            Returns True if a relationship was removed. False otherwise.
        """
        if owner in self.incoming:
            del self.incoming[owner]
            return True

        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "outgoing": {str(k.uid): v.uid for k, v in self.outgoing.items()},
            "incoming": {str(k.uid): v.uid for k, v in self.incoming.items()},
        }

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(outgoing={self.outgoing}, "
            f"incoming={self.incoming})"
        )


class Reputation(StatComponent):
    """Tracks a relationship's reputations stat."""

    __stat_name__ = "reputation"

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (-50, 50), True)


class Romance(StatComponent):
    """Tracks a relationship's romance stat."""

    __stat_name__ = "romance"

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (-50, 50), True)


class RelationshipModifiers(Component):
    """Manages all the modifiers attached to a GameObject."""

    __slots__ = ("modifiers",)

    modifiers: list[RelationshipModifier]
    """All modifiers within the manager."""

    def __init__(self) -> None:
        super().__init__()
        self.modifiers = []

    def add_modifier(self, modifier: RelationshipModifier) -> None:
        """Add a modifier to the manager."""
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier: RelationshipModifier) -> bool:
        """Remove a modifier from the manager.

        Returns
        -------
        bool
            True if successfully removed.
        """
        try:
            self.modifiers.remove(modifier)
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {}


class KeyRelations(Component):
    """Cache of key people in a character's life, indexed by relationship type."""

    __slots__ = ("relations",)

    relations: defaultdict[str, OrderedSet[GameObject]]
    """Relationship types mapped to target of the relationship (another character)."""

    def __init__(self) -> None:
        super().__init__()
        self.relations = defaultdict(lambda: OrderedSet([]))

    def set(self, key: str, character: GameObject) -> None:
        """Set a character in the cache"""
        self.relations[key].add(character)

    def unset(self, key: str, character: GameObject) -> bool:
        """Unset a character in the cache."""
        try:
            self.relations[key].remove(character)
            return True
        except KeyError:
            return False

    def get(self, *keys: str) -> OrderedSet[GameObject]:
        """Get relations indexed under the given keys."""
        all_sets = [self.relations[k] for k in keys]

        return all_sets[0].intersection(*all_sets[1:])

    def to_dict(self) -> dict[str, Any]:
        return {}


class IsSingle(TagComponent):
    """Tags a character as not being in any romantic relationships."""


class IsMarried(TagComponent):
    """Tags a character as being married."""
