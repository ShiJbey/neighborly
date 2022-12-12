from __future__ import annotations

import random
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from neighborly import constants
from neighborly.components.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
    Services,
    WorkHistory,
)
from neighborly.components.character import (
    CanAge,
    CanDie,
    CanGetPregnant,
    CharacterAgingConfig,
    CollegeGraduate,
    Deceased,
    Departed,
    GameCharacter,
    Gender,
    LifeStage,
    PersonalValues,
    Retired,
)
from neighborly.components.factory import (
    BusinessFactory,
    GameCharacterFactory,
    GenderFactory,
    PersonalValuesFactory,
    RoutineFactory,
    ServicesFactory,
)
from neighborly.components.relationship import Relationships
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.routine import Routine
from neighborly.components.shared import (
    Active,
    Age,
    Building,
    CurrentLocation,
    Lifespan,
    Location,
    LocationAliases,
    MaxCapacity,
    OpenToPublic,
    Position2D,
)
from neighborly.core.ai import MovementAI, SocialAI
from neighborly.core.ecs import ISystem, World
from neighborly.core.event import EventLog
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.settlement import Settlement, create_grid_settlement
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.engine import NeighborlyEngine
from neighborly.systems import (
    DynamicLoDTimeSystem,
    EventSystem,
    LifeEventSystem,
    LinearTimeSystem,
    MovementAISystem,
    SocialAISystem,
    StatusSystem,
)

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
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
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
    starting_date: SimDateTime
        The starting date for the simulation
    """

    __slots__ = (
        "world",
        "engine",
        "seed",
        "starting_date",
    )

    def __init__(
        self,
        seed: int,
        world: World,
        engine: NeighborlyEngine,
        starting_date: SimDateTime,
    ) -> None:
        self.seed: int = seed
        self.world: World = world
        self.engine: NeighborlyEngine = engine
        self.world.add_resource(engine)
        self.starting_date: SimDateTime = starting_date

    def run_for(self, years: int) -> None:
        """Run the simulation for a given number of years"""
        stop_date = self.date.copy() + TimeDelta(years=years)
        self.run_until(stop_date)

    def run_until(self, stop_date: SimDateTime) -> None:
        """Run the simulation until a specific date is reached"""
        try:
            while stop_date >= self.date:
                self.step()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep"""
        self.world.step()

    @property
    def date(self) -> SimDateTime:
        """Get the simulated DateTime instance used by the simulation"""
        return self.world.get_resource(SimDateTime)

    @property
    def town(self) -> Settlement:
        """Get a reference to the Town instance"""
        return self.world.get_resource(Settlement)


