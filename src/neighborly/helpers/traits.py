"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from neighborly.components.traits import Trait, Traits
from neighborly.datetime import SimDate
from neighborly.ecs import GameObject
from neighborly.libraries import TraitLibrary


def add_trait_with_id(
    gameobject: GameObject,
    trait_id: str,
    duration: int = -1,
) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait_id
        The trait.
    duration
        How long the trait should last.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """

    library = gameobject.world.resource_manager.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    return add_trait(gameobject, trait, duration)


def add_trait(
    gameobject: GameObject,
    trait: Trait,
    duration: int = -1,
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

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    success = gameobject.get_component(Traits).add_trait(trait, duration=duration)

    if success is False:
        return False

    for effect in trait.effects:
        effect.apply(gameobject)

    return True


def remove_trait_with_id(gameobject: GameObject, trait_id: str) -> bool:
    """Remove a trait from a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to remove the trait from.
    trait_id
        The trait.

    Returns
    -------
    bool
        True if the trait was removed successfully, False otherwise.
    """

    library = gameobject.world.resource_manager.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    return remove_trait(gameobject, trait)


def remove_trait(gameobject: GameObject, trait: Trait) -> bool:
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
    success = gameobject.get_component(Traits).remove_trait(trait)

    if success is False:
        return False

    for effect in trait.effects:
        effect.remove(gameobject)

    return True


def has_trait(gameobject: GameObject, trait: str) -> bool:
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
    return gameobject.get_component(Traits).has_trait(trait)


def get_time_with_trait(gameobject: GameObject, trait_id: str) -> int:
    """Get the number of months the trait has been active."""
    current_date = gameobject.world.resources.get_resource(SimDate)

    if trait_instance := gameobject.get_component(Traits).traits.get(trait_id):
        return current_date.total_months - trait_instance.timestamp.total_months
    else:
        return 0
