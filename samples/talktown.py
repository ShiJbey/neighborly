"""
samples/talktown.py

This samples shows Neighborly simulating a Talk of the Town-style
town. It uses the TalkOfTheTown plugin included with Neighborly
and simulated 140 years of town history.
"""

import logging
import random
import time

from neighborly.core.time import SimDateTime
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.plugins import defaults, talktown, weather
from neighborly.simulation import SimulationBuilder

EXPORT_WORLD = False
DEBUG_LOGGING = False

if __name__ == "__main__":

    if DEBUG_LOGGING:
        logging.basicConfig(level=logging.DEBUG)

    sim = (
        SimulationBuilder(
            seed=random.randint(0, 999999),
            starting_date=SimDateTime(year=1839, month=8, day=19),
            print_events=True,
        )
        .add_plugin(defaults.get_plugin())
        .add_plugin(weather.get_plugin())
        .add_plugin(talktown.get_plugin())
        .build()
    )

    st = time.time()
    sim.run_for(140)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        output_path = f"{sim.seed}_{sim.town.name.replace(' ', '_')}.json"

        with open(output_path, "w") as f:
            data = NeighborlyJsonExporter().export(sim)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")
