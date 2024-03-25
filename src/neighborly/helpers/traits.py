"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from neighborly.components.traits import Traits
from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World
from neighborly.libraries import TraitLibrary


def add_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait_id
        The ID of the trait.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    world = gameobject.world
    library = world.resource_manager.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    if gameobject.get_component(Traits).add_trait(trait):
        world.rp_db.insert(f"{gameobject.uid}.traits.{trait_id}")

        return True

    return False


def remove_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Remove a trait from a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to remove the trait from.
    trait_id
        The ID of the trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    library = gameobject.world.resource_manager.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    if gameobject.get_component(Traits).remove_trait(trait):
        gameobject.world.rp_db.delete(f"{gameobject.uid}.traits.{trait_id}")

        return True

    return False


def has_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Check if a GameObject has a given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait_id
        The ID of the trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """
    library = gameobject.world.resource_manager.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)
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
