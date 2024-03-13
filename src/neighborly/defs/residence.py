"""Residence Factory.

"""

from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.stats import Stats
from neighborly.components.traits import Traits
from neighborly.defs.base_types import ResidenceDef, ResidenceGenOptions
from neighborly.ecs import GameObject, World
from neighborly.libraries import ResidenceLibrary


class DefaultResidenceDef(ResidenceDef):
    """Generates residence GameObjects."""

    def instantiate(
        self, world: World, district: GameObject, options: ResidenceGenOptions
    ) -> GameObject:
        """Generate a residence GameObject"""

        residence_library = world.resources.get_resource(ResidenceLibrary)
        residence_def = residence_library.get_definition(options.definition_id)

        residence = world.gameobjects.spawn_gameobject()

        building = ResidentialBuilding(district=district)
        residence.add_component(building)
        residence.add_component(Traits())
        residence.add_component(Stats())

        residence.name = residence_def.display_name

        for _ in range(residence_def.residential_units):
            residential_unit = world.gameobjects.spawn_gameobject(
                components=[Traits()], name="ResidentialUnit"
            )
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(building=residence, district=district)
            )
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())

        return residence
