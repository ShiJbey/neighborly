import random
import logging
from neighborly.simulation import NeighborlyConfig, Simulation
from neighborly.inspection_tools import *

NEIGHBORLY_CONFIG = NeighborlyConfig(
    **{
        "simulation": {
            "seed": random.randint(0, 999999),
            "hours_per_timestep": 6,
            "start_date": "0000-00-00T00:00.000z",
            "end_date": "0001-00-00T00:00.000z",
        },
        "plugins": ["neighborly.plugins.default_plugin", "neighborly.plugins.talktown"],
    }
)


if __name__ == "__main__":
    # logging.basicConfig(filename="neighborly.log", filemode="w", level=logging.DEBUG)
    sim = Simulation(NEIGHBORLY_CONFIG)
    sim.run()
