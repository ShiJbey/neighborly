"""Relationship System Helper Functions.

"""

from typing import Optional

from neighborly.components.beliefs import HeldBeliefs
from neighborly.components.relationship import (
    Relationship,
    RelationshipModifiers,
    Relationships,
    Reputation,
    Romance,
)
from neighborly.components.shared import Modifiers
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.ecs import Event, GameObject
from neighborly.effects.modifiers import RelationshipModifier, RelationshipModifierDir
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

    relationship.add_component(Relationship(owner=owner, target=target))
    relationship.add_component(Stats())
    relationship.add_component(Traits())
    relationship.add_component(Reputation())
    relationship.add_component(Romance())
    relationship.add_component(Modifiers())

    relationship.name = f"[{owner.name} -> {target.name}]"

    owner.get_component(Relationships).add_outgoing_relationship(target, relationship)
    target.get_component(Relationships).add_incoming_relationship(owner, relationship)

    reevaluate_relationship(relationship.get_component(Relationship))

    relationship.world.events.dispatch_event(
        Event("relationship-added", world=relationship.world, relationship=relationship)
    )

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
    held_beliefs = agent.get_component(HeldBeliefs)

    if held_beliefs.has_belief(belief_id):
        # Add the belief to increment the internal belief reference counter.
        held_beliefs.add_belief(belief_id)
        return

    belief = library.get_belief(belief_id)
    held_beliefs.add_belief(belief_id)
    add_relationship_modifier(
        agent,
        RelationshipModifier(
            direction=RelationshipModifierDir.OUTGOING,
            description=belief.description,
            preconditions=belief.preconditions,
            effects=belief.effects,
            source=belief,
            reason=f"{belief.description}",
        ),
    )

    relationships = agent.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        reevaluate_relationship(relationship.get_component(Relationship))


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
    held_beliefs = agent.get_component(HeldBeliefs)

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

    remove_relationship_modifiers_from_source(agent, belief)


def reevaluate_relationships(gameobject: GameObject) -> None:
    """Reevaluate all relationships for a GameObject."""

    for relationship in gameobject.get_component(Relationships).outgoing.values():
        reevaluate_relationship(relationship.get_component(Relationship))

    for relationship in gameobject.get_component(Relationships).outgoing.values():
        reevaluate_relationship(relationship.get_component(Relationship))


def reevaluate_relationship(relationship: Relationship) -> None:
    """Reevaluate modifiers for a given relationship."""

    # Loop through all the owners modifiers looking for relationship modifiers.
    # Remove the effects of all that you find and re-evaluate if they pass
    owner_modifiers = relationship.owner.get_component(RelationshipModifiers)
    for modifier in owner_modifiers.modifiers:
        modifier.remove_from_relationship(relationship.gameobject)

        if modifier.direction != RelationshipModifierDir.OUTGOING:
            continue

        if modifier.check_preconditions(relationship.gameobject):
            modifier.apply_to_relationship(relationship.gameobject)

    # Do the same as the above with the targets relationship modifiers, but this
    # time look for incoming modifiers
    target_modifiers = relationship.target.get_component(RelationshipModifiers)
    for modifier in target_modifiers.modifiers:
        modifier.remove_from_relationship(relationship.gameobject)

        if modifier.direction != RelationshipModifierDir.INCOMING:
            continue

        if modifier.check_preconditions(relationship.gameobject):
            modifier.apply_to_relationship(relationship.gameobject)


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(Relationships)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()


def get_relationships_with_traits(
    gameobject: GameObject, *traits: str
) -> list[GameObject]:
    """Get all the relationships with the given tags.

    Parameters
    ----------
    gameobject
        The character to check.
    *traits
        The trait IDs to check for on relationships.

    Returns
    -------
    list[GameObject]
        Relationships with the given traits.
    """
    matches: list[GameObject] = []

    relationships = gameobject.get_component(Relationships).outgoing.values()

    for relationship in relationships:
        relationship_traits = relationship.get_component(Traits)
        if all(relationship_traits.has_trait(t) for t in traits):
            matches.append(relationship)

    return matches


def add_relationship_modifier(
    target: GameObject, modifier: RelationshipModifier
) -> None:
    """Add a modifier to a GameObject."""

    target.get_component(RelationshipModifiers).add_modifier(modifier)

    reevaluate_relationships(target)


def remove_relationship_modifier(
    target: GameObject, modifier: RelationshipModifier
) -> bool:
    """Remove a modifier from a GameObject.

    Returns
    -------
    bool
        True if removed successfully.
    """

    success = target.get_component(RelationshipModifiers).remove_modifier(modifier)

    if success:
        if modifier.direction == RelationshipModifierDir.OUTGOING:
            for relationship in target.get_component(Relationships).outgoing.values():
                modifier.remove_from_relationship(relationship)
        else:
            for relationship in target.get_component(Relationships).incoming.values():
                modifier.remove_from_relationship(relationship)

        modifier.remove(target)

    return success


def remove_relationship_modifiers_from_source(
    target: GameObject, source: Optional[object]
) -> bool:
    """Remove all modifiers from a given source.

    Returns
    -------
    bool
        True if any modifiers were removed
    """
    modifier_manager = target.get_component(RelationshipModifiers)

    modifiers_to_remove = [
        m for m in modifier_manager.modifiers if m.get_source() == source
    ]

    for m in modifiers_to_remove:
        remove_relationship_modifier(target, m)

    return len(modifiers_to_remove) > 0
