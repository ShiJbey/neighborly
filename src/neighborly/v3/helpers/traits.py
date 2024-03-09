from typing import Union

from neighborly.libraries import TraitLibrary
from neighborly.v3.components.traits import Trait, Traits
from neighborly.v3.ecs import GameObject, System, World


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
    library = world.resources.get_resource(TraitLibrary)
    trait = library.get_trait(trait_id)

    return gameobject.get_component(Traits).add_trait(trait.get_component(Trait))


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
    trait = library.get_trait(trait_id)

    if has_trait(gameobject, trait_id):
        # Remove stat and skill modifiers
        pass

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


class TickTraitsSystem(System):
    def on_update(self, world: World) -> None:
        for _, (traits,) in world.get_components((Traits,)):
            trait_instances = list(traits)

            for instance in trait_instances:
                if instance.has_duration:
                    instance.duration -= 1

                    if instance.duration <= 0:
                        remove_trait(traits.gameobject, instance.trait)
