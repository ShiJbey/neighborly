import random
from dataclasses import dataclass, field
from typing import Optional

import esper
import numpy as np

from neighborly.core.processors import CharacterProcessor, RoutineProcessor
from neighborly.core.time import SimDateTime, TimeProcessor
from neighborly.core.town.town import Town, TownConfig
from neighborly.core.weather import Weather, WeatherManager, WeatherProcessor


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration parameters for a Neighborly instance

    Attributes
    ----------
    seed: int
        The seed provided to the random number generator
    hours_per_timestep: int
        How many in-simulation hours elapse every simulation tic
    misc_paces_set: str
        Namespace of miscellaneous places that can exist in the town
    residences_set: str
        Namespace of residential buildings archetypes that can exist in the town
    businesses_set: str
        Namespace of business archetypes that can exist in the town
    characters_set: str
        Namespace of character archetypes that can exist in the town
    town: TownConfig
        Configuration settings for town creation
    """

    seed: int = random.randint(0, 99999)
    hours_per_timestep: int = 4
    misc_places_set: str = "default"
    residences_set: str = "default"
    business_set: str = "default"
    character_set: str = "default"
    town: TownConfig = field(default_factory=TownConfig)


class Simulation:
    """A Neighborly simulation instance

    Attributes
    ----------
    config: SimulationConfig
        Configuration settings for how the simulation
    world: esper.World
        Entity-component system (ECS) that manages entities in the virtual world
    simulation_manager: int
        Entity ID of the Simulation Manager entity in the ECS
    town: int
        Entity ID of the town entity within the ECS
    """

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
            WeatherManager(), SimDateTime()
        )
        self.town: int = self.world.create_entity(Town.create(self.config.town))

    def _set_seed(self) -> None:
        """Sets the seed random number generation"""
        random.seed(self.config.seed)
        np.random.seed(self.config.seed)

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timestep)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.component_for_entity(self.simulation_manager, SimDateTime)

    def get_weather(self) -> Weather:
        """Get the current weather pattern in the town"""
        return self.world.component_for_entity(
            self.simulation_manager, WeatherManager
        ).current_weather

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.component_for_entity(self.town, Town)
