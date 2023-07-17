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

from neighborly import Neighborly, NeighborlyConfig, SystemBase, World
from neighborly.components.shared import Name
from neighborly.core.settlement import Settlement
from neighborly.decorators import system
from neighborly.systems import InitializationSystemGroup, InitializeSettlementSystem
from neighborly.utils.common import spawn_settlement

sim = Neighborly(
    NeighborlyConfig.parse_obj({"plugins": ["neighborly.plugins.defaults.settlement"]})
)


@system(sim.world, system_group=InitializationSystemGroup)
class InitializeMajorSettlements(SystemBase):
    def on_update(self, world: World) -> None:
        print("Setting up settlements...")
        spawn_settlement(world, name="Winterfell")
        spawn_settlement(world, name="The Vale of Arryn")
        spawn_settlement(world, name="Casterly Rock")
        spawn_settlement(world, name="King's Landing")
        spawn_settlement(world, name="Highgarden")
        spawn_settlement(world, name="Braavos")
        spawn_settlement(world, name="Pentos")


def main():
    sim.world.system_manager.get_system(InitializeSettlementSystem).set_active(False)

    # We run the simulation for 10 timesteps, but the initialization
    # system group only runs once on the first timestep.
    for _ in range(10):
        sim.step()

    for guid, (name, _) in sim.world.get_components((Name, Settlement)):
        print(f"({guid}) {name}")


if __name__ == "__main__":
    main()
