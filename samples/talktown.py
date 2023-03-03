"""
samples/talktown.py

This samples shows Neighborly simulating a Talk of the Town-style
town. It uses the TalkOfTheTown plugin included with Neighborly
and simulated 140 years of town history.
"""

import time
from typing import Any

from neighborly import ISystem, NeighborlyConfig
from neighborly.decorators import system
from neighborly.exporter import export_to_json
from neighborly.simulation import Neighborly
from neighborly.utils.common import spawn_settlement

EXPORT_WORLD = False
DEBUG_LOGGING = False

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "seed": 3,
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
                "neighborly.plugins.defaults.social_rules",
                "neighborly.plugins.defaults.location_bias_rules",
                "neighborly.plugins.talktown",
            ],
        }
    )
)


@system(sim)
class CreateTown(ISystem):
    sys_group = "initialization"

    def process(self, *args: Any, **kwargs: Any) -> None:
        spawn_settlement(self.world)


if __name__ == "__main__":

    st = time.time()
    sim.run_for(140)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        with open(f"neighborly_{sim.config.seed}.json", "w") as f:
            f.write(export_to_json(sim))
