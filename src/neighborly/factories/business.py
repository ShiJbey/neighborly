"""Business Component Factories.

"""

from typing import Any

from neighborly.components.business import (
    Business,
    JobOpeningData,
    Occupation,
    Unemployed,
)
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import BusinessNameFactories, JobRoleLibrary


class OccupationFactory(ComponentFactory):
    """Creates Occupation component instances."""

    __component__ = "Occupation"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Occupation(gameobject, **kwargs)


class BusinessFactory(ComponentFactory):
    """Creates Business component instances."""

    __component__ = "Business"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        name = kwargs.get("name", "")

        if name_factory := kwargs.get("name_factory", ""):
            factories = gameobject.world.resource_manager.get_resource(
                BusinessNameFactories
            )
            name = factories.get_factory(name_factory)(gameobject)

        job_role_library = gameobject.world.resource_manager.get_resource(
            JobRoleLibrary
        )

        owner_role_id: str = kwargs["owner_role"]
        owner_role = job_role_library.get_role(owner_role_id)
        employee_roles: dict[str, int] = kwargs.get("employee_roles", {})

        business = Business(
            gameobject,
            name=name,
            owner_role=owner_role,
            employee_roles={
                role: JobOpeningData(
                    role_id=role,
                    business_id=gameobject.uid,
                    count=count,
                )
                for role, count in employee_roles.items()
            },
        )

        return business


class UnemployedFactory(ComponentFactory):
    """Creates Unemployed component instances."""

    __component__ = "Unemployed"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Unemployed(gameobject, **kwargs)
