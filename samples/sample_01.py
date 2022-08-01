from neighborly.core.town import TownConfig
from neighborly.loaders import YamlDataLoader
from neighborly.plugins import NeighborlyPlugin, PluginContext
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.simulation import NeighborlyConfig, Simulation, SimulationConfig


class CustomPlugin(NeighborlyPlugin):
    def apply(self, ctx: PluginContext, **kwargs) -> None:
        places = """
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
        YamlDataLoader(str_data=places).load(ctx.engine)


def main():
    config = NeighborlyConfig(
        simulation=SimulationConfig(
            hours_per_timestep=12, town=TownConfig(width=5, length=1)
        ),
        plugins=[
            CustomPlugin(),
            DefaultPlugin(),
        ],
    )

    _sim = Simulation.from_config(config)

    _sim.step()

    return _sim


if __name__ == "__main__":
    sim = main()
