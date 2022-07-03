from __future__ import annotations

import importlib
import os
import sys
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Dict, List, Literal, Optional, Protocol, Tuple, Union

from pydantic import BaseModel, Field

import neighborly.core.utils.utilities as utilities
from neighborly.core.ecs import ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.rng import DefaultRNG
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid

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
    days_per_year: int


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
    path: str
        Path to the config file
    """

    quiet: bool = False
    simulation: SimulationConfig
    plugins: List[Union[str, PluginConfig]] = Field(default_factory=list)
    path: str = "."

    @classmethod
    def from_partial(
        cls, data: Dict[str, Any], defaults: NeighborlyConfig
    ) -> NeighborlyConfig:
        """Construct new config from a default config and a partial set of parameters"""
        return cls(**utilities.merge(data, defaults.dict()))


class PluginSetupError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Plugin(ABC):
    @classmethod
    def get_name(cls) -> str:
        """Return the name of this plugin"""
        return cls.__name__

    @abstractmethod
    def setup(self, sim: Simulation, **kwargs) -> None:
        """Add the plugin data to the simulation"""
        raise NotImplementedError


class Simulation:
    """
    A Neighborly simulation instance

    Attributes
    ----------
    world: World
        Entity-component system (ECS) that manages entities and procedures in the virtual world
    """

    __slots__ = "world"

    def __init__(self, world: World, engine: NeighborlyEngine) -> None:
        self.world: World = world
        self.world.add_resource(engine)

    @classmethod
    def default(cls, seed: Optional[int] = None) -> Simulation:
        sim = Simulation(World(), NeighborlyEngine())
        if seed is None:
            sim.add_resource(DefaultRNG())
        else:
            sim.add_resource(DefaultRNG(seed))
        return sim

    def add_system(self, system: ISystem, priority: int = 0) -> Simulation:
        """Add a new system to the simulation"""
        self.world.add_system(system, priority)
        return self

    def add_setup_system(self, system: ISystem) -> Simulation:
        """Add a new setup system to the simulation"""
        self.world.add_setup_system(system)
        return self

    def add_resource(self, resource: Any) -> Simulation:
        """Add a new resource to the simulation"""
        self.world.add_resource(resource)
        return self

    def add_plugin(self, plugin: Union[str, PluginConfig, Plugin]) -> Simulation:
        """Add plugin to simulation"""
        if isinstance(plugin, str):
            self._dynamic_load_plugin(plugin)
        elif isinstance(plugin, PluginConfig):
            self._dynamic_load_plugin(plugin.name, plugin.path, **plugin.options)
        else:
            plugin.setup(self)
            logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")
        return self

    def _dynamic_load_plugin(
        self, module_name: str, path: Optional[str] = None, **kwargs
    ) -> None:
        """
        Load a plugin

        Parameters
        ----------
        module_name: str
            Name of module to load
        """
        path_prepended = False

        if path:
            path_prepended = True
            plugin_abs_path = os.path.abspath(path)
            sys.path.insert(0, plugin_abs_path)
            logger.debug(
                f"Temporarily added plugin path '{plugin_abs_path}' to sys.path"
            )

        try:
            plugin_module = importlib.import_module(module_name)
            plugin: Plugin = plugin_module.__dict__["get_plugin"]()
            plugin.setup(self, **kwargs)
            logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")
        except KeyError:
            raise PluginSetupError(
                f"'get_plugin' function not found for plugin: {module_name}"
            )
        finally:
            # Remove the given plugin path from the front
            # of the system path to prevent module resolution bugs
            if path_prepended:
                sys.path.pop(0)

    def create_land(
        self,
        size: Union[Literal["small", "medium", "large"], Tuple[int, int]] = "medium",
    ) -> Simulation:
        """Create a new grid of land to build the town on"""
        if self.world.has_resource(LandGrid):
            logger.error("Attempted to overwrite previously generated land grid")
            return self

        if isinstance(size, tuple):
            land_size = size
        else:
            if size == "small":
                land_size = (3, 3)
            elif size == "medium":
                land_size = (5, 5)
            else:
                land_size = (7, 7)

        land_grid = LandGrid(land_size)

        self.add_resource(land_grid)

        return self

    def establish_setting(self, start_date: SimDateTime, end_date: SimDateTime) -> None:
        """Run the simulation until it reaches the end date in the config"""
        self.world.add_resource(start_date)
        try:
            while end_date > self.get_time():
                self.step()
                print(f"{self.get_time().to_date_str()}", end="\r")
            print()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.run()

    def get_time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    def get_engine(self) -> NeighborlyEngine:
        """Get the NeighborlyEngine instance"""
        return self.world.get_resource(NeighborlyEngine)
