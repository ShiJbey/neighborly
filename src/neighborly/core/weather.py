from enum import Enum
from typing import cast
import random

import esper
import numpy as np


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


class WeatherProcessor(esper.Processor):

    world: esper.World

    def __init__(self, avg_change_interval: int = 24) -> None:
        self.avg_change_interval: int = avg_change_interval

    def process(self, *args, **kwargs):
        delta_time: int = kwargs["delta_time"]
        for _, weather_manager in self.world.get_component(WeatherManager):
            weather_manager = cast(WeatherManager, weather_manager)

            if (weather_manager.time_before_change <= 0):
                # Select the next weather pattern
                weather_manager.current_weather = random.choice(list(Weather))
                weather_manager.time_before_change = round(
                    np.random.normal(self.avg_change_interval))

            weather_manager.time_before_change -= delta_time

        return super().process(*args, **kwargs)
