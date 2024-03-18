"""Business Factory.

"""

from neighborly.components.business import Business, JobRole
from neighborly.components.location import Location
from neighborly.components.relationship import Relationships
from neighborly.components.shared import Agent, PersonalEventHistory
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import BusinessDef, BusinessGenOptions, JobRoleDef
from neighborly.ecs import GameObject, World
from neighborly.helpers.traits import add_trait
from neighborly.libraries import JobRoleLibrary
from neighborly.tracery import Tracery


class DefaultJobRoleDef(JobRoleDef):
    """A default implementation of a Job Role Definition."""

    def instantiate(self, world: World) -> GameObject:

        role = world.gameobjects.spawn_gameobject(name=self.display_name)

        role.add_component(
            JobRole(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                job_level=self.job_level,
                requirements=[],
                stat_modifiers=self.stat_modifiers,
                periodic_stat_boosts=self.periodic_stat_boosts,
                periodic_skill_boosts=self.periodic_skill_boosts,
            )
        )

        return role


class DefaultBusinessDef(BusinessDef):
    """Generates business GameObjects."""

    def instantiate(
        self,
        world: World,
        district: GameObject,
        options: BusinessGenOptions,
    ) -> GameObject:

        business = world.gameobjects.spawn_gameobject(name=self.display_name)

        business.metadata["definition_id"] = options.definition_id

        job_role_library = world.resources.get_resource(JobRoleLibrary)

        business.add_component(
            Business(
                name=self.display_name,
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

        business.add_component(Agent("business"))
        business.add_component(Traits())
        business.add_component(Location(is_private=self.open_to_public))
        business.add_component(PersonalEventHistory())
        business.add_component(Stats())
        business.add_component(Relationships())

        if self.name_factory:
            tracery = world.resources.get_resource(Tracery)
            new_name = tracery.generate(self.display_name)
            business.name = new_name
            business.get_component(Business).name = new_name

        for trait in self.traits:
            add_trait(business, trait)

        return business
