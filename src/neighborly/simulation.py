import random
from dataclasses import dataclass, field
from typing import Optional

from neighborly.core.ecs import World
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

    __slots__ = "config", "world"

    def __init__(self, config: SimulationConfig, engine: NeighborlyEngine, town: Town) -> None:
        self.config: SimulationConfig = config
        self.world: World = World()
        self.world.add_system(WeatherProcessor(), 9)
        self.world.add_system(TimeProcessor(), 10)
        self.world.add_system(RoutineProcessor(), 5)
        self.world.add_system(CharacterProcessor())
        self.world.add_resource(WeatherManager())
        self.world.add_resource(SimDateTime())
        self.world.add_resource(engine)
        self.world.add_resource(RelationshipNetwork())
        self.world.add_resource(town)

    @classmethod
    def create(
            cls,
            config: Optional[SimulationConfig] = None,
            engine: Optional[NeighborlyEngine] = None,
    ) -> 'Simulation':
        """Create new simulation instance"""
        sim_config: SimulationConfig = config if config else SimulationConfig()
        engine: NeighborlyEngine = engine if engine else create_default_engine()
        town = Town.create(sim_config.town)
        return cls(sim_config, engine, town)

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timestep)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    def get_weather(self) -> Weather:
        """Get the current weather pattern in the town"""
        return self.world.get_resource(WeatherManager).current_weather

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.get_resource(Town)

    def get_engine(self) -> NeighborlyEngine:
        return self.world.get_resource(NeighborlyEngine)
