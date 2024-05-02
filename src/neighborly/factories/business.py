"""Business Component Factories.

"""

from typing import Any

from neighborly.components.business import Business, Occupation, Unemployed
from neighborly.ecs import Component, ComponentFactory, World
from neighborly.libraries import BusinessNameFactories, JobRoleLibrary


class OccupationFactory(ComponentFactory):
    """Creates Occupation component instances."""

    __component__ = "Occupation"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        return Occupation(**kwargs)


class BusinessFactory(ComponentFactory):
    """Creates Business component instances."""

    __component__ = "Business"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        name = kwargs.get("name", "")

        if name_factory := kwargs.get("name_factory", ""):
            factories = world.resource_manager.get_resource(BusinessNameFactories)

            name = factories.get_factory(name_factory)(world)

        job_role_library = world.resource_manager.get_resource(JobRoleLibrary)

        owner_role_id: str = kwargs["owner_role"]
        owner_role = job_role_library.get_role(owner_role_id)
        employee_roles: dict[str, int] = kwargs.get("employee_roles", {})

        business = Business(
            name=name,
            owner_role=owner_role,
            employee_roles={
                job_role_library.get_role(role): count
                for role, count in employee_roles.items()
            },
        )

        return business


class UnemployedFactory(ComponentFactory):
    """Creates Unemployed component instances."""

    __component__ = "Unemployed"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        return Unemployed(**kwargs)
