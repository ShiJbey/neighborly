"""Helper functions for business operations.

"""

from __future__ import annotations

from neighborly.defs.base_types import (
    BusinessDef,
    BusinessGenerationOptions,
    JobRoleDef,
)
from neighborly.ecs import GameObject, World
from neighborly.libraries import BusinessLibrary, JobRoleLibrary


def create_business(
    world: World, district: GameObject, options: BusinessGenerationOptions
) -> GameObject:
    """Create a new business instance.

    Parameters
    ----------
    world
        The World instance to spawn the business into.
    district
        The district where the business resides.
    options
        Generation options.

    Returns
    -------
    GameObject
        The instantiated business.
    """

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
    world.resources.get_resource(BusinessLibrary).add_definition(definition)


def register_job_role_def(world: World, definition: JobRoleDef) -> None:
    """Add a new job role definition for the JobRoleLibrary.

    Parameters
    ----------
    world
        The world instance containing the job role library.
    definition
        The definition to add.
    """
    world.resources.get_resource(JobRoleLibrary).add_definition(definition)
