from neighborly.plugins import default_plugin
from neighborly.simulation import SimulationConfig, Simulation


def main():
    """Main Function."""

    sim = Simulation.create(SimulationConfig(hours_per_timestep=500, seed=10902))
    default_plugin.initialize_plugin(sim.get_engine())

    for _ in range(100):
        sim.step()

    print("Done")


if __name__ == "__main__":
    main()
