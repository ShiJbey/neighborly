import random
from enum import Enum

import numpy as np

from neighborly.core.ecs import World
from neighborly.simulation import PluginContext
from neighborly.core.time import SimDateTime


class Weather(Enum):
    """Weather status"""

    SUNNY = "sunny"
    RAINING = "raining"
    PARTIALLY_CLOUDY = "partially cloudy"
    OVERCAST = "overcast"


class WeatherManager:
    """Manages the weather in the town

    Attributes
    ----------
    current_weather : Weather
        Current weather in the town
    time_before_change : int
        Number of hours before the weather
        pattern changes
    """

    __slots__ = "current_weather", "time_before_change"

    def __init__(self, default: Weather = Weather.SUNNY) -> None:
        self.current_weather: Weather = default
        self.time_before_change: int = 0


class WeatherProcessor:
    """Updates the current weather state

    Attributes
    ----------
    avg_change_interval: int
        Average number of hours that the current weather
        state will last before being changed
    """

    def __init__(self, avg_change_interval: int = 24) -> None:
        super().__init__()
        self.avg_change_interval: int = avg_change_interval

    def __call__(self, world: World, **kwargs):
        delta_time = world.get_resource(SimDateTime).delta_time
        weather_manager = world.get_resource(WeatherManager)

        if weather_manager.time_before_change <= 0:
            # Select the next weather pattern
            weather_manager.current_weather = random.choice(list(Weather))
            weather_manager.time_before_change = round(
                np.random.normal(self.avg_change_interval)
            )

        weather_manager.time_before_change -= delta_time


def setup(ctx: PluginContext, **kwargs) -> None:
    ctx.world.add_system(WeatherProcessor(), 9)
    ctx.world.add_resource(WeatherManager())
