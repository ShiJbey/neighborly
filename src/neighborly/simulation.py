import random
from typing import Optional, List, Dict
from pydantic import BaseModel, Field

from neighborly.core.business import BusinessFactory
from neighborly.core.character.character import GameCharacterFactory
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import EventLog, LifeEventHandlerFactory
from neighborly.core.location import LocationFactory
from neighborly.core.position import Position2DFactory
from neighborly.core.processors import (
    CharacterProcessor,
    RoutineProcessor,
    SocializeProcessor,
    LifeEventProcessor,
    TimeProcessor,
    ResidentImmigrationSystem,
    CityPlanner,
)
from neighborly.core.residence import ResidenceFactory
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import RoutineFactory
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime, DAYS_PER_YEAR, HOURS_PER_DAY
from neighborly.core.town import Town, TownConfig
from neighborly.plugins import NeighborlyPlugin
from neighborly.plugins.default_plugin import DefaultPlugin, PluginContext


class SimulationConfig(BaseModel):
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
    hours_per_timestep: int = 6
    start_date: str = "0000-00-00T00:00.000z"
    end_date: str = "0100-00-00T00:00.000z"
    town: TownConfig = Field(default_factory=TownConfig)
    character_weights: Dict[str, int] = Field(default_factory=dict)
    residence_weights: Dict[str, int] = Field(default_factory=dict)
    business_wights: Dict[str, int] = Field(default_factory=dict)


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
        self.world.add_system(SocializeProcessor(), 2)
        self.world.add_system(CityPlanner())
        self.world.add_system(
            ResidentImmigrationSystem(
                config.character_weights, config.residence_weights
            )
        )
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
    ) -> "Simulation":
        """Create new simulation instance"""
        sim_config: SimulationConfig = config if config else SimulationConfig()
        engine_instance: NeighborlyEngine = (
            engine if engine else create_default_engine(sim_config.seed)
        )
        sim = cls(sim_config, engine_instance)
        sim.world.add_resource(Town.create(sim_config.town))
        return sim

    @classmethod
    def from_config(cls, config: "NeighborlyConfig") -> "Simulation":
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

        fully_simulated_days = set(
            self._generate_sample_days(start_date, end_date, n=36)
        )

        total_days = (start_date - end_date).total_days
        total_timesteps = (total_days - len(fully_simulated_days)) + (
            len(fully_simulated_days)
            * (HOURS_PER_DAY // self.config.hours_per_timestep)
        )

        try:
            while self.get_time() <= end_date:
                if self.get_time().to_ordinal() in fully_simulated_days:
                    self.step(hours=self.config.hours_per_timestep, full_sim=True)
                else:
                    self.step(hours=24)
        except KeyboardInterrupt:
            print("Stopping Simulation")
        finally:
            print(f"Current Date: {self.get_time().to_date_str()}")

    def step(self, hours: int, **kwargs) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=self.config.hours_per_timestep, **kwargs)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.get_resource(Town)

    def get_engine(self) -> NeighborlyEngine:
        return self.world.get_resource(NeighborlyEngine)

    @staticmethod
    def _generate_sample_days(
        start_date: SimDateTime, end_date: SimDateTime, n: int
    ) -> list[int]:
        """Samples n days from each year between the start and end dates"""
        ordinal_start_date: int = start_date.to_ordinal()
        ordinal_end_date: int = end_date.to_ordinal()

        sampled_ordinal_dates: list[int] = []

        current_date = ordinal_start_date

        while current_date < ordinal_end_date:
            sampled_dates = random.sample(
                range(current_date, current_date + DAYS_PER_YEAR), k=n
            )
            sampled_ordinal_dates.extend(sorted(sampled_dates))
            current_date = min(current_date + DAYS_PER_YEAR, ordinal_end_date)

        return sampled_ordinal_dates


def create_default_engine(seed: int) -> NeighborlyEngine:
    engine = NeighborlyEngine(DefaultRNG(seed))
    engine.add_component_factory(GameCharacterFactory())
    engine.add_component_factory(RoutineFactory())
    engine.add_component_factory(LocationFactory())
    engine.add_component_factory(ResidenceFactory())
    engine.add_component_factory(Position2DFactory())
    engine.add_component_factory(LifeEventHandlerFactory())
    engine.add_component_factory(BusinessFactory())
    return engine


class NeighborlyConfig(BaseModel):
    simulation: SimulationConfig = Field(default_factory=lambda: SimulationConfig())
    plugins: List[NeighborlyPlugin] = Field(default_factory=lambda: [DefaultPlugin()])

    @staticmethod
    def merge(
        config_a: "NeighborlyConfig", config_b: "NeighborlyConfig"
    ) -> "NeighborlyConfig":
        """Merge config B into config A and return a new config"""
        ret = NeighborlyConfig()
        ret.simulation = SimulationConfig(
            **{**config_a.simulation.dict(), **config_b.simulation.dict()}
        )
        return ret
