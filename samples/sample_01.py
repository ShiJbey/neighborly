from neighborly.loaders import YamlDataLoader
from neighborly.plugins import default_plugin
from neighborly.simulation import Simulation, SimulationConfig

STRUCTURES = \
    """
    Places:
        - name: Space Casino
          components:
            - type: Location
              options:
                activities: ["Gambling", "Drinking", "Eating", "Socializing"]
        - name: Mars
          components:
            - type: Location
              options:
                activities: ["Reading", "Relaxing"]
        - name: Kamino
          components:
            - type: Location
              options:
                activities: ["Recreation", "Studying"]
    """


def main():
    config = SimulationConfig(hours_per_timestep=4)
    sim = Simulation.create(config)
    default_plugin.initialize_plugin(sim.get_engine())
    YamlDataLoader(str_data=STRUCTURES).load(sim.get_engine())

    for _ in range(100):
        sim.step()

    print("Done")


if __name__ == "__main__":
    main()
