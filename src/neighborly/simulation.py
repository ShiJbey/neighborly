import math
import random
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from tqdm import tqdm

from neighborly.core.business import BusinessFactory
from neighborly.core.character.character import GameCharacterFactory
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventLog, LifeEventHandlerFactory
from neighborly.core.location import LocationFactory
from neighborly.core.position import Position2DFactory
from neighborly.core.processors import CharacterProcessor, RoutineProcessor, CityPlanner, SocializeProcessor, \
    LifeEventProcessor, StatusManagerProcessor
from neighborly.core.residence import ResidenceFactory
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import RoutineFactory
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.status import StatusManagerFactory
from neighborly.core.time import SimDateTime, TimeProcessor
from neighborly.core.town import Town, TownConfig
from neighborly.plugins import NeighborlyPlugin
from neighborly.plugins.default_plugin import DefaultPlugin, PluginContext


@dataclass
class SimulationConfig:
    """Configuration parameters for a Neighborly instance

    Attributes
    ----------
    seed: int
        The seed provided to the random number factory
    hours_per_timestep: int
        How many in-simulation hours elapse every simulation tic
    town: TownConfig
        Configuration settings for town creation
    """

    seed: int = random.randint(0, 99999)
    hours_per_timestep: int = 4
    start_date: str = "0000-00-00T00:00.000z"
    end_date: str = "0001-00-00T00:00.000z"
    town: TownConfig = field(default_factory=TownConfig)
    population_weights: Dict[str, int] = field(default_factory=dict)
    business_wights: Dict[str, int] = field(default_factory=dict)


class Simulation:
    """A Neighborly simulation instance

    Attributes
    ----------
    config: SimulationConfig
        Configuration settings for how the simulation
    world: World
        Entity-component system (ECS) that manages entities in the virtual world
    """

    __slots__ = "config", "world"

    def __init__(self, config: SimulationConfig, engine: NeighborlyEngine) -> None:
        self.config: SimulationConfig = config
        self.world: World = World()
        self.world.add_system(TimeProcessor(), 10)
        self.world.add_system(RoutineProcessor(), 5)
        self.world.add_system(CharacterProcessor(), 3)
        self.world.add_system(StatusManagerProcessor(), 2)
        self.world.add_system(SocializeProcessor(), 2)
        self.world.add_system(CityPlanner())
        self.world.add_system(LifeEventProcessor())
        self.world.add_resource(SimDateTime())
        self.world.add_resource(engine)
        self.world.add_resource(RelationshipNetwork())
        self.world.add_resource(EventLog())

    @classmethod
    def create(
            cls,
            config: Optional[SimulationConfig] = None,
            engine: Optional[NeighborlyEngine] = None,
    ) -> 'Simulation':
        """Create new simulation instance"""
        sim_config: SimulationConfig = config if config else SimulationConfig()
        engine_instance: NeighborlyEngine = engine if engine else create_default_engine(sim_config.seed)
        sim = cls(sim_config, engine_instance)
        sim.world.add_resource(Town.create(sim_config.town))
        return sim

    @classmethod
    def from_config(cls, config: 'NeighborlyConfig') -> 'Simulation':
        """Create a new simulation from a Neighborly configuration"""
        engine = create_default_engine(config.simulation.seed)
        sim = cls(config.simulation, engine)

        for plugin in config.plugins:
            plugin.apply(PluginContext(engine=engine, world=sim.world))

        town = Town.create(config.simulation.town)
        sim.world.add_resource(town)

        return sim

    def run(self) -> None:
        """Run the simulation until it reaches the end date in the config"""
        start_date: SimDateTime = SimDateTime.from_iso_str(self.config.start_date)
        end_date: SimDateTime = SimDateTime.from_iso_str(self.config.end_date)
        total_hours = end_date.to_hours() - start_date.to_hours()
        total_timesteps = math.ceil(total_hours / self.config.hours_per_timestep)

        try:
            for _ in tqdm(range(total_timesteps)):
                self.step()
        except KeyboardInterrupt:
            print("Stopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timestep)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.get_resource(Town)

    def get_engine(self) -> NeighborlyEngine:
        return self.world.get_resource(NeighborlyEngine)


def create_default_engine(seed: int) -> NeighborlyEngine:
    engine = NeighborlyEngine(DefaultRNG(seed))
    engine.add_component_factory(GameCharacterFactory())
    engine.add_component_factory(RoutineFactory())
    engine.add_component_factory(LocationFactory())
    engine.add_component_factory(ResidenceFactory())
    engine.add_component_factory(Position2DFactory())
    engine.add_component_factory(StatusManagerFactory())
    engine.add_component_factory(LifeEventHandlerFactory())
    engine.add_component_factory(BusinessFactory())
    return engine


@dataclass
class NeighborlyConfig:
    simulation: SimulationConfig = field(default_factory=lambda: SimulationConfig())
    plugins: List[NeighborlyPlugin] = field(default_factory=lambda: [DefaultPlugin()])

    @staticmethod
    def merge(config_a: 'NeighborlyConfig', config_b: 'NeighborlyConfig') -> 'NeighborlyConfig':
        """Merge config B into config A and return a new config"""
        ret = NeighborlyConfig()
        ret.simulation = {**config_a.simulation, **config_b.simulation}
        return ret
