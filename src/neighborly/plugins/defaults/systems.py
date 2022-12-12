from typing import Any

from neighborly import constants, systems
from neighborly.core.time import TimeDelta
from neighborly.simulation import Plugin, Simulation


class DefaultSystemsPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:

        resident_spawn_interval_days: int = kwargs.get(
            "resident_spawn_interval_days", 7
        )
        business_spawn_interval_days: int = kwargs.get(
            "business_spawn_interval_days", 5
        )

        sim.world.add_system(
            systems.CharacterAgingSystem(), constants.CHARACTER_UPDATE_PHASE
        )
        sim.world.add_system(
            systems.BusinessUpdateSystem(), constants.BUSINESS_UPDATE_PHASE
        )
        sim.world.add_system(
            systems.FindEmployeesSystem(), constants.BUSINESS_UPDATE_PHASE
        )
        sim.world.add_system(systems.BuildHousingSystem(), constants.TOWN_SYSTEMS_PHASE)
        sim.world.add_system(
            systems.SpawnResidentSystem(
                interval=TimeDelta(days=resident_spawn_interval_days)
            ),
            constants.TOWN_SYSTEMS_PHASE,
        )
        sim.world.add_system(
            systems.BuildBusinessSystem(
                interval=TimeDelta(days=business_spawn_interval_days)
            ),
            constants.TOWN_SYSTEMS_PHASE,
        )


def get_plugin() -> Plugin:
    return DefaultSystemsPlugin()
