"""Business Factory.

"""

import pydantic

from neighborly.ecs.world import World


class BusinessGenerationOptions(pydantic.BaseModel):
    """Parameters used to generate new businesses."""

    definition_id: str
    """The definition to generate."""
    name: str = ""
    """The name of the business."""


class BusinessFactory:
    """A default implementation of a Business Definition."""

    def instantiate(
        self,
        world: World
        district: GameObject,
        options: BusinessGenerationOptions,
    ) -> None:

        library = world.resources.get_resource(BusinessLibrary)

        business_def = library.get_definition(options.definition_id)

        business = world.gameobjects.spawn_gameobject()
        business.metadata["definition_id"] = options.definition_id

        business_def.initialize(district, business, options)

        world = business.world
        job_role_library = world.resources.get_resource(JobRoleLibrary)

        business.add_component(
            Business(
                name="",
                owner_role=job_role_library.get_role(self.owner_role).get_component(
                    JobRole
                ),
                employee_roles={
                    job_role_library.get_role(role).get_component(JobRole): count
                    for role, count in self.employee_roles.items()
                },
                district=district,
            )
        )

        business.add_component(Traits())
        business.add_component(FrequentedBy())
        business.add_component(PersonalEventHistory())
        business.add_component(Stats())
        business.add_component(Relationships())

        self.initialize_name(business)

        if self.open_to_public:
            business.add_component(OpenToPublic())

        for trait in self.traits:
            add_trait(business, trait)

    def initialize_name(self, business: GameObject) -> None:
        """Generates a name for the business."""
        tracery = business.world.resources.get_resource(Tracery)
        name = tracery.generate(self.display_name)
        business.get_component(Business).name = name
        business.name = name
