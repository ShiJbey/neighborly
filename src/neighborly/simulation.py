from __future__ import annotations

import importlib
import pathlib
import os
import sys
from dataclasses import dataclass
from logging import getLogger
from typing import Any, Dict, List, Optional, Union, Generator

from pydantic import BaseModel, Field
from tqdm import tqdm

import neighborly.core.utils.utilities as utilities
from neighborly.core.business import BusinessFactory
from neighborly.core.character import GameCharacterFactory
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEventLogger
from neighborly.core.location import LocationFactory
from neighborly.core.position import Position2DFactory
from neighborly.core.systems import (
    AddResidentsSystem,
    AdolescentSystem,
    AdultSystem,
    CharacterSystem,
    ChildSystem,
    LifeEventSystem,
    RoutineSystem,
    TimeSystem,
    YoungAdultSystem,
)
from neighborly.core.residence import ResidenceFactory
from neighborly.core.rng import DefaultRNG, IRandNumGenerator
from neighborly.core.routine import RoutineFactory
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import DAYS_PER_YEAR, HOURS_PER_DAY, SimDateTime, TimeDelta
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
    days_per_year: int
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
    path: str
        Path to the config file
    """

    quiet: bool = False
    simulation: SimulationConfig = Field(default_factory=lambda: SimulationConfig())
    plugins: List[Union[str, PluginConfig]] = Field(default_factory=list)
    path: str = "."

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

    __slots__ = "config", "world", "_lod_manager"

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
        engine.add_component_factory(BusinessFactory())
        self.world.add_resource(engine)
        # Add default systems
        self.world.add_system(TimeSystem(), 10)
        self.world.add_system(RoutineSystem(), 5)
        self.world.add_system(CharacterSystem(), 3)
        self.world.add_system(ChildSystem(), 3)
        self.world.add_system(AdolescentSystem(), 3)
        self.world.add_system(YoungAdultSystem(), 3)
        self.world.add_system(AdultSystem(), 3)
        self.world.add_system(LifeEventSystem())
        self.world.add_system(AddResidentsSystem())
        # Add default resources
        self.world.add_resource(SimDateTime())
        self.world.add_resource(RelationshipNetwork())
        self.world.add_resource(LifeEventLogger())
        # Load Plugins
        for plugin in config.plugins:
            if isinstance(plugin, str):
                self.load_plugin(plugin)
            else:
                plugin_path = os.path.join(
                    pathlib.Path(config.path).parent, plugin.path if plugin.path else ""
                )
                self.load_plugin(plugin.name, plugin_path, **plugin.options)
        # Create the town
        town = Town.create(config.simulation.town)
        logger.debug(f"Created town of {town.name}")
        self.world.add_resource(town)
        # Create the LOD manager
        self._lod_manager: Generator[int, None, None] = create_lod_generator(
            current_date=self.world.get_resource(SimDateTime),
            high_lod_step=self.config.simulation.hours_per_timestep,
            days_per_year=self.config.simulation.days_per_year,
            rng=self.world.get_resource(NeighborlyEngine).get_rng(),
            end_date=SimDateTime,
        )

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

        high_res_days = set(self._generate_sample_days(start_date, end_date, n=10))

        low_res_days = (end_date - start_date).total_days - len(high_res_days)

        total_timesteps = low_res_days + len(high_res_days) * (
            HOURS_PER_DAY // self.config.simulation.hours_per_timestep
        )

        try:
            for _ in tqdm(range(total_timesteps), disable=self.config.quiet is True):
                if self.get_time().to_ordinal() in high_res_days:
                    self.step(hours=self.config.simulation.hours_per_timestep)
                else:
                    self.step(hours=24)

        except KeyboardInterrupt:
            if self.config.quiet is False:
                print("Stopping Simulation")
                print(f"Current Date: {self.get_time().to_date_str()}")

    def step(self) -> None:
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
    ) -> List[int]:
        """Samples n days from each year between the start and end dates"""
        ordinal_start_date: int = start_date.to_ordinal()
        ordinal_end_date: int = end_date.to_ordinal()

        sampled_ordinal_dates: List[int] = []

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


def create_lod_generator(
    current_date: SimDateTime,
    high_lod_step: int,
    days_per_year: int,
    rng: IRandNumGenerator,
    end_date: Optional[SimDateTime] = None,
) -> Generator[int, None, None]:
    """
    Yields time step increments based on the current date,
    switching between low and high levels-of-detail.
    """
    while True:
        one_year_ahead = current_date.to_ordinal() + DAYS_PER_YEAR

        # Sample the fully simulated days for the next year
        high_res_days = set(
            rng.sample(
                range(current_date.to_ordinal(), one_year_ahead),
                days_per_year,
            )
        )

        while current_date.to_ordinal() < one_year_ahead:
            if current_date.to_ordinal() in high_res_days:
                current_date += TimeDelta(hours=high_lod_step)
                yield high_lod_step
            else:
                current_date += TimeDelta(hours=24)
                yield 24

            if end_date and current_date > end_date:
                return
