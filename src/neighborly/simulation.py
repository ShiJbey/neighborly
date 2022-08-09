from __future__ import annotations

import random
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Literal, Optional, Tuple, Union

from neighborly.builtin.systems import (
    BuildBusinessSystem,
    BuildResidenceSystem,
    BusinessUpdateSystem,
    CharacterAgingSystem,
    FindBusinessOwnerSystem,
    FindEmployeesSystem,
    LinearTimeSystem,
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


TownSize = Union[Literal["small", "medium", "large"], Tuple[int, int]]


class Simulation:
    """
    A Neighborly simulation instance

    Attributes
    ----------
    world: World
        Entity-component system (ECS) that manages entities and procedures in the virtual world
    """

    __slots__ = (
        "world",
        "engine",
        "seed",
        "world_gen_start",
        "world_gen_end",
        "town_size",
        "town_name",
    )

    def __init__(
        self,
        seed: int,
        world: World,
        engine: NeighborlyEngine,
        world_gen_start: SimDateTime,
        world_gen_end: SimDateTime,
        town_size: TownSize,
        town_name: str = None,
    ) -> None:
        self.seed: int = seed
        self.world: World = world
        self.engine: NeighborlyEngine = engine
        self.world.add_resource(engine)
        self.world_gen_start: SimDateTime = world_gen_start
        self.world_gen_end: SimDateTime = world_gen_end
        self.town_size: TownSize = town_size
        self.town_name: Optional[str] = town_name

    @classmethod
    def create(
        cls,
        seed: Optional[int] = None,
        world_gen_start: Union[str, SimDateTime] = "0000-00-00",
        world_gen_end: Union[str, SimDateTime] = "0100-00-00",
        time_increment_hours: int = 12,
        town_name: str = "#town_name#",
        town_size: TownSize = "medium",
    ) -> Simulation:
        """Creates an instance of a Neighborly simulation with an empty world and engine"""
        seed = seed if seed is not None else random.randint(0, 99999999)

        start_date = (
            world_gen_start
            if isinstance(world_gen_start, SimDateTime)
            else SimDateTime.from_iso_str(world_gen_start)
        )

        end_date = (
            world_gen_end
            if isinstance(world_gen_end, SimDateTime)
            else SimDateTime.from_iso_str(world_gen_end)
        )

        sim = (
            Simulation(
                seed,
                World(),
                NeighborlyEngine(seed),
                start_date,
                end_date,
                town_size=town_size,
                town_name=town_name,
            )
            .add_resource(start_date.copy())
            .add_system(LinearTimeSystem(TimeDelta(hours=time_increment_hours)))
            .add_system(LifeEventSimulator(interval=TimeDelta(months=1)))
            .add_resource(LifeEventLog())
            .add_system(BuildResidenceSystem(interval=TimeDelta(days=5)))
            .add_system(SpawnResidentSystem(interval=TimeDelta(days=7)))
            .add_system(BuildBusinessSystem(interval=TimeDelta(days=5)))
            .add_resource(RelationshipGraph())
            .add_system(CharacterAgingSystem())
            .add_system(RoutineSystem(), 5)
            .add_system(BusinessUpdateSystem())
            .add_system(FindBusinessOwnerSystem())
            .add_system(FindEmployeesSystem())
            .add_system(UnemploymentSystem(days_to_departure=30))
            .add_system(RelationshipStatusSystem())
            .add_system(SocializeSystem())
        )

        return sim

    def add_system(self, system: ISystem, priority: int = 0) -> Simulation:
        """Add a new system to the simulation"""
        self.world.add_system(system, priority)
        return self

    def add_resource(self, resource: Any) -> Simulation:
        """Add a new resource to the simulation"""
        self.world.add_resource(resource)
        return self

    def add_plugin(self, plugin: Plugin, **kwargs) -> Simulation:
        """Add plugin to simulation"""
        plugin.setup(self, **kwargs)
        logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")
        return self

    def _create_town(
        self,
        name: str,
    ) -> Simulation:
        """Create a new grid of land to build the town on"""
        if self.world.has_resource(LandGrid) or self.world.has_resource(Town):
            logger.error("Attempted to overwrite previously created town")
            return self

        # create town
        self.add_resource(Town.create(self.world, name=name))

        # Create the land
        if isinstance(self.town_size, tuple):
            land_size = self.town_size
        else:
            if self.town_size == "small":
                land_size = (3, 3)
            elif self.town_size == "medium":
                land_size = (5, 5)
            else:
                land_size = (7, 7)

        land_grid = LandGrid(land_size)

        self.add_resource(land_grid)

        return self

    def establish_setting(self) -> None:
        """Run the simulation until it reaches the end date in the config"""
        self._create_town(self.town_name if self.town_name else "#town_name#")

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
