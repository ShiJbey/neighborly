"""
Talk of the Town Sample
------------------------

This samples shows Neighborly simulating a Talk of the Town-style
town. It uses the talktown plugin included with Neighborly
and simulates 140 years of town history.
"""

import time

from neighborly import NeighborlyConfig
from neighborly.core.ecs.ecs import GameObject
from neighborly.core.time import SimDateTime
from neighborly.core.tracery import Tracery
from neighborly.events import NewSettlementEvent
from neighborly.exporter import export_to_json
from neighborly.simulation import Neighborly
from neighborly.systems import AIActionSystem, RandomLifeEventSystem

EXPORT_WORLD = False

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "seed": "Apples",
            "time_increment": "1mo",
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
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown.spawn_tables",
                "neighborly.plugins.talktown",
            ]
        }
    )
)

RandomLifeEventSystem.active = True
AIActionSystem.active = True

if __name__ == "__main__":
    st = time.time()
    sim.run_until(SimDateTime(20, 1, 1))
    elapsed_time = time.time() - st


    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        with open(f"neighborly_{sim.config.seed}.json", "w") as f:
            f.write(export_to_json(sim))
