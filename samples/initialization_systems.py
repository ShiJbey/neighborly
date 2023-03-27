"""
samples/initialization_systems.py

This sample shows how to use initialization systems to set up the simulation before
the first timestep.
"""
from typing import Any

from neighborly import ISystem, Neighborly, NeighborlyConfig
from neighborly.components.shared import Name
from neighborly.core.settlement import Settlement
from neighborly.decorators import system
from neighborly.utils.common import spawn_settlement

sim = Neighborly(
    NeighborlyConfig.parse_obj({"plugins": ["neighborly.plugins.defaults.settlement"]})
)


@system(sim)
class InitializeMajorSettlements(ISystem):
    sys_group = "initialization"

    def process(self, *args: Any, **kwargs: Any) -> None:
        print("Setting up settlements...")
        spawn_settlement(self.world, "settlement", name="Winterfell")
        spawn_settlement(self.world, "settlement", name="The Vale of Arryn")
        spawn_settlement(self.world, "settlement", name="Casterly Rock")
        spawn_settlement(self.world, "settlement", name="King's Landing")
        spawn_settlement(self.world, "settlement", name="Highgarden")
        spawn_settlement(self.world, "settlement", name="Braavos")
        spawn_settlement(self.world, "settlement", name="Pentos")


def main():
    # We run the simulation for 10 timesteps, but the initialization
    # system group only runs once on the first timestep.
    for _ in range(10):
        sim.step()

    for guid, (name, _) in sim.world.get_components((Name, Settlement)):
        print(f"({guid}) {name}")


if __name__ == "__main__":
    main()
