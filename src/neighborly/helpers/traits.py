from typing import Union

from neighborly.components.skills import Skills
from neighborly.components.stats import Stats
from neighborly.components.traits import Trait, Traits
from neighborly.ecs import GameObject
from neighborly.libraries import TraitLibrary


def add_trait(gameobject: GameObject, trait_id: str, duration: int = -1) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait_id
        The ID of the trait.
    duration
        The amount of time to apply the trait for.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    world = gameobject.world
    library = world.resources.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id).get_component(Trait)

    if gameobject.get_component(Traits).add_trait(trait, duration=duration):

        stats = gameobject.get_component(Stats)
        for modifier in trait.stat_modifiers:
            stats.get_stat(modifier.name).remove_modifiers_from_source(trait)

        skills = gameobject.get_component(Skills)
        for modifier in trait.skill_modifiers:
            skills.get_skill(modifier.name).remove_modifiers_from_source(trait)

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
    library = gameobject.world.resources.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id).get_component(Trait)

    if has_trait(gameobject, trait_id):
        # Remove stat and skill modifiers
        stats = gameobject.get_component(Stats)
        for modifier in trait.stat_modifiers:
            stats.get_stat(modifier.name).remove_modifiers_from_source(trait)

        skills = gameobject.get_component(Skills)
        for modifier in trait.skill_modifiers:
            skills.get_skill(modifier.name).remove_modifiers_from_source(trait)

    return gameobject.get_component(Traits).remove_trait(trait_id)


def has_trait(gameobject: GameObject, trait: Union[str, Trait]) -> bool:
    """Check if a GameObject has a given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait
        The ID of a trait or a trait object.

    Returns
    -------
    bool
        True if the gameobject has the trait, False otherwise.
    """
    if isinstance(trait, Trait):
        return gameobject.get_component(Traits).has_trait(trait.definition_id)

    return gameobject.get_component(Traits).has_trait(trait)