class Neighborly:
    """
    Builder class for Neighborly Simulation instances

    Attributes
    ----------
    time_increment_hours: int
        How many hours should time advance each tick of the simulation
    starting_date: SimDateTime
        What date should the simulation start from
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
        "starting_date",
        "town_name",
        "town_size",
        "seed",
        "systems",
        "resources",
        "plugins",
        "print_events",
        "life_event_interval_hours",
        "enable_dynamic_lod",
        "dyn_lod_days_per_year",
    )

    def __init__(
        self,
        seed: Optional[Union[int, str]] = None,
        starting_date: Union[str, SimDateTime] = "0000-00-00",
        time_increment_hours: int = 12,
        town_name: str = "#town_name#",
        town_size: TownSize = "medium",
        print_events: bool = True,
        life_event_interval_hours: int = 336,
        enable_dynamic_lod: bool = False,
        dyn_lod_days_per_year: int = 20,
    ) -> None:
        self.seed: int = hash(seed if seed is not None else random.randint(0, 99999999))
        self.time_increment_hours: int = time_increment_hours
        self.starting_date: SimDateTime = (
            starting_date
            if isinstance(starting_date, SimDateTime)
            else SimDateTime.from_iso_str(starting_date)
        )
        self.town_name: str = town_name
        self.town_size: Tuple[int, int] = Neighborly._convert_town_size(town_size)
        self.systems: List[Tuple[ISystem, int]] = []
        self.resources: List[Any] = []
        self.plugins: List[Tuple[Plugin, Dict[str, Any]]] = []
        self.print_events: bool = print_events
        self.life_event_interval_hours: int = life_event_interval_hours
        self.enable_dynamic_lod: bool = enable_dynamic_lod
        self.dyn_lod_days_per_year: int = dyn_lod_days_per_year

    def add_plugin(self, plugin: Plugin, **kwargs: Any) -> Neighborly:
        """Add plugin to simulation"""
        self.plugins.append((plugin, {**kwargs}))
        return self

    def _create_town(
        self,
        sim: Simulation,
    ) -> Neighborly:
        """Create a new Settlement to represent the Town"""
        generated_name = sim.world.get_resource(
            NeighborlyEngine
        ).name_generator.get_name(self.town_name)

        sim.world.add_resource(create_grid_settlement(generated_name, self.town_size))

        return self

    def build(
        self,
    ) -> Simulation:
        """Constructs the simulation and returns it"""
        sim = Simulation(
            seed=self.seed,
            world=World(),
            engine=NeighborlyEngine(),
            starting_date=self.starting_date,
        )

        # These resources are required by all games
        sim.world.add_resource(random.Random(self.seed))
        sim.world.add_resource(TraceryNameFactory())
        sim.world.add_resource(self.starting_date.copy())
        sim.world.add_resource(EventLog())

        # The following systems are loaded by default
        if self.enable_dynamic_lod:
            sim.world.add_system(
                DynamicLoDTimeSystem(
                    self.dyn_lod_days_per_year,
                    low_lod_time_increment=TimeDelta(hours=self.time_increment_hours),
                    high_lod_time_increment=TimeDelta(hours=24),
                ),
                constants.TIME_UPDATE_PHASE,
            )
        else:
            sim.world.add_system(
                LinearTimeSystem(TimeDelta(hours=self.time_increment_hours)),
                constants.TIME_UPDATE_PHASE,
            )
        sim.world.add_system(StatusSystem(), constants.CHARACTER_UPDATE_PHASE)
        sim.world.add_system(MovementAISystem(), constants.CHARACTER_ACTION_PHASE)
        sim.world.add_system(SocialAISystem(), constants.CHARACTER_ACTION_PHASE)
        sim.world.add_system(
            LifeEventSystem(interval=TimeDelta(hours=self.life_event_interval_hours)),
            constants.TOWN_SYSTEMS_PHASE,
        )
        sim.world.add_system(EventSystem(), constants.CLEAN_UP_PHASE)

        # Register all the built-in components
        sim.engine.register_component(Occupation)
        sim.engine.register_component(WorkHistory)
        sim.engine.register_component(Services, factory=ServicesFactory())
        sim.engine.register_component(ClosedForBusiness)
        sim.engine.register_component(OpenForBusiness)
        sim.engine.register_component(Business, factory=BusinessFactory())
        sim.engine.register_component(InTheWorkforce)
        sim.engine.register_component(Departed)
        sim.engine.register_component(CanAge)
        sim.engine.register_component(CanDie)
        sim.engine.register_component(CanGetPregnant)
        sim.engine.register_component(Deceased)
        sim.engine.register_component(Retired)
        sim.engine.register_component(CollegeGraduate)
        sim.engine.register_component(PersonalValues, factory=PersonalValuesFactory())
        sim.engine.register_component(GameCharacter, factory=GameCharacterFactory())
        sim.engine.register_component(CharacterAgingConfig)
        sim.engine.register_component(LifeStage)
        sim.engine.register_component(Gender, factory=GenderFactory())
        sim.engine.register_component(Relationships)
        sim.engine.register_component(Residence)
        sim.engine.register_component(Resident)
        sim.engine.register_component(Vacant)
        sim.engine.register_component(Routine, factory=RoutineFactory())
        sim.engine.register_component(Age)
        sim.engine.register_component(Lifespan)
        sim.engine.register_component(Building)
        sim.engine.register_component(Location)
        sim.engine.register_component(MaxCapacity)
        sim.engine.register_component(OpenToPublic)
        sim.engine.register_component(CurrentLocation)
        sim.engine.register_component(LocationAliases)
        sim.engine.register_component(Position2D)
        sim.engine.register_component(Active)
        sim.engine.register_component(MovementAI)
        sim.engine.register_component(SocialAI)

        for plugin, options in self.plugins:
            plugin.setup(sim, **options)
            logger.debug(f"Successfully loaded plugin: {plugin.get_name()}")

        if self.print_events:
            sim.world.get_resource(EventLog).subscribe(lambda e: print(str(e)))

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
