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

sim = Neighborly(NeighborlyConfig(verbose=False))


@system(sim)
class InitializeMajorSettlements(ISystem):
    sys_group = "initialization"

    def process(self, *args: Any, **kwargs: Any) -> None:
        print("Setting up settlements...")
        spawn_settlement(self.world, "Winterfell")
        spawn_settlement(self.world, "The Vale of Arryn")
        spawn_settlement(self.world, "Casterly Rock")
        spawn_settlement(self.world, "King's Landing")
        spawn_settlement(self.world, "Highgarden")
        spawn_settlement(self.world, "Braavos")
        spawn_settlement(self.world, "Pentos")


def main():
    # We run the simulation for 10 timesteps, but the initialization
    # system group only runs once on the first timestep.
    for _ in range(10):
        sim.step()

    for guid, (name, _) in sim.world.get_components((Name, Settlement)):
        print(f"({guid}) {name}")


if __name__ == "__main__":
    main()
