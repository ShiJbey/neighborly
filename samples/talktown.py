import logging
import random
import time

from neighborly.core.life_event import LifeEventLog
from neighborly.core.time import SimDateTime
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.plugins.talktown import TalkOfTheTownPlugin
from neighborly.plugins.weather_plugin import WeatherPlugin
from neighborly.simulation import Simulation

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sim = (
        Simulation.create(
            seed=random.randint(0, 999999),
            world_gen_start=SimDateTime(year=1839, month=8, day=19),
            world_gen_end=SimDateTime(year=1979, month=8, day=19),
        )
        .add_plugin(DefaultPlugin())
        .add_plugin(WeatherPlugin())
        .add_plugin(TalkOfTheTownPlugin())
    )

    sim.world.get_resource(LifeEventLog).subscribe(lambda e: print(str(e)))

    st = time.time()
    sim.establish_setting()
    elapsed_time = time.time() - st

    print(f"World Date: {sim.time.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    output_path = f"{sim.seed}_{sim.town.name.replace(' ', '_')}.json"

    with open(output_path, "w") as f:
        data = NeighborlyJsonExporter().export(sim)
        f.write(data)
        print(f"Simulation data written to: '{output_path}'")
