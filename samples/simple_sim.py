import logging
import time
from typing import Any

from neighborly import ISystem, Neighborly, NeighborlyConfig, SimDateTime
from neighborly.decorators import system
from neighborly.exporter import export_to_json
from neighborly.utils.common import spawn_settlement

EXPORT_WORLD = False
DEBUG_LOGGING = False

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "seed": 8080,
            "relationship_schema": {
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {
                        "min_value": -5,
                        "max_value": 5,
                    },
                }
            },
            "plugins": [
                "neighborly.plugins.defaults.names",
                "neighborly.plugins.defaults.characters",
                "neighborly.plugins.defaults.businesses",
                "neighborly.plugins.defaults.residences",
                "neighborly.plugins.defaults.life_events",
                "neighborly.plugins.defaults.ai",
            ],
            "settings": {"new_families_per_year": 10},
        }
    )
)


@system(sim)
class CreateTown(ISystem):
    sys_group = "initialization"

    def process(self, *args: Any, **kwargs: Any) -> None:
        spawn_settlement(self.world)


if __name__ == "__main__":

    if DEBUG_LOGGING:
        logging.basicConfig(level=logging.DEBUG)

    print(f"Generating with world seed: {sim.config.seed}")

    st = time.time()
    sim.run_for(140)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.world.get_resource(SimDateTime)}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        output_path = f"{sim.config.seed}_neighborly.json"

        with open(output_path, "w") as f:
            f.write(export_to_json(sim))
            print(f"Simulation data written to: '{output_path}'")
