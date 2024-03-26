"""Helper functions for managing GameObject Traits.

"""

from __future__ import annotations

from neighborly.components.relationship import Relationships
from neighborly.components.stats import StatModifier, StatModifierType
from neighborly.components.traits import Trait, Traits
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
    trait = library.get_trait(trait_id).get_component(Trait)

    if gameobject.get_component(Traits).add_trait(trait):

        trait_def = trait.definition

        for entry in trait_def.stat_modifiers:
            get_stat(gameobject, entry.name).add_modifier(
                StatModifier(
                    value=entry.value,
                    modifier_type=StatModifierType[entry.modifier_type],
                    source=trait,
                )
            )

        for entry in trait_def.skill_modifiers:
            get_skill(gameobject, entry.name).stat.add_modifier(
                StatModifier(
                    value=entry.value,
                    modifier_type=StatModifierType[entry.modifier_type],
                    source=trait,
                )
            )

        for rule_id in trait.definition.social_rules:
            add_social_rule(gameobject, rule_id)

        for rule_id in trait.definition.location_preferences:
            add_location_preference(gameobject, rule_id)

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
    traits = gameobject.get_component(Traits)

    if trait_id in gameobject.get_component(Traits).traits:

        trait = traits.traits[trait_id].trait

        for entry in trait.definition.stat_modifiers:
            get_stat(gameobject, entry.name).remove_modifiers_from_source(trait)

        for entry in trait.definition.skill_modifiers:
            get_skill(gameobject, entry.name).stat.remove_modifiers_from_source(trait)

        for rule_id in trait.definition.social_rules:
            remove_social_rule(gameobject, rule_id)

        for rule_id in trait.definition.location_preferences:
            remove_location_preference(gameobject, rule_id)

        del traits.traits[trait_id]

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
    return trait_id in gameobject.get_component(Traits).traits


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
