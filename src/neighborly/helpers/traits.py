"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from typing import Union

from neighborly.components.relationship import Relationships
from neighborly.components.traits import Trait, Traits
from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World
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
        return gameobject.get_component(Traits).add_trait(
            library.get_trait(trait), description=description, duration=duration
        )

    return gameobject.get_component(Traits).add_trait(
        trait, description=description, duration=duration
    )


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

        return gameobject.get_component(Traits).remove_trait(library.get_trait(trait))

    return gameobject.get_component(Traits).remove_trait(trait)


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
    if isinstance(trait, str):
        library = gameobject.world.resource_manager.get_resource(TraitLibrary)

        return gameobject.get_component(Traits).has_trait(library.get_trait(trait))

    return gameobject.get_component(Traits).has_trait(trait)


def register_trait_def(world: World, definition: TraitDef) -> None:
    """Add a new trait definition for the TraitLibrary.

    Parameters
    ----------
    world
        The world instance containing the trait library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(TraitLibrary).add_definition(definition)


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
