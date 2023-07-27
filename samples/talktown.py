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
            "seed": "Apples",
            "settlement_name": "Townsville",
            "plugins": [
                "neighborly.plugins.defaults.all",
                # "neighborly.plugins.talktown",
            ],
            "logging": {
                "logging_enabled": True,
                "log_level": "DEBUG",
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
