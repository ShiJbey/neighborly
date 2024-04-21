"""Business Component Factories.

"""

from typing import Any

from neighborly.components.business import Business, Occupation, Unemployed
from neighborly.defs.base_types import BusinessGenOptions
from neighborly.ecs import Component, ComponentFactory, GameObject
from neighborly.libraries import BusinessNameFactories


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
            name = factories.get_factory(name_factory)(
                gameobject.world, BusinessGenOptions()
            )

        # job_role_library = gameobject.world.resource_manager.get_resource(
        #     JobRoleLibrary
        # )

        business = Business(
            gameobject,
            name=name,
            **kwargs,
            # name=name,
            # owner_role=job_role_library.get_definition(self.owner_role),
            # employee_roles={
            #     role: JobOpeningData(
            #         role_id=role,
            #         business_id=business.uid,
            #         count=count,
            #     )
            #     for role, count in self.employee_roles.items()  # pylint: disable=E1101
            # },
            # district=district,
        )

        return business


class UnemployedFactory(ComponentFactory):
    """Creates Unemployed component instances."""

    __component__ = "Unemployed"

    def instantiate(self, gameobject: GameObject, /, **kwargs: Any) -> Component:

        return Unemployed(gameobject, **kwargs)
