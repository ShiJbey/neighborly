"""Helper functions for managing residences and residents.

"""

from __future__ import annotations

from typing import Optional

from neighborly.defs.base_types import ResidenceDef, ResidenceGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import ResidenceLibrary


def create_residence(
    world: World,
    district: GameObject,
    definition_id: str,
    options: Optional[ResidenceGenOptions] = None,
) -> GameObject:
    """Create a new residence instance."""
    library = world.resource_manager.get_resource(ResidenceLibrary)

    residence_def = library.get_definition(definition_id)

    options = options if options else ResidenceGenOptions()

    residence = residence_def.instantiate(world, district, options)

    return residence


def register_residence_def(world: World, definition: ResidenceDef) -> None:
    """Add a new residence definition for the ResidenceLibrary.

    Parameters
    ----------
    world
        The world instance containing the residence library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(ResidenceLibrary).add_definition(definition)
    world.resource_manager.get_resource(ResidenceLibrary).add_definition(definition)
