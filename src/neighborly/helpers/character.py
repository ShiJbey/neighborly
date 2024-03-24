"""Helper functions for character operations.

"""

from __future__ import annotations

from typing import Optional

from neighborly.defs.base_types import CharacterDef, CharacterGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import CharacterLibrary


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
