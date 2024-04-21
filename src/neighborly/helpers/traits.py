"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from typing import Union

from neighborly.components.relationship import Relationships
from neighborly.components.stats import StatModifier, StatModifierType
from neighborly.components.traits import Traits
from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.location import (
    add_location_preference,
    remove_location_preference,
)
from neighborly.helpers.relationship import add_social_rule, remove_social_rule
from neighborly.helpers.skills import get_skill
from neighborly.helpers.stats import get_stat
from neighborly.libraries import TraitLibrary


def add_trait(
    gameobject: GameObject,
    trait: Union[str, TraitDef],
    duration: int = -1,
    description: str = "",
) -> bool:
    """Add a trait to a GameObject.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    trait
        The ID of the trait.
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
    world = gameobject.world

    if isinstance(trait, str):
        library = world.resource_manager.get_resource(TraitLibrary)
        trait_def = library.get_definition(trait)
    else:
        trait_def = trait

    traits = gameobject.get_component(Traits)

    if trait_def.definition_id in traits.traits:
        return False

    if has_conflicting_trait(gameobject, trait_def):
        return False

    for entry in trait_def.stat_modifiers:
        get_stat(gameobject, entry.name).add_modifier(
            StatModifier(
                value=entry.value,
                modifier_type=StatModifierType[entry.modifier_type],
                source=trait_def,
            )
        )

    for entry in trait_def.skill_modifiers:
        get_skill(gameobject, entry.name).add_modifier(
            StatModifier(
                value=entry.value,
                modifier_type=StatModifierType[entry.modifier_type],
                source=trait_def,
            )
        )

    for rule_id in trait_def.social_rules:
        add_social_rule(gameobject, rule_id)

    for rule_id in trait_def.location_preferences:
        add_location_preference(gameobject, rule_id)

    traits.add_trait(
        trait_def.definition_id,
        duration=duration,
        description=description if description else trait_def.description,
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
    world = gameobject.world
    library = world.resource_manager.get_resource(TraitLibrary)
    traits = gameobject.get_component(Traits)

    if trait_id in traits.traits:

        trait = library.get_definition(trait_id)

        for entry in trait.stat_modifiers:
            get_stat(gameobject, entry.name).remove_modifiers_from_source(trait)

        for entry in trait.skill_modifiers:
            get_skill(gameobject, entry.name).remove_modifiers_from_source(trait)

        for rule_id in trait.social_rules:
            remove_social_rule(gameobject, rule_id)

        for rule_id in trait.location_preferences:
            remove_location_preference(gameobject, rule_id)

        traits.remove_trait(trait_id)

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
    return trait_id in gameobject.get_component(Traits).traits


def has_conflicting_trait(gameobject: GameObject, trait: Union[str, TraitDef]) -> bool:
    """Check if a trait conflicts with current traits.

    Parameters
    ----------
    gameobject
        The gameobject to check.
    trait
        The trait to check.

    Returns
    -------
    bool
        True if the trait conflicts with any of the current traits or if any current
        traits conflict with the given trait. False otherwise.
    """
    world = gameobject.world
    library = world.resource_manager.get_resource(TraitLibrary)

    if isinstance(trait, str):
        trait_def = library.get_definition(trait)
    else:
        trait_def = trait

    traits = gameobject.get_component(Traits)

    for instance in traits.traits.values():

        instance_trait = library.get_definition(instance.trait_id)

        if instance.trait_id in trait_def.conflicts_with:
            return True

        if trait_def.definition_id in instance_trait.conflicts_with:
            return True

    return False


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
