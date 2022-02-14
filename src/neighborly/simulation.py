import random
from dataclasses import dataclass, field
from typing import Optional

import esper

from neighborly.core.processors import CharacterProcessor, RoutineProcessor
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime, TimeProcessor
from neighborly.core.town import Town, TownConfig
from neighborly.core.weather import Weather, WeatherManager, WeatherProcessor
from neighborly.engine import NeighborlyEngine, create_default_engine


@dataclass(frozen=True)
class SimulationConfig:
    """Configuration parameters for a Neighborly instance

    Attributes
    ----------
    seed: int
        The seed provided to the random number factory
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
    town: TownConfig = field(default_factory=TownConfig)


class Simulation:
    """A Neighborly simulation instance

    Attributes
    ----------
    config: SimulationConfig
        Configuration settings for how the simulation
    world: esper.World
        Entity-component system (ECS) that manages entities in the virtual world
    resources: int
        Entity ID of the entity that holds common resources used by all entities
    town: int
        Entity ID of the town entity within the ECS
    """

    __slots__ = "config", "world", "resources", "town"

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config: SimulationConfig = config if config else SimulationConfig()
        self.world: esper.World = esper.World()
        self.world.add_processor(WeatherProcessor(), 9)
        self.world.add_processor(TimeProcessor(), 10)
        self.world.add_processor(RoutineProcessor(), 5)
        self.world.add_processor(CharacterProcessor())
        self.resources: int = self.world.create_entity(
            WeatherManager(), SimDateTime(), create_default_engine(),
            RelationshipNetwork(),
        )
        self.town: int = -1

    def create_town(self) -> None:
        self.town = self.world.create_entity(Town.create(self.config.town))

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timestep)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.component_for_entity(self.resources, SimDateTime)

    def get_weather(self) -> Weather:
        """Get the current weather pattern in the town"""
        return self.world.component_for_entity(
            self.resources, WeatherManager
        ).current_weather

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.component_for_entity(self.town, Town)

    def get_engine(self) -> NeighborlyEngine:
        return self.world.component_for_entity(self.resources, NeighborlyEngine)
