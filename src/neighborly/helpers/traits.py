"""Helper functions for working with traits.

"""

from sqlalchemy import delete

from neighborly.components.stats import StatModifier, StatModifierType
from neighborly.components.traits import TraitInstance, Traits
from neighborly.ecs import GameObject
from neighborly.helpers.skills import (
    add_skill_modifier,
    remove_skill_modifiers_from_source,
)
from neighborly.helpers.stats import (
    add_stat_modifier,
    remove_stat_modifiers_from_source,
)
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
    trait_def = library.get_definition(trait_id)

    if has_trait(gameobject, trait_id):
        return False

    if has_conflicting_traits(gameobject, trait_id):
        return False

    gameobject.get_component(Traits).instances.append(
        TraitInstance(
            trait_id=trait_id,
            description=trait_def.description,
            has_duration=duration > 0,
            duration=duration,
        )
    )

    for modifier_data in trait_def.stat_modifiers:
        add_stat_modifier(
            gameobject,
            modifier_data.name,
            StatModifier(
                value=modifier_data.value,
                modifier_type=StatModifierType[modifier_data.modifier_type],
                source=trait_def,
            ),
        )

    for modifier_data in trait_def.skill_modifiers:
        add_skill_modifier(
            gameobject,
            modifier_data.name,
            StatModifier(
                value=modifier_data.value,
                modifier_type=StatModifierType[modifier_data.modifier_type],
                source=trait_def,
            ),
        )

    return True


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
    trait_def = library.get_definition(trait_id)

    if not has_trait(gameobject, trait_id):
        return False

    for modifier in trait_def.stat_modifiers:
        remove_stat_modifiers_from_source(gameobject, modifier.name, trait_id)

    for modifier in trait_def.skill_modifiers:
        remove_skill_modifiers_from_source(gameobject, modifier.name, trait_id)

    gameobject.world.session.execute(
        delete(TraitInstance)
        .where(TraitInstance.uid == gameobject.uid)
        .where(TraitInstance.trait_id == trait_id)
    )

    gameobject.world.session.flush()

    return True


def has_trait(gameobject: GameObject, trait_id: str) -> bool:
    """Check if a GameObject has a given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait_id
        The ID of a trait.

    Returns
    -------
    bool
        True if the gameobject has the trait, False otherwise.
    """
    trait_instances = gameobject.get_component(Traits).instances

    for instance in trait_instances:
        if instance.trait_id == trait_id:
            return True

    return False


def get_trait(gameobject: GameObject, trait_id: str) -> TraitInstance:
    """Get a trait from a gameobject.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait_id
        The ID of a trait.

    Returns
    -------
    bool
        True if the gameobject has the trait, False otherwise.
    """
    trait_instances = gameobject.get_component(Traits).instances

    for instance in trait_instances:
        if instance.trait_id == trait_id:
            return instance

    raise KeyError(f"Could not find trait: {trait_id!r}")


def has_conflicting_traits(gameobject: GameObject, trait_id: str) -> bool:
    """Check if a GameObject has traits that conflict with the given trait.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait_id
        The ID of a trait.

    Returns
    -------
    bool
        True if the gameobject has conflicts, False otherwise.
    """
    library = gameobject.world.resources.get_resource(TraitLibrary)
    trait_def = library.get_definition(trait_id)
    trait_instances = gameobject.get_component(Traits).instances

    for instance in trait_instances:
        instance_def = library.get_definition(instance.trait_id)

        if trait_id in instance_def.conflicts_with:
            return True

        if instance.trait_id in trait_def.conflicts_with:
            return True

    return False
