"""Helper functions for business operations.

"""

from __future__ import annotations

from typing import Optional

from neighborly.components.business import (
    Business,
    BusinessStatus,
    Occupation,
    Unemployed,
)
from neighborly.components.settlement import District
from neighborly.components.spawn_table import BusinessSpawnTable
from neighborly.datetime import SimDate
from neighborly.defs.base_types import BusinessDef, BusinessGenOptions, JobRoleDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.location import (
    add_frequented_location,
    remove_all_frequenting_characters,
    remove_frequented_location,
)
from neighborly.helpers.relationship import get_relationship
from neighborly.helpers.stats import get_stat
from neighborly.helpers.traits import add_trait, remove_trait
from neighborly.libraries import BusinessLibrary, JobRoleLibrary
from neighborly.life_event import add_to_personal_history, dispatch_life_event
from neighborly.plugins.default_events import FiredFromJobEvent


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


def close_business(business: GameObject) -> None:
    business_comp = business.get_component(Business)

    # Update the business as no longer active
    business_comp.status = BusinessStatus.CLOSED

    # Remove all the employees
    for employee, _ in [*business_comp.employees.items()]:
        lay_off_employee(business, employee)

    # Remove the owner if applicable
    if business_comp.owner is not None:
        leave_job(business, business_comp.owner)

    # Decrement the number of this type
    business_comp.district.get_component(BusinessSpawnTable).decrement_count(
        business.metadata["definition_id"]
    )
    business_comp.district.get_component(District).remove_business(business)

    # Remove any other characters that frequent the location
    remove_all_frequenting_characters(business)

    # Un-mark the business as active so it doesn't appear in queries
    business.deactivate()


def lay_off_employee(business: GameObject, employee: GameObject) -> None:

    world = business.world

    current_date = world.resource_manager.get_resource(SimDate)

    business_comp = business.get_component(Business)

    remove_frequented_location(employee, business)

    business_comp.remove_employee(employee)

    # Update boss/employee relationships if needed
    owner = business_comp.owner
    if owner is not None:
        remove_trait(get_relationship(employee, owner), "boss")
        remove_trait(get_relationship(owner, employee), "employee")

    # Update coworker relationships
    for other_employee, _ in business_comp.employees.items():
        if other_employee == employee:
            continue

        remove_trait(get_relationship(employee, other_employee), "coworker")
        remove_trait(get_relationship(other_employee, employee), "coworker")

    employee.add_component(Unemployed(employee, timestamp=current_date))
    employee.remove_component(Occupation)


def leave_job(business: GameObject, character: GameObject) -> None:
    """Have character leave their job."""
    world = business.world

    current_date = world.resource_manager.get_resource(SimDate)

    business_comp = business.get_component(Business)

    remove_frequented_location(character, business)

    if character == business_comp.owner:
        business_comp.set_owner(None)

        # Update relationships boss/employee relationships
        for employee, _ in business_comp.employees.items():
            remove_trait(get_relationship(character, employee), "employee")
            remove_trait(get_relationship(employee, character), "boss")

        character.add_component(Unemployed(character, timestamp=current_date))

        character.remove_component(Occupation)

        character.add_component(Unemployed(character, timestamp=current_date))

    else:
        business_comp.remove_employee(character)

        # Update boss/employee relationships if needed
        owner = business_comp.owner
        if owner is not None:
            remove_trait(get_relationship(character, owner), "boss")
            remove_trait(get_relationship(owner, character), "employee")

        # Update coworker relationships
        for other_employee, _ in business_comp.employees.items():
            if other_employee == character:
                continue

            remove_trait(get_relationship(character, other_employee), "coworker")
            remove_trait(get_relationship(other_employee, character), "coworker")

    character.add_component(Unemployed(character, timestamp=current_date))
    character.remove_component(Occupation)


def fire_employee(business: GameObject, character: GameObject) -> None:
    """Fire an employee."""

    job_role = character.get_component(Occupation).job_role

    event = FiredFromJobEvent(character, business, job_role)

    dispatch_life_event(business.world, event)
    add_to_personal_history(character, event)

    leave_job(business, character)

    business_data = business.get_component(Business)

    owner = business_data.owner
    if owner is not None:
        get_stat(get_relationship(character, owner), "reputation").base_value -= 20
        get_stat(get_relationship(owner, character), "reputation").base_value -= 10
        get_stat(get_relationship(character, owner), "romance").base_value -= 30


def add_employee(
    business: GameObject, character: GameObject, job_role: JobRoleDef
) -> None:
    """Add an employee to the business."""
    world = business.world

    business_comp = business.get_component(Business)
    current_date = world.resource_manager.get_resource(SimDate)

    character.add_component(
        Occupation(
            character,
            business=business,
            start_date=current_date,
            job_role=job_role,
        )
    )

    add_frequented_location(character, business)

    if character.has_component(Unemployed):
        character.remove_component(Unemployed)

    # Update boss/employee relationships if needed
    if business_comp.owner is not None:
        add_trait(get_relationship(character, business_comp.owner), "boss")
        add_trait(get_relationship(business_comp.owner, character), "employee")

    # Update employee/employee relationships
    for employee, _ in business_comp.employees.items():
        add_trait(get_relationship(character, employee), "coworker")
        add_trait(get_relationship(employee, character), "coworker")

    business_comp.add_employee(character, job_role)


def promote_employee(
    business: GameObject, character: GameObject, job_role: JobRoleDef
) -> None:
    """Promote a character to a higher position."""

    business_data = business.get_component(Business)

    # Remove the old occupation
    character.remove_component(Occupation)

    business_data.remove_employee(character)

    # Add the new occupation
    character.add_component(
        Occupation(
            character,
            business=business,
            start_date=character.world.resource_manager.get_resource(SimDate),
            job_role=job_role,
        )
    )

    business_data.add_employee(character, job_role)
