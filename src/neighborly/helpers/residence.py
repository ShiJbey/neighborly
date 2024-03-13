"""Helper functions for managing residences and residents.

"""

from __future__ import annotations

from neighborly.defs.base_types import ResidenceDef, ResidenceGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import ResidenceLibrary


def create_residence(
    world: World, district: GameObject, options: ResidenceGenOptions
) -> GameObject:
    """Create a new residence instance."""

    return (
        world.resources.get_resource(ResidenceLibrary)
        .get_definition(options.definition_id)
        .instantiate(world, district, options)
    )


def register_residence_def(world: World, definition: ResidenceDef) -> None:
    """Add a new residence definition for the ResidenceLibrary.

    Parameters
    ----------
    world
        The world instance containing the residence library.
    definition
        The definition to add.
    """
    world.resources.get_resource(ResidenceLibrary).add_definition(definition)
