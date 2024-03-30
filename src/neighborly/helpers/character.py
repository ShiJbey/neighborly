"""Helper functions for character operations.

"""

from __future__ import annotations

from typing import Optional, cast

from neighborly.components.character import Character
from neighborly.defs.base_types import CharacterDef, CharacterGenOptions, SpeciesDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.libraries import CharacterLibrary, TraitLibrary


def create_character(
    world: World, definition_id: str, options: Optional[CharacterGenOptions] = None
) -> GameObject:
    """Create a new character instance.

    Parameters
    ----------
    world
        The simulation's World instance.
    definition_id
        The ID of the definition to instantiate.
    options
        Generation parameters.

    Returns
    -------
    GameObject
        An instantiated character.
    """
    character_library = world.resource_manager.get_resource(CharacterLibrary)

    character_def = character_library.get_definition(definition_id)

    options = options if options else CharacterGenOptions()

    character = character_def.instantiate(world, options)

    return character


def set_species(gameobject: GameObject, species_id: str) -> bool:
    """the species of the character.

    Parameters
    ----------
    gameobject
        The gameobject to add the trait to.
    species
        The ID of the species.

    Return
    ------
    bool
        True if the trait was added successfully, False if already present or
        if the trait conflict with existing traits.
    """
    world = gameobject.world

    character = gameobject.get_component(Character)

    if character.species:
        remove_trait(gameobject, character.species.definition_id)

    if add_trait(gameobject, species_id):
        library = world.resources.get_resource(TraitLibrary)
        character.species = cast(SpeciesDef, library.get_definition(species_id))
        return True

    return False


def register_character_def(world: World, definition: CharacterDef) -> None:
    """Add a new character definition for the CharacterLibrary.

    Parameters
    ----------
    world
        The world instance containing the character library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(CharacterLibrary).add_definition(definition)
    world.resource_manager.get_resource(CharacterLibrary).add_definition(definition)
