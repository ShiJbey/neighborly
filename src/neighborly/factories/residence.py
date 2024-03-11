"""Residence Factory.

"""

from neighborly.ecs import GameObject, World


class ResidenceFactory:
    """A default implementation of a Residence Definition."""

    def instantiate(self, world: World, district: GameObject) -> None:

        building = ResidentialBuilding(district=district)
        residence.add_component(building)
        residence.add_component(Traits())
        residence.add_component(Stats())

        residence.name = self.display_name

        for _ in range(self.residential_units):
            residential_unit = world.gameobjects.spawn_gameobject(
                components=[Traits()], name="ResidentialUnit"
            )
            residence.add_child(residential_unit)
            residential_unit.add_component(
                ResidentialUnit(building=residence, district=district)
            )
            building.add_residential_unit(residential_unit)
            residential_unit.add_component(Vacant())
