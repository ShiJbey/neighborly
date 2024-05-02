"""Neighborly Belief System Components.

The belief system replaces the old social rule system as an additional mechanism for
agents to determine how they feel about each other. Beliefs have the same general
structure as social rules. However, they are only applied to outgoing relationships.
Thus they represent  model beliefs that one agent has that affect how they feel
about another agent.

"""

from collections import defaultdict
from typing import Any, Iterable

from ordered_set import OrderedSet

from neighborly.components.relationship import Relationship
from neighborly.ecs import Component, GameObject
from neighborly.effects.base_types import Effect
from neighborly.preconditions.base_types import Precondition


class Belief:
    """A cultural or personal belief that affects how an agent feels about another.

    Beliefs are applied to an agents outgoing relationship's depending on its associated
    preconditions.
    """

    __slots__ = (
        "belief_id",
        "description",
        "preconditions",
        "owner_preconditions",
        "target_preconditions",
        "effects",
        "is_global",
    )

    belief_id: str
    """A unique ID for the belief."""
    description: str
    """A text description of this belief."""
    preconditions: list[Precondition]
    """Preconditions checked against a relationship GameObject."""
    effects: list[Effect]
    """Effects to apply to a relationship GameObject."""
    is_global: bool
    """(Used by library) Is this belief held by all agents."""

    def __init__(
        self,
        belief_id: str,
        description: str,
        preconditions: list[Precondition],
        effects: list[Effect],
        is_global: bool,
    ) -> None:
        self.belief_id = belief_id
        self.description = description
        self.preconditions = preconditions
        self.effects = effects
        self.is_global = is_global

    def check_preconditions(self, relationship: GameObject) -> bool:
        """Check the preconditions against the given relationship."""

        relationship_comp = relationship.get_component(Relationship)
        owner = relationship_comp.owner
        target = relationship_comp.target

        for precondition in self.preconditions:
            if (
                precondition.check(
                    {"relationship": relationship, "owner": owner, "target": target}
                )
                is False
            ):
                return False

        return True

    def apply_effects(self, relationship: GameObject) -> None:
        """Apply this belief's effects to the given relationship."""

        for effect in self.effects:
            effect.apply(relationship)

    def remove_effects(self, relationship: GameObject) -> None:
        """Remove this belief's effects from the given relationship."""

        for effect in self.effects:
            effect.remove(relationship)


class AgentBeliefs(Component):
    """Tracks all the beliefs held by an agent."""

    __slots__ = ("_beliefs",)

    _beliefs: defaultdict[str, int]
    """Belief IDs mapped to reference counts."""

    def __init__(self, gameobject: GameObject) -> None:
        super().__init__(gameobject)
        self._beliefs = defaultdict(lambda: 0)

    def get_all(self) -> Iterable[str]:
        """Get all beliefs held."""

        return self._beliefs

    def add_belief(self, belief_id: str) -> None:
        """Add a belief collection."""

        self._beliefs[belief_id] += 1

    def has_belief(self, belief_id: str) -> bool:
        """Check if a belief is held locally by the agent."""

        return belief_id in self._beliefs

    def remove_belief(self, belief_id: str) -> bool:
        """Remove a belief from the collection."""

        if belief_id in self._beliefs:
            self._beliefs[belief_id] -= 1

            if self._beliefs[belief_id] <= 0:
                del self._beliefs[belief_id]

            return True

        return False

    def to_dict(self) -> dict[str, Any]:

        return {"beliefs": [b for b in self._beliefs]}


class AppliedBeliefs(Component):
    """Tracks all beliefs applied to a relationship GameObject."""

    __slots__ = ("beliefs",)

    beliefs: OrderedSet[str]
    """A collection of belief IDs."""

    def __init__(self, gameobject: GameObject) -> None:
        super().__init__(gameobject)
        self.beliefs = OrderedSet([])

    def get_all(self) -> Iterable[str]:
        """Get the IDs of all beliefs applied to the relationship."""

        return self.beliefs

    def add_belief(self, belief_id: str) -> None:
        """Add a belief to the collection."""

        self.beliefs.add(belief_id)

    def has_belief(self, belief_id: str) -> bool:
        """Check if a belief has been applied to the relationship."""

        return belief_id in self.beliefs

    def remove_belief(self, belief_id: str) -> bool:
        """Remove a belief."""

        if belief_id in self.beliefs:
            self.beliefs.remove(belief_id)
            return True

        return False

    def to_dict(self) -> dict[str, Any]:

        return {"beliefs": [b for b in self.beliefs]}
