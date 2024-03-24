"""Helper functions for business operations.

"""

from __future__ import annotations

from typing import Optional

from neighborly.defs.base_types import BusinessDef, BusinessGenOptions, JobRoleDef
from neighborly.ecs import GameObject, World
from neighborly.libraries import BusinessLibrary, JobRoleLibrary


def create_business(
    world: World,
    district: GameObject,
    definition_id: str,
    options: Optional[BusinessGenOptions] = None,
) -> GameObject:
    """Create a new business instance.

    Parameters
    ----------
    world
        The World instance to spawn the business into.
    district
        The district where the business resides.
    definition_id
        The ID of the business definition to instantiate
    options
        Generation options.

    Returns
    -------
    GameObject
        The instantiated business.
    """
    library = world.resource_manager.get_resource(BusinessLibrary)

    business_def = library.get_definition(definition_id)

    options = options if options else BusinessGenOptions()

    business = business_def.instantiate(world, district, options)

    return business


def register_business_def(world: World, definition: BusinessDef) -> None:
    """Add a new business definition for the BusinessLibrary.

    Parameters
    ----------
    world
        The world instance containing the business library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(BusinessLibrary).add_definition(definition)


def register_job_role_def(world: World, definition: JobRoleDef) -> None:
    """Add a new job role definition for the JobRoleLibrary.

    Parameters
    ----------
    world
        The world instance containing the job role library.
    definition
        The definition to add.
    """
    world.resource_manager.get_resource(JobRoleLibrary).add_definition(definition)
    world.resource_manager.get_resource(JobRoleLibrary).add_definition(definition)
