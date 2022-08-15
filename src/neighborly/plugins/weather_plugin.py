from enum import Enum

from neighborly.core.ecs import ISystem
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import SimDateTime
from neighborly.simulation import Plugin, Simulation


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


class WeatherSystem(ISystem):
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

    def process(self, *args, **kwargs):
        delta_time = self.world.get_resource(SimDateTime).delta_time
        weather_manager = self.world.get_resource(WeatherManager)
        engine = self.world.get_resource(NeighborlyEngine)

        if weather_manager.time_before_change <= 0:
            # Select the next weather pattern
            weather_manager.current_weather = engine.rng.choice(list(Weather))
            weather_manager.time_before_change = round(
                engine.rng.normalvariate(mu=self.avg_change_interval, sigma=1)
            )

        weather_manager.time_before_change -= delta_time


class WeatherPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        sim.world.add_system(WeatherSystem(), 9)
        sim.world.add_resource(WeatherManager())


def get_plugin() -> Plugin:
    return WeatherPlugin()
