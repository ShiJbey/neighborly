"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional

import attrs

from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect
from neighborly.preconditions.base_types import Precondition


class Relationship(Component):
    """Tags a GameObject as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner"

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
        "_incoming",
        "_outgoing",
    )

    _incoming: dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""
    _outgoing: dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""

    def __init__(self) -> None:
        super().__init__()
        self._incoming = {}
        self._outgoing = {}

    @property
    def outgoing(self) -> Mapping[GameObject, GameObject]:
        """Returns a mapping of the outgoing relationship collection."""
        return self._outgoing

    @property
    def incoming(self) -> Mapping[GameObject, GameObject]:
        """Returns a mapping of the incoming relationship collection."""
        return self._incoming

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
        if target in self._outgoing:
            raise ValueError(
                f"{self.gameobject.name} has existing outgoing relationship to "
                "target: {target.name}"
            )

        self._outgoing[target] = relationship

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
        if target in self._outgoing:
            del self._outgoing[target]
            return True

        return False

    def get_outgoing_relationship(self, target: GameObject) -> GameObject:
        """Get a relationship from one GameObject to another.

        Parameters
        ----------
        target
            The target of the relationship.

        Returns
        -------
        GameObject
            A relationship instance.
        """
        return self._outgoing[target]

    def has_outgoing_relationship(self, target: GameObject) -> bool:
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
        if owner in self._incoming:
            raise ValueError(
                f"{self.gameobject.name} has existing incoming relationship from "
                "target: {target.name}"
            )

        self._incoming[owner] = relationship

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
        if owner in self._incoming:
            del self._incoming[owner]
            return True

        return False

    def get_incoming_relationship(self, owner: GameObject) -> GameObject:
        """Get a relationship from one another GameObject to this one.

        Parameters
        ----------
        owner
            The owner of the relationship.

        Returns
        -------
        GameObject
            A relationship instance.
        """
        return self._incoming[owner]

    def has_incoming_relationship(self, owner: GameObject) -> bool:
        """Check if there is an existing relationship from the owner to this GameObject.

        Parameters
        ----------
        owner
            The owner of the relationship.

        Returns
        -------
        bool
            True if there is an existing Relationship between the GameObjects,
            False otherwise.
        """
        return owner in self._incoming

    def to_dict(self) -> dict[str, Any]:
        return {
            "outgoing": {str(k.uid): v.uid for k, v in self._outgoing.items()},
            "incoming": {str(k.uid): v.uid for k, v in self._incoming.items()},
        }

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(outgoing={self._outgoing}, "
            f"incoming={self._incoming})"
        )


@attrs.define
class SocialRule:
    """A rule that modifies a relationship depending on some preconditions."""

    preconditions: list[Precondition]
    """Conditions that need to be met to apply the rule."""
    effects: list[Effect]
    """Side-effects of the rule applied to a relationship."""
    source: Optional[object] = None
    """The object responsible for adding this rule."""

    def check_preconditions(self, relationship: GameObject) -> bool:
        """Check that a relationship passes all the preconditions."""
        return all(p(relationship) for p in self.preconditions)

    def apply(self, relationship: GameObject) -> None:
        """Apply the effects of the social rule.

        Parameters
        ----------
        relationship
            The relationship to apply the effects to.
        """
        for effect in self.effects:
            effect.apply(relationship)

    def remove(self, relationship: GameObject) -> None:
        """Remove the effects of the social rule.

        Parameters
        ----------
        relationship
            The relationship to remove the effects from.
        """
        for effect in self.effects:
            effect.remove(relationship)


class SocialRules(Component):
    """Tracks all the social rules that a GameObject abides by."""

    __slots__ = ("_rules",)

    _rules: list[SocialRule]
    """Rules applied to the owning GameObject's relationships."""

    def __init__(self) -> None:
        super().__init__()
        self._rules = []

    @property
    def rules(self) -> Iterable[SocialRule]:
        """Rules applied to the owning GameObject's relationships."""
        return self._rules

    def add_rule(self, rule: SocialRule) -> None:
        """Add a rule to the rule collection."""
        self._rules.append(rule)

    def has_rule(self, rule: SocialRule) -> bool:
        """Check if a rule is present."""
        return rule in self._rules

    def remove_rule(self, rule: SocialRule) -> bool:
        """Remove a rule from the rules collection."""
        try:
            self._rules.remove(rule)
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {}
