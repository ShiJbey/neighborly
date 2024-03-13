"""Helper functions for character operations.

"""

from __future__ import annotations

from neighborly.defs.base_types import CharacterDef, CharacterGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import CharacterLibrary


def create_character(world: World, options: CharacterGenOptions) -> GameObject:
    """Create a new character object.

    Parameters
    ----------
    world
        The world instance to spawn the character into.
    options
        Various creation settings.

    Returns
    -------
    GameObject
        The new character object.
    """

    return (
        world.resources.get_resource(CharacterLibrary)
        .get_definition(options.definition_id)
        .instantiate(world, options)
    )


def register_character_def(world: World, definition: CharacterDef) -> None:
    """Add a new character definition for the CharacterLibrary.

    Parameters
    ----------
    world
        The world instance containing the character library.
    definition
        The definition to add.
    """
    world.resources.get_resource(CharacterLibrary).add_definition(definition)
