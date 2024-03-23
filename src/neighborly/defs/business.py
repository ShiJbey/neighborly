"""Business Factory.

"""

from neighborly.components.business import Business, JobOpening
from neighborly.components.location import Location
from neighborly.components.shared import Agent, EventHistory
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import BusinessDef, BusinessGenOptions, JobRoleDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.traits import add_trait
from neighborly.tracery import Tracery


class DefaultJobRoleDef(JobRoleDef):
    """A default implementation of a Job Role Definition."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()


class DefaultBusinessDef(BusinessDef):
    """Generates business GameObjects."""

    def instantiate(
        self,
        world: World,
        district: GameObject,
        options: BusinessGenOptions,
    ) -> GameObject:

        business = GameObject.create_new(world, name=self.display_name)

        business.metadata["definition_id"] = options.definition_id

        business_comp = business.add_component(
            Business,
            name=self.display_name,
            owner_role=self.owner_role,
            district=district,
        )

        for role, count in self.employee_roles.items():  # pylint: disable=E1101
            business_comp.job_openings.append(
                JobOpening(role_id=role, positions_available=count)
            )

        business.add_component(Agent, agent_type="business")
        business.add_component(Traits)
        business.add_component(Location, is_private=self.open_to_public)
        business.add_component(EventHistory)
        business.add_component(Stats)

        if self.name_factory:
            tracery = world.resources.get_resource(Tracery)
            new_name = tracery.generate(self.display_name)
            business.name = new_name
            business.get_component(Business).name = new_name

        for trait in self.traits:
            add_trait(business, trait)

        return business
