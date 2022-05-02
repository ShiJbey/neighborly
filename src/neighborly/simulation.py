from __future__ import annotations

import importlib
from logging import getLogger
import os
import sys
from dataclasses import dataclass
from typing import Any, List, Dict, Optional, Union

from pydantic import BaseModel, Field
from tqdm import tqdm

import neighborly.core.utils.utilities as utilities
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
)
from neighborly.core.residence import ResidenceFactory
from neighborly.core.rng import DefaultRNG
from neighborly.core.routine import RoutineFactory
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import HOURS_PER_DAY, SimDateTime, DAYS_PER_YEAR
from neighborly.core.town import Town, TownConfig

logger = getLogger(__name__)


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

    seed: int
    hours_per_timestep: int
    start_date: str
    end_date: str
    town: TownConfig = Field(default_factory=TownConfig)


class PluginConfig(BaseModel):
    """
    Settings for loading and constructing a plugin

    Attributes
    ----------
    name: str
        Name of the plugin to load
    options: Dict[str, Any]
        Parameters to pass to the plugin when constructing
        and loading it
    """

    name: str
    path: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class NeighborlyConfig(BaseModel):
    """
    Static configuration setting for the Neighborly

    Attributes
    ----------
    simulation: SimulationConfig
        Static configuration settings specifically for
        the simulation instance
    plugins: List[Union[str, PluginConfig]]
        Names of plugins to load or names combined with
        instantiation parameters
    """

    simulation: SimulationConfig = Field(default_factory=lambda: SimulationConfig())
    plugins: List[Union[str, PluginConfig]] = Field(default_factory=list)

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**utilities.merge(data, defaults.dict()))


@dataclass(frozen=True)
class PluginContext:
    engine: NeighborlyEngine
    world: World


class PluginSetupError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Simulation:
    """
    A Neighborly simulation instance

    Attributes
    ----------
    config: SimulationConfig
        Configuration settings for how the simulation
    world: World
        Entity-component system (ECS) that manages entities in the virtual world
    """

    __slots__ = "config", "world"

    def __init__(self, config: NeighborlyConfig) -> None:
        self.config: NeighborlyConfig = config
        self.world: World = World()
        # Create the default Engine configuration
        engine = NeighborlyEngine(DefaultRNG(config.simulation.seed))
        engine.add_component_factory(GameCharacterFactory())
        engine.add_component_factory(RoutineFactory())
        engine.add_component_factory(LocationFactory())
        engine.add_component_factory(ResidenceFactory())
        engine.add_component_factory(Position2DFactory())
        engine.add_component_factory(LifeEventHandlerFactory())
        engine.add_component_factory(BusinessFactory())
        self.world.add_resource(engine)
        # Add default systems
        self.world.add_system(TimeProcessor(), 10)
        self.world.add_system(RoutineProcessor(), 5)
        self.world.add_system(CharacterProcessor(), 3)
        self.world.add_system(SocializeProcessor(), 2)
        self.world.add_system(LifeEventProcessor())
        # Add default resources
        self.world.add_resource(SimDateTime())
        self.world.add_resource(RelationshipNetwork())
        self.world.add_resource(EventLog())
        # Load Plugins
        for plugin in config.plugins:
            if isinstance(plugin, str):
                self.load_plugin(plugin)
            else:
                self.load_plugin(plugin.name, plugin.path, **plugin.options)
        # Create the town
        town = Town.create(config.simulation.town)
        self.world.add_resource(town)

    def load_plugin(
        self, module_name: str, path: Optional[str] = None, **kwargs
    ) -> None:
        """
        Load a plugin

        Parameters
        ----------
        module_name: str
            Name of module to load
        """
        plugin_path: Optional[str] = kwargs.get("path")
        path_prepended = False

        if plugin_path:
            path_prepended = True
            sys.path.insert(0, os.path.abspath(plugin_path))
            logger.debug(f"Temporarily added plugin path '{plugin_path}' to sys.path")

        try:
            plugin_module = importlib.import_module(module_name, package=".")
            plugin_module.__dict__["setup"](
                PluginContext(engine=self.get_engine(), world=self.world), **kwargs
            )
        except KeyError:
            raise PluginSetupError(
                f"setup function not found for plugin: {module_name}"
            )
        finally:
            # Remove the given plugin path from the front
            # of the system path to prevent module resolution bugs
            if path_prepended:
                sys.path.pop(0)

    def run(self) -> None:
        """Run the simulation until it reaches the end date in the config"""
        start_date: SimDateTime = SimDateTime.from_iso_str(
            self.config.simulation.start_date
        )
        end_date: SimDateTime = SimDateTime.from_iso_str(
            self.config.simulation.end_date
        )

        high_res_days = set(self._generate_sample_days(start_date, end_date, n=36))

        low_res_days = (end_date - start_date).total_days - len(high_res_days)

        total_timesteps = low_res_days + len(high_res_days) * (
            HOURS_PER_DAY // self.config.simulation.hours_per_timestep
        )

        try:
            for _ in tqdm(range(total_timesteps)):
                if self.get_time().to_ordinal() in high_res_days:
                    self.step(hours=self.config.simulation.hours_per_timestep)
                else:
                    self.step(hours=24)

        except KeyboardInterrupt:
            print("Stopping Simulation")
        finally:
            print(f"Current Date: {self.get_time().to_date_str()}")

    def step(self, hours: int, **kwargs) -> None:
        """Advance the simulation a single timestep"""
        self.world.process(delta_time=hours, **kwargs)

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    def get_town(self) -> Town:
        """Get the Town instance"""
        return self.world.get_resource(Town)

    def get_engine(self) -> NeighborlyEngine:
        """Get the NeighborlyEngine instance"""
        return self.world.get_resource(NeighborlyEngine)

    def _generate_sample_days(
        self, start_date: SimDateTime, end_date: SimDateTime, n: int
    ) -> list[int]:
        """Samples n days from each year between the start and end dates"""
        ordinal_start_date: int = start_date.to_ordinal()
        ordinal_end_date: int = end_date.to_ordinal()

        sampled_ordinal_dates: list[int] = []

        current_date = ordinal_start_date

        while current_date < ordinal_end_date:
            sampled_dates = (
                self.get_engine()
                .get_rng()
                .sample(range(current_date, current_date + DAYS_PER_YEAR), n)
            )
            sampled_ordinal_dates.extend(sorted(sampled_dates))
            current_date = min(current_date + DAYS_PER_YEAR, ordinal_end_date)

        return sampled_ordinal_dates
