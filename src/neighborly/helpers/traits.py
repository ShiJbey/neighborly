"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from typing import Union

from neighborly.components.relationship import Relationship, Relationships
from neighborly.components.traits import Trait, Traits, TraitType
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.helpers.relationship import get_relationship
from neighborly.libraries import TraitLibrary


def add_trait(
    gameobject: GameObject,
    trait: Union[str, Trait],
    duration: int = -1,
    description: str = "",
) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait
        The trait.
    duration
        How long the trait should last.
    description
        Override the default trait description.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """

    if isinstance(trait, str):
        library = gameobject.world.resource_manager.get_resource(TraitLibrary)
        trait_obj = library.get_trait(trait)
    else:
        trait_obj = trait

    if trait_obj.trait_type != TraitType.AGENT:
        raise TypeError(f"{trait_obj.definition_id} is not an agent trait.")

    success = gameobject.get_component(Traits).add_trait(
        trait_obj, description=description, duration=duration
    )

    if success is False:
        return False

    for effect in trait_obj.effects:
        effect.apply(gameobject)

    outgoing_relationships = gameobject.get_component(Relationships).outgoing
    for relationship in outgoing_relationships.values():
        for effect in trait_obj.outgoing_relationship_effects:
            effect.apply(relationship)

    incoming_relationships = gameobject.get_component(Relationships).incoming
    for relationship in incoming_relationships.values():
        for effect in trait_obj.outgoing_relationship_effects:
            effect.apply(relationship)

    return True


def add_relationship_trait(
    owner: GameObject,
    target: GameObject,
    trait: Union[str, Trait],
    duration: int = -1,
    description: str = "",
) -> bool:
    """Add a trait to a relationship.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.
    trait
        The trait.
    duration
        How long the trait should last.
    description
        Override the default trait description.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    relationship = get_relationship(owner, target)

    if isinstance(trait, str):
        library = relationship.world.resource_manager.get_resource(TraitLibrary)
        trait_obj = library.get_trait(trait)
    else:
        trait_obj = trait

    if trait_obj.trait_type != TraitType.RELATIONSHIP:
        raise TypeError(f"{trait_obj.definition_id} is not a relationship trait.")

    success = relationship.get_component(Traits).add_trait(
        trait_obj,
        description=description if description else trait_obj.description,
        duration=duration,
    )

    if success is False:
        return False

    relationship_owner = relationship.get_component(Relationship).owner
    relationship_target = relationship.get_component(Relationship).target

    for effect in trait_obj.effects:
        effect.apply(relationship)

    for effect in trait_obj.owner_effects:
        effect.apply(relationship_owner)

    for effect in trait_obj.outgoing_relationship_effects:
        effect.apply(relationship_target)

    return True


def remove_trait(gameobject: GameObject, trait: Union[str, Trait]) -> bool:
    """Remove a trait from a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to remove the trait from.
    trait
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """

    if isinstance(trait, str):
        library = gameobject.world.resource_manager.get_resource(TraitLibrary)
        trait_obj = library.get_trait(trait)
    else:
        trait_obj = trait

    success = gameobject.get_component(Traits).remove_trait(trait_obj)

    if success is False:
        return False

    for effect in trait_obj.effects:
        effect.remove(gameobject)

    outgoing_relationships = gameobject.get_component(Relationships).outgoing
    for relationship in outgoing_relationships.values():
        for effect in trait_obj.outgoing_relationship_effects:
            effect.remove(relationship)

    incoming_relationships = gameobject.get_component(Relationships).incoming
    for relationship in incoming_relationships.values():
        for effect in trait_obj.outgoing_relationship_effects:
            effect.remove(relationship)

    return True


def remove_relationship_trait(
    owner: GameObject, target: GameObject, trait: Union[str, Trait]
) -> bool:
    """Remove a trait from a relationship.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.
    trait
        The trait.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    relationship = get_relationship(owner, target)

    if isinstance(trait, str):
        library = relationship.world.resource_manager.get_resource(TraitLibrary)
        trait_obj = library.get_trait(trait)
    else:
        trait_obj = trait

    success = relationship.get_component(Traits).remove_trait(trait_obj)

    if success is False:
        return False

    relationship_owner = relationship.get_component(Relationship).owner
    relationship_target = relationship.get_component(Relationship).target

    for effect in trait_obj.effects:
        effect.remove(relationship)

    for effect in trait_obj.owner_effects:
        effect.remove(relationship_owner)

    for effect in trait_obj.outgoing_relationship_effects:
        effect.remove(relationship_target)

    return True


def has_trait(gameobject: GameObject, trait: Union[str, Trait]) -> bool:
    """Check if a GameObject has a given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    # if isinstance(trait, str):
    #     library = gameobject.world.resource_manager.get_resource(TraitLibrary)

    #     return gameobject.get_component(Traits).has_trait(library.get_trait(trait))

    return gameobject.get_component(Traits).has_trait(trait)


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

    for _, relationship in gameobject.get_component(Relationships).outgoing.items():
        if all(has_trait(relationship, trait) for trait in traits):
            matches.append(relationship)

    return matches


def get_time_with_trait(gameobject: GameObject, trait: Union[str, Trait]) -> int:
    """Get the number of months the trait has been active."""
    current_date = gameobject.world.resources.get_resource(SimDate)

    if isinstance(trait, str):
        trait_id = trait
    else:
        trait_id = trait.definition_id

    if trait_instance := gameobject.get_component(Traits).traits.get(trait_id):
        return current_date.total_months - trait_instance.timestamp.total_months
    else:
        return 0
