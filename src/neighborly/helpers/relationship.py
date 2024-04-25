"""Relationship System Helper Functions.

"""

from neighborly.components.beliefs import AgentBeliefs, AppliedBeliefs, Belief
from neighborly.components.relationship import (
    Compatibility,
    InteractionScore,
    Relationship,
    Relationships,
    Reputation,
    Romance,
    RomanticCompatibility,
)
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.ecs import GameObject
from neighborly.libraries import BeliefLibrary


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
    if has_relationship(owner, target):
        return get_relationship(owner, target)

    relationship = owner.world.gameobject_manager.spawn_gameobject()

    relationship.add_component(Relationship(relationship, owner=owner, target=target))
    relationship.add_component(Stats(relationship))
    relationship.add_component(Traits(relationship))
    relationship.add_component(Reputation(relationship))
    relationship.add_component(Romance(relationship))
    relationship.add_component(Compatibility(relationship))
    relationship.add_component(RomanticCompatibility(relationship))
    relationship.add_component(InteractionScore(relationship))

    relationship.name = f"{owner.name} -> {target.name}"

    owner.get_component(Relationships).add_outgoing_relationship(target, relationship)
    target.get_component(Relationships).add_incoming_relationship(owner, relationship)

    reevaluate_relationship(relationship.get_component(Relationship))

    return relationship


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
    if has_relationship(owner, target):
        return owner.get_component(Relationships).get_outgoing_relationship(target)

    return add_relationship(owner, target)


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
    return owner.get_component(Relationships).has_outgoing_relationship(target)


def destroy_relationship(owner: GameObject, target: GameObject) -> bool:
    """Destroy the relationship GameObject to the target.

    Parameters
    ----------
    owner
        The owner of the relationship
    target
        The target of the relationship

    Returns
    -------
    bool
        Returns True if a relationship was removed. False otherwise.
    """
    if has_relationship(owner, target):
        relationship = get_relationship(owner, target)
        owner.get_component(Relationships).remove_outgoing_relationship(target)
        target.get_component(Relationships).remove_incoming_relationship(owner)
        owner.world.rp_db.delete(f"{relationship.uid}")
        relationship.destroy()
        return True

    return False


def add_belief(agent: GameObject, belief_id: str) -> None:
    """Add a belief to an agent.

    Parameters
    ----------
    agent
        The agent that will hold the belief.
    belief_id
        The ID of the belief to add.
    """
    library = agent.world.resource_manager.get_resource(BeliefLibrary)
    held_beliefs = agent.get_component(AgentBeliefs)

    if held_beliefs.has_belief(belief_id):
        # Add the belief to increment the internal belief reference counter.
        held_beliefs.add_belief(belief_id)
        return

    belief = library.get_belief(belief_id)
    held_beliefs.add_belief(belief_id)

    relationships = agent.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        if belief.check_preconditions(relationship):
            belief.apply_effects(relationship)


def remove_belief(agent: GameObject, belief_id: str) -> None:
    """Remove a belief from an agent.

    Parameters
    ----------
    agent
        The agent to modify.
    belief_id
        The ID of the belief to remove.
    """
    library = agent.world.resource_manager.get_resource(BeliefLibrary)
    held_beliefs = agent.get_component(AgentBeliefs)

    if not held_beliefs.has_belief(belief_id):
        return

    held_beliefs.remove_belief(belief_id)

    # If the agent still has the belief, then there is something else like a trait
    # that still requires this belief to be present.
    if held_beliefs.has_belief(belief_id):
        return

    # If the belief is no longer held by the agent, remove the effects from all
    # outgoing relationships.

    belief = library.get_belief(belief_id)

    relationships = agent.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        applied_beliefs = relationship.get_component(AppliedBeliefs)

        if applied_beliefs.has_belief(belief_id):
            applied_beliefs.remove_belief(belief_id)
            belief.remove_effects(relationship)


def reevaluate_relationship(relationship: Relationship) -> None:
    """Reevaluate beliefs for a given relationship."""

    library = relationship.gameobject.world.resource_manager.get_resource(BeliefLibrary)

    applied_beliefs = relationship.gameobject.get_component(AppliedBeliefs)

    # Check that existing rules still pass their preconditions

    beliefs_to_remove: list[Belief] = []

    for belief_id in applied_beliefs.beliefs:
        belief = library.get_belief(belief_id)
        if belief.check_preconditions(relationship.gameobject) is False:
            beliefs_to_remove.append(belief)

    for belief in beliefs_to_remove:
        applied_beliefs.remove_belief(belief.belief_id)
        belief.remove_effects(relationship.gameobject)

    # Check if any global beliefs should be applied

    for belief_id in library.global_beliefs:
        belief = library.get_belief(belief_id)
        if belief.check_preconditions(relationship.gameobject):
            applied_beliefs.add_belief(belief_id)
            belief.apply_effects(relationship.gameobject)


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(Relationships)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()
