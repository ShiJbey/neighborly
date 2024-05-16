"""Helper functions for business operations.

"""

from __future__ import annotations

from typing import Optional

from neighborly.components.business import (
    Business,
    BusinessStatus,
    JobRole,
    Occupation,
    Unemployed,
)
from neighborly.datetime import SimDate
from neighborly.ecs import Event, GameObject, World
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


def set_business_name(business: Business, name: str) -> None:
    """Set the name of a business."""

    business.name = name
    business.gameobject.name = name
    business.gameobject.dispatch_event(
        Event(
            "name-changed",
            world=business.gameobject.world,
            name=name,
            business=business,
        )
    )


def set_business_status(business: Business, status: BusinessStatus) -> None:
    """Set the status of a business."""

    business.status = status
    business.gameobject.dispatch_event(
        Event(
            "status-changed",
            world=business.gameobject.world,
            status=status,
            business=business,
        )
    )


def set_business_owner(business: Business, owner: Optional[GameObject]) -> None:
    """Set the owner of a business."""

    current_date = business.gameobject.world.resources.get_resource(SimDate)

    # Remove the current owner if there is one.
    if business.owner is not None:
        business.owner.remove_component(Occupation)
        business.owner.add_component(Unemployed(timestamp=current_date.copy()))

        business.owner.dispatch_event(
            Event(
                "occupation-changed",
                world=business.gameobject.world,
                occupation=None,
            )
        )

    # Set the business owner
    business.owner = owner

    # If set to character, configure their occupation.
    if owner:
        occupation = owner.add_component(
            Occupation(
                business=business.gameobject,
                start_date=current_date.copy(),
                job_role=business.owner_role,
            )
        )

        if owner.has_component(Unemployed):
            owner.remove_component(Unemployed)

        owner.dispatch_event(
            Event(
                "occupation-changed",
                world=business.gameobject.world,
                occupation=occupation,
            )
        )

    business.gameobject.dispatch_event(
        Event(
            "owner-changed",
            world=business.gameobject.world,
            business=business,
            owner=owner,
        )
    )


def add_employee(business: Business, employee: GameObject, role: JobRole) -> None:
    """Add an employee to the business.

    Parameters
    ----------
    employee
        The employee to add.
    role
        The employee's job role.
    """
    if business.owner is not None and employee == business.owner:
        raise ValueError("Business owner cannot be added as an employee.")

    if employee in business.employees:
        raise ValueError("Character cannot hold two roles at the same business.")

    if role not in business.employee_roles:
        raise ValueError(f"Business does not have employee role with ID: {role}.")

    remaining_slots = business.employee_roles[role]

    if remaining_slots == 0:
        raise ValueError(f"No remaining slots job role with ID: {role}.")

    business.employee_roles[role] -= 1

    business.employees[employee] = role

    current_date = business.gameobject.world.resources.get_resource(SimDate)

    occupation = employee.add_component(
        Occupation(
            business=business.gameobject,
            start_date=current_date.copy(),
            job_role=business.owner_role,
        )
    )

    if employee.has_component(Unemployed):
        employee.remove_component(Unemployed)

    employee.dispatch_event(
        Event(
            "occupation-changed",
            world=business.gameobject.world,
            occupation=occupation,
        )
    )

    business.gameobject.dispatch_event(
        Event(
            "employee-added",
            world=business.gameobject.world,
            business=business,
            employee=employee,
            role=role,
        )
    )


def remove_employee(business: Business, employee: GameObject) -> None:
    """Remove an employee from the business.

    Parameters
    ----------
    employee
        The employee to remove.
    """
    if employee not in business.employees:
        raise ValueError(f"{employee.name} is not an employee of this business.")

    role = business.employees[employee]

    del business.employees[employee]

    business.employee_roles[role] += 1

    current_date = business.gameobject.world.resources.get_resource(SimDate)
    employee.remove_component(Occupation)
    employee.add_component(Unemployed(timestamp=current_date.copy()))

    business.gameobject.dispatch_event(
        Event(
            "employee-removed",
            world=business.gameobject.world,
            business=business,
            employee=employee,
            role=role,
        )
    )
