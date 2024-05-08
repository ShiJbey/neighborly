"""Helper functions for business operations.

"""

from __future__ import annotations

from neighborly.ecs import GameObject, World
from neighborly.libraries import BusinessLibrary


def create_business(
    world: World,
    definition_id: str,
) -> GameObject:
    """Create a new business instance.

    Parameters
    ----------
    world
        The World instance to spawn the business into.
    definition_id
        The ID of the business definition to instantiate

    Returns
    -------
    GameObject
        The instantiated business.
    """
    library = world.resource_manager.get_resource(BusinessLibrary)

    return library.factory.create_business(world, definition_id)
