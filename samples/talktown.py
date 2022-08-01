import logging
import random

from neighborly.core.time import SimDateTime
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.plugins.talktown import TalkOfTheTownPlugin
from neighborly.plugins.weather_plugin import WeatherPlugin
from neighborly.simulation import Simulation

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    sim = (
        Simulation.create(seed=random.randint(0, 999999))
        .add_plugin(DefaultPlugin())
        .add_plugin(WeatherPlugin())
        .add_plugin(TalkOfTheTownPlugin())
    )

    sim.establish_setting(
        SimDateTime.from_iso_str("0000-00-00T00:00.000z"),
        SimDateTime.from_iso_str("0050-00-00T00:00.000z"),
    )

    print(sim.world)
