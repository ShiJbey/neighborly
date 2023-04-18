import random
from enum import Enum
from typing import Any

from neighborly.simulation import Neighborly, PluginInfo
from neighborly.systems import System


class Weather(Enum):
    """Weather status"""

    SUNNY = "sunny"
    RAINING = "raining"
    PARTIALLY_CLOUDY = "partially cloudy"
    OVERCAST = "overcast"


class WeatherManager:
    """Manages the weather in the town."""

    current_weather: Weather
    """Current weather in the town."""

    time_before_change: int
    """Number of hours before the weather pattern changes."""

    __slots__ = "current_weather", "time_before_change"

    def __init__(self, default: Weather = Weather.SUNNY) -> None:
        self.current_weather = default
        self.time_before_change = 0

    def __repr__(self) -> str:
        return f"Weather({str(self.current_weather.value)})"


class WeatherSystem(System):
    """Updates the current weather state

    Attributes
    ----------
    avg_change_interval: int
        Average number of hours that the current weather
        state will last before being changed
    """

    sys_group = "early-update"

    def __init__(self, avg_change_interval: int = 24) -> None:
        super().__init__()
        self.avg_change_interval: int = avg_change_interval

    def run(self, *args: Any, **kwargs: Any) -> None:
        weather_manager = self.world.get_resource(WeatherManager)
        rng = self.world.get_resource(random.Random)

        if weather_manager.time_before_change <= 0:
            # Select the next weather pattern
            weather_manager.current_weather = rng.choice(list(Weather))
            weather_manager.time_before_change = round(
                rng.normalvariate(mu=self.avg_change_interval, sigma=1)
            )

        weather_manager.time_before_change -= self.elapsed_time.hours


plugin_info = PluginInfo(
    name="default residences plugin",
    plugin_id="default.residences",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:
    sim.world.add_system(WeatherSystem())
    sim.world.add_resource(WeatherManager())
