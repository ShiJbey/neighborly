"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

import enum
from collections import defaultdict
from typing import Any, Optional

from ordered_set import OrderedSet

from neighborly.components.shared import Modifier
from neighborly.components.stats import StatComponent
from neighborly.ecs import Component, GameObject, TagComponent
from neighborly.effects import Effect
from neighborly.preconditions import Precondition


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
        effect_descriptions = "; ".join([e.description for e in self.effects])
        precondition_descriptions = "; ".join(
            [p.description for p in self.preconditions]
        )
        return (
            f"Effect(s): {effect_descriptions}\n"
            f"Precondition(s): {precondition_descriptions}\n"
            f"Reason: {self.reason}"
        )

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
        return

    def remove(self, target: GameObject) -> None:
        return

    def apply_to_relationship(self, relationship: GameObject) -> None:
        """Apply this modifier's effects to the given relationship."""

        for effect in self.effects:
            effect.apply(relationship)

    def remove_from_relationship(self, relationship: GameObject) -> None:
        """Remove this modifier's effects from the given relationship."""

        for effect in self.effects:
            effect.remove(relationship)
