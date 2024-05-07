"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from typing import Any, Mapping

from neighborly.components.stats import StatComponent
from neighborly.ecs import Component, GameObject


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
        "_incoming",
        "_outgoing",
    )

    _incoming: dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""
    _outgoing: dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""

    def __init__(
        self,
    ) -> None:
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


class Reputation(StatComponent):
    """Tracks a relationship's reputations stat."""

    __stat_name__ = "reputation"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)


class Romance(StatComponent):
    """Tracks a relationship's romance stat."""

    __stat_name__ = "romance"

    MAX_VALUE: int = 100

    def __init__(
        self,
        base_value: float = 0,
    ) -> None:
        super().__init__(base_value, (0, self.MAX_VALUE), True)
