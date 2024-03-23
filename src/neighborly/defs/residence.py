"""Residence Factory.

"""

from neighborly.components.residence import ResidentialBuilding, ResidentialUnit, Vacant
from neighborly.components.settlement import District
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

        residence = GameObject.create_new(world)

        building = residence.add_component(
            ResidentialBuilding, district=district.get_component(District)
        )
        residence.add_component(Traits)
        residence.add_component(Stats)

        residence.name = residence_def.display_name

        for _ in range(residence_def.residential_units):
            residential_unit = GameObject.create_new(
                world,
                components={Traits: {}, ResidentialUnit: {}},
                name="ResidentialUnit",
            )
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit, building=residence, district=district
            )
            building.units.append(residential_unit.get_component(ResidentialUnit))
            residential_unit.add_component(Vacant)

        return residence
