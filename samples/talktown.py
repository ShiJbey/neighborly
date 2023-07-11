"""
Talk of the Town Sample
------------------------

This samples shows Neighborly simulating a Talk of the Town-style
town. It uses the talktown plugin included with Neighborly
and simulates 140 years of town history.
"""

import time

from neighborly import NeighborlyConfig
from neighborly.exporter import export_to_json
from neighborly.simulation import Neighborly

EXPORT_WORLD = False

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            # "seed": 7167130,
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown",
            ],
            "logging": {
                "logging_enabled": True,
                "log_level": "DEBUG",
            },
            "settings": {
                "settlement_size": (5, 5),  # Width/length of the settlement grid
                "zoning": (0.5, 0.5),  # Zoning is 50/50 residential vs. commercial
                "character_spawn_table": [
                    {"name": "character::default::male"},
                    {"name": "character::default::female"},
                    {"name": "character::default::non-binary"},
                ],
                "residence_spawn_table": [
                    {"name": "residence::default::house"},
                ],
                "business_spawn_table": [],
            },
        }
    )
)

if __name__ == "__main__":
    st = time.time()
    sim.run_for(140)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        with open(f"neighborly_{sim.config.seed}.json", "w") as f:
            f.write(export_to_json(sim))
