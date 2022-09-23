from __future__ import annotations

import hashlib
import random
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from neighborly.builtin.systems import (
    BuildBusinessSystem,
    BuildResidenceSystem,
    BusinessUpdateSystem,
    CharacterAgingSystem,
    FindBusinessOwnerSystem,
    FindEmployeesSystem,
    LinearTimeSystem,
    PregnancySystem,
    RelationshipStatusSystem,
    RoutineSystem,
    SocializeSystem,
    SpawnResidentSystem,
    UnemploymentSystem,
)
from neighborly.core.ecs import ISystem, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import LifeEventLog, LifeEventSimulator
from neighborly.core.relationship import RelationshipGraph
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.core.town import LandGrid, Town

logger = getLogger(__name__)


class PluginSetupError(Exception):
    """Exception thrown when an error occurs while loading a plugin"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class Plugin(ABC):
    """
    Plugins are loaded before the simulation runs and can modify
    a Simulation's World instance to add new components, systems,
    resources, and entity archetypes.
    """

    @classmethod
    def get_name(cls) -> str:
        """Return the name of this plugin"""
        return cls.__name__

    @abstractmethod
    def setup(self, sim: Simulation, **kwargs) -> None:
        """Add the plugin data to the simulation"""
        raise NotImplementedError


TownSize = Union[Literal["small", "medium", "large"], Tuple[int, int]]


class Simulation:
    """
    A Neighborly simulation instance

    Attributes
    ----------
    world: World
        Entity-component system (ECS) that manages entities and procedures in the virtual world
    engine: NeighborlyEngine
        Engine instance used for PRNG and name generation
    seed: int
        The seed passed to the random number generator
    world_gen_start: SimDateTime
        The starting date for the simulation
    world_gen_end: SimDateTime
        The date that the simulation stops continuously updating and all following updates
        are manual calls to .step().
    """

    __slots__ = (
        "world",
        "engine",
        "seed",
        "world_gen_start",
        "world_gen_end",
    )

    def __init__(
        self,
        seed: int,
        world: World,
        engine: NeighborlyEngine,
        world_gen_start: SimDateTime,
        world_gen_end: SimDateTime,
    ) -> None:
        self.seed: int = seed
        self.world: World = world
        self.engine: NeighborlyEngine = engine
        self.world.add_resource(engine)
        self.world_gen_start: SimDateTime = world_gen_start
        self.world_gen_end: SimDateTime = world_gen_end

    def establish_setting(self) -> None:
        """Run the simulation until it reaches the end date in the config"""
        try:
            while self.world_gen_end >= self.time:
                self.step()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.step()

    @property
    def time(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    @property
    def town(self) -> Town:
        """Get a reference to the Town instance"""
        return self.world.get_resource(Town)


class SimulationBuilder:
    """
    Builder class for Neighborly Simulation instances

    Attributes
    ----------
    time_increment_hours: int
        How many hours should time advance each tick of the simulation
    world_gen_start: SimDateTime
        What date should the simulation start from
    world_gen_end: SimDateTime
        What date should the simulation stop automatically advancing time
    town_size: Tuple[int, int]
        Tuple containing the width and length of the grid of land the town is built on
    seed: int
        The value used to seed the random number generator
    systems: List[Tuple[ISystem, int]]
        The systems to add to the simulation instance and their associated priorities
    resources: List[Any]
        Resource instances to add to the simulation instance
    plugins: List[Tuple[Plugin, Dict[str, Any]]]
        Plugins to add to the simulation
    """

    __slots__ = (
        "time_increment_hours",
        "world_gen_start",
        "world_gen_end",
        "town_name",
        "town_size",
        "seed",
        "systems",
        "resources",
        "plugins",
    )

    def __init__(
        self,
        seed: Optional[Union[int, str]] = None,
        world_gen_start: Union[str, SimDateTime] = "0000-00-00",
        world_gen_end: Union[str, SimDateTime] = "0100-00-00",
        time_increment_hours: int = 12,
        town_name: str = "#town_name#",
        town_size: TownSize = "medium",
    ) -> None:
        self.seed: int = self._hash_seed(
            seed if seed is not None else random.randint(0, 99999999)
        )
        self.time_increment_hours: int = time_increment_hours
        self.world_gen_start: SimDateTime = (
            world_gen_start
            if isinstance(world_gen_start, SimDateTime)
            else SimDateTime.from_iso_str(world_gen_start)
        )
        self.world_gen_end: SimDateTime = (
            world_gen_end
            if isinstance(world_gen_end, SimDateTime)
            else SimDateTime.from_iso_str(world_gen_end)
        )
        self.town_name: str = town_name
        self.town_size: Tuple[int, int] = SimulationBuilder._convert_town_size(
            town_size
        )
        self.systems: List[Tuple[ISystem, int]] = []
        self.resources: List[Any] = []
        self.plugins: List[Tuple[Plugin, Dict[str, Any]]] = []

    def _hash_seed(self, seed: Union[str, int]) -> int:
        """Create an int hash from the given seed value"""
        return int.from_bytes(hashlib.sha256(str(seed)).digest()[:8], "little")

    def add_system(self, system: ISystem, priority: int = 0) -> SimulationBuilder:
        """Add a new system to the simulation"""
        self.systems.append((system, priority))
        return self

    def add_resource(self, resource: Any) -> SimulationBuilder:
        """Add a new resource to the simulation"""
        self.resources.append(resource)
        return self

    def add_plugin(self, plugin: Plugin, **kwargs) -> SimulationBuilder:
        """Add plugin to simulation"""
        self.plugins.append((plugin, {**kwargs}))
        return self

    def _create_town(
        self,
        sim: Simulation,
    ) -> SimulationBuilder:
        """Create a new grid of land to build the town on"""
        # create town
        sim.world.add_resource(Town.create(sim.world, name=self.town_name))

        # Create the land
        land_grid = LandGrid(self.town_size)

        sim.world.add_resource(land_grid)

        return self

    def build(
        self,
    ) -> Simulation:
        """Constructs the simulation and returns it"""
        sim = Simulation(
            seed=self.seed,
            world=World(),
            engine=NeighborlyEngine(),
            world_gen_start=self.world_gen_start,
            world_gen_end=self.world_gen_end,
        )

        self.add_resource(self.world_gen_start.copy())
        self.add_system(LinearTimeSystem(TimeDelta(hours=self.time_increment_hours)))
        self.add_system(LifeEventSimulator(interval=TimeDelta(months=1)))
        self.add_resource(LifeEventLog())
        self.add_system(BuildResidenceSystem(interval=TimeDelta(days=5)))
        self.add_system(SpawnResidentSystem(interval=TimeDelta(days=7)))
        self.add_system(BuildBusinessSystem(interval=TimeDelta(days=5)))
        self.add_resource(RelationshipGraph())
        self.add_system(CharacterAgingSystem())
        self.add_system(RoutineSystem(), 5)
        self.add_system(BusinessUpdateSystem())
        self.add_system(FindBusinessOwnerSystem())
        self.add_system(FindEmployeesSystem())
        self.add_system(UnemploymentSystem(days_to_departure=30))
        self.add_system(RelationshipStatusSystem())
        self.add_system(SocializeSystem())
        self.add_system(PregnancySystem())

        for system, priority in self.systems:
            sim.world.add_system(system, priority)

        for resource in self.resources:
            sim.world.add_resource(resource)

        for plugin, options in self.plugins:
            plugin.setup(sim, **options)
            logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")

        self._create_town(sim)

        return sim

    @staticmethod
    def _convert_town_size(town_size: TownSize) -> Tuple[int, int]:
        """Convert a TownSize to a tuple of ints"""
        if isinstance(town_size, tuple):
            land_size = town_size
        else:
            if town_size == "small":
                land_size = (3, 3)
            elif town_size == "medium":
                land_size = (5, 5)
            else:
                land_size = (7, 7)

        return land_size
