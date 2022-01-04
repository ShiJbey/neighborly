import random
from dataclasses import dataclass
from typing import Optional

import esper

from neighborly.core.time import SimDateTime, TimeProcessor
from neighborly.core.weather import Weather, WeatherManager, WeatherProcessor
from neighborly.core.processors import CharacterProcessor, RoutineProcessor

__all__ = [
    "SimulationConfig",
    "Simulation"
]


@dataclass
class SimulationConfig:
    """Configuration parameters for a Neighborly instance"""
    seed: str = str(random.randint(0, 99999))
    hours_per_timstep: int = 4


class Simulation:
    """A Neighborly instance"""

    __slots__ = "config", "world", "simulation_manager"

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config: SimulationConfig = config if config else SimulationConfig()
        random.seed(self.config.seed)
        self.world: esper.World = esper.World()
        self.world.add_processor(WeatherProcessor(), 9)
        self.world.add_processor(TimeProcessor(), 10)
        self.world.add_processor(RoutineProcessor(), 5)
        self.world.add_processor(CharacterProcessor())
        self.simulation_manager: int = self.world.create_entity(
            WeatherManager(),
            SimDateTime())

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timstep)

    def get_time(self) -> SimDateTime:
        return self.world.component_for_entity(self.simulation_manager, SimDateTime)

    def get_weather(self) -> Weather:
        return self.world.component_for_entity(self.simulation_manager, WeatherManager).current_weather
