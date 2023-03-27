"""
samples/initialization_systems.py

Neighborly is a step-based simulation. So, time advances one timestep at a time. Each
timestep is divided into three phases: early-update, update, and late-update. There is
also a special fourth phase called "initialization" that runs only once at the beginning
of the first timestep. This is where users should place any systems intended to set up
the simulation.

In this example, we show how a user could add a new initialization system that spawns
multiple settlements into the simulation.
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
