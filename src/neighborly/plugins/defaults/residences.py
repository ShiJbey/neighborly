from typing import Any, Tuple

from neighborly.components.residence import BaseResidence
from neighborly.components.shared import Building, Location, Position2D
from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import EventHistory
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.status_system import Statuses
from neighborly.world_map import BuildingMap

plugin_info = PluginInfo(
    name="default residences plugin",
    plugin_id="default.residences",
    version="0.1.0",
)


class House(BaseResidence):
    @classmethod
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        residence = super().instantiate(world, **kwargs)
        residence.add_component(Location)
        residence.add_component(Statuses)
        residence.add_component(EventHistory)
        residence.add_component(Building, building_type="residential")

        building_map = world.resource_manager.get_resource(BuildingMap)

        lot: Tuple[int, int] = kwargs.get("lot")
        if lot is None:
            raise TypeError(
                "{}.instantiate is missing required keyword argument: 'lot'.".format(
                    cls.__name__
                )
            )

        # Reserve the space
        building_map.add_building(lot, residence)

        # Set the position of the building
        residence.add_component(Position2D, x=lot[0], y=lot[1])

        return residence


def setup(sim: Neighborly):
    sim.world.gameobject_manager.register_component(House)
