"""Helper functions for character operations.

"""

from __future__ import annotations

from typing import Any

from neighborly.defs.base_types import CharacterDef
from neighborly.ecs import GameObject, World
from neighborly.libraries import CharacterLibrary


def create_character(world: World, definition_id: str, **kwargs: Any) -> GameObject:
    """Create a new character instance."""
    character_library = world.resource_manager.get_resource(CharacterLibrary)

    character_def = character_library.get_definition(definition_id)

    character = world.gameobject_manager.spawn_gameobject()
    character.metadata["definition_id"] = definition_id

    character_def.initialize(character, **kwargs)

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
