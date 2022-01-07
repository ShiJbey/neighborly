import random
from dataclasses import dataclass
from typing import Optional

import esper
import numpy as np

from neighborly.core.time import SimDateTime, TimeProcessor
from neighborly.core.town.town import Town
from neighborly.core.weather import Weather, WeatherManager, WeatherProcessor
from neighborly.core.processors import CharacterProcessor, RoutineProcessor


@dataclass
class SimulationConfig:
    """Configuration parameters for a Neighborly instance"""
    seed: int = random.randint(0, 99999)
    hours_per_timstep: int = 4
    structures_set: str = "default"
    residences_set: str = "default"
    business_set: str = "default"
    occupation_set: str = "default"
    activity_set: str = "default"
    character_set: str = "default"
    town_names: str = "default"


class Simulation:
    """A Neighborly instance"""

    __slots__ = "config", "world", "simulation_manager", "town"

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config: SimulationConfig = config if config else SimulationConfig()
        self._set_seed()
        self.world: esper.World = esper.World()
        self.world.add_processor(WeatherProcessor(), 9)
        self.world.add_processor(TimeProcessor(), 10)
        self.world.add_processor(RoutineProcessor(), 5)
        self.world.add_processor(CharacterProcessor())
        self.simulation_manager: int = self.world.create_entity(
            WeatherManager(),
            SimDateTime())
        self.town: int = self.world.create_entity(
            Town.create(self.config.town_names))

    def _set_seed(self) -> None:
        """Sets the seed random number generation"""
        random.seed(self.config.seed)
        np.random.seed(self.config.seed)

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timstep)

    def get_time(self) -> SimDateTime:
        return self.world.component_for_entity(self.simulation_manager, SimDateTime)

    def get_weather(self) -> Weather:
        return self.world.component_for_entity(self.simulation_manager, WeatherManager).current_weather

    def get_town(self) -> Town:
        return self.world.component_for_entity(self.town, Town)
