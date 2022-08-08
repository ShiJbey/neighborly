import logging
import random
import time

from neighborly.core.life_event import LifeEventLog
from neighborly.core.time import SimDateTime
from neighborly.plugins.default_plugin import (
    DefaultLifeEventPlugin,
    DefaultNameDataPlugin,
)
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
        .add_plugin(DefaultNameDataPlugin())
        .add_plugin(DefaultLifeEventPlugin())
        .add_plugin(WeatherPlugin())
        .add_plugin(TalkOfTheTownPlugin())
    )

    sim.world.get_resource(LifeEventLog).subscribe(lambda e: print(str(e)))

    st = time.time()
    sim.establish_setting()
    elapsed_time = time.time() - st

    print(f"World Date: {sim.get_time().to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")
