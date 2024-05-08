"""Helper functions for character operations.

"""

from __future__ import annotations

from neighborly.ecs import GameObject, World
from neighborly.libraries import CharacterLibrary


def create_character(world: World, definition_id: str) -> GameObject:
    """Create a new character instance.

    Parameters
    ----------
    world
        The simulation's World instance.
    definition_id
        The ID of the definition to instantiate.

    Returns
    -------
    GameObject
        An instantiated character.
    """
    character_library = world.resource_manager.get_resource(CharacterLibrary)

    return character_library.factory.create_character(world, definition_id)


def create_child(birthing_parent: GameObject, other_parent: GameObject) -> GameObject:
    """Create instance of a child from two parents.

    Parameters
    ----------
    birthing_parent
        The parent who gave birth to the child.
    other_parent
        The other parent contributing genetics to the child.

    Returns
    -------
    GameObject
        The new child.
    """
    character_library = birthing_parent.world.resource_manager.get_resource(
        CharacterLibrary
    )

    return character_library.child_factory.create_child(birthing_parent, other_parent)
