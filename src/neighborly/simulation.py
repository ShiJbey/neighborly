from __future__ import annotations

import importlib
import os
import random
import re
import sys
from dataclasses import dataclass
from typing import Any, Callable, Optional, Type, Union

import neighborly.components as components
import neighborly.core.relationship as relationship
from neighborly.core.tracery import Tracery
import neighborly.factories as factories
import neighborly.systems as systems
from neighborly.__version__ import VERSION
from neighborly.config import NeighborlyConfig, PluginConfig
from neighborly.core.ai.brain import AIBrain, Goals
from neighborly.core.ecs import (
    Active,
    Component,
    EntityPrefab,
    GameObject,
    GameObjectFactory,
    IComponentFactory,
    ISystem,
    World,
)
from neighborly.core.life_event import AllEvents, EventHistory
from neighborly.core.settlement import Settlement
from neighborly.core.status import StatusManager
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.data_collection import DataCollector
from neighborly.event_listeners import (
    add_event_to_personal_history,
    deactivate_relationships_on_death,
    deactivate_relationships_on_depart,
    join_workforce_when_young_adult,
    on_adult_join_settlement,
)
from neighborly.events import (
    BecomeYoungAdultEvent,
    DeathEvent,
    DepartEvent,
    JoinSettlementEvent,
)
from neighborly.factories.settlement import SettlementFactory
from neighborly.factories.shared import NameFactory


class PluginSetupError(Exception):
    """Exception thrown when an error occurs while loading a plugin"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)


@dataclass
class PluginInfo:
    """Metadata for Neighborly plugins"""

    name: str
    """A display name"""

    plugin_id: str
    """A unique ID that differentiates this plugin from other plugins"""

    version: str
    """The plugin's version number in the form MAJOR.MINOR.PATCH"""

    required_version: Optional[str] = None
    """The version of Neighborly required to load the plugin"""


class Neighborly:
    """Main entry class for running Neighborly simulations."""

    __slots__ = "world", "config"

    world: World
    """Entity-component system (ECS) that manages the virtual world."""

    config: NeighborlyConfig
    """Configuration settings for the simulation."""

    def __init__(self, config: Optional[NeighborlyConfig] = None) -> None:
        """
        Parameters
        ----------
        config
            Configuration settings for the simulation.
        """
        self.world = World()
        self.config = config if config else NeighborlyConfig()

        # Seed RNG for libraries we don't control, like Tracery
        random.seed(self.config.seed)
        Tracery.set_rng_seed(self.config.seed)

        # Set the relationship schema
        GameObjectFactory.add(
            EntityPrefab(
                name="relationship",
                components={**self.config.relationship_schema.components},
            )
        )

        # Add default resources
        self.world.add_resource(self.config)
        self.world.add_resource(random.Random(self.config.seed))
        self.world.add_resource(self.config.start_date.copy())
        self.world.add_resource(AllEvents())
        self.world.add_resource(DataCollector())

        # Add default top-level system groups (in execution order)
        self.world.add_system(systems.InitializationSystemGroup())
        self.world.add_system(systems.EarlyUpdateSystemGroup())
        self.world.add_system(systems.UpdateSystemGroup())
        self.world.add_system(systems.LateUpdateSystemGroup())

        # Add default early-update subgroups (in execution order)
        self.world.add_system(systems.DataCollectionSystemGroup())
        self.world.add_system(systems.StatusUpdateSystemGroup())
        self.world.add_system(systems.GoalSuggestionSystemGroup())
        self.world.add_system(systems.RelationshipUpdateSystemGroup())

        # Add early-update systems (in execution order)
        self.world.add_system(systems.MeetNewPeopleSystem())
        self.world.add_system(systems.RandomLifeEventSystem())
        self.world.add_system(systems.UpdateFrequentedLocationSystem())
        self.world.add_system(systems.AIRoutineSystem())

        # Add relationship-update systems (in execution order)
        # self.world.add_system(systems.EvaluateSocialRulesSystem())
        self.world.add_system(systems.RelationshipUpdateSystem())
        self.world.add_system(systems.FriendshipStatSystem())
        self.world.add_system(systems.RomanceStatSystem())

        # Add update systems (in execution order)
        self.world.add_system(systems.CharacterAgingSystem())
        self.world.add_system(systems.AIActionSystem())

        # Add status-update systems (in execution order)
        self.world.add_system(systems.PregnantStatusSystem())
        self.world.add_system(systems.UnemployedStatusSystem())

        if self.config.verbose:
            AllEvents.on_event(lambda event: print(str(event)))

        # Time actually sits outside any group and runs last
        self.world.add_system(systems.TimeSystem())

        # Register components
        self.world.register_component(Active)
        self.world.register_component(AIBrain)
        self.world.register_component(Goals)
        self.world.register_component(
            components.GameCharacter, factory=factories.GameCharacterFactory()
        )
        self.world.register_component(relationship.RelationshipManager)
        self.world.register_component(relationship.Relationship)
        self.world.register_component(relationship.Friendship)
        self.world.register_component(relationship.Romance)
        self.world.register_component(relationship.InteractionScore)
        self.world.register_component(components.Location)
        self.world.register_component(components.FrequentedBy)
        self.world.register_component(components.CurrentSettlement)
        self.world.register_component(
            components.Virtues, factory=factories.VirtuesFactory()
        )
        self.world.register_component(components.Activities)
        self.world.register_component(components.Occupation)
        self.world.register_component(components.WorkHistory)
        self.world.register_component(components.Services)
        self.world.register_component(components.ClosedForBusiness)
        self.world.register_component(components.OpenForBusiness)
        self.world.register_component(
            components.Business, factory=factories.BusinessFactory()
        )
        self.world.register_component(components.InTheWorkforce)
        self.world.register_component(components.Departed)
        self.world.register_component(components.CanAge)
        self.world.register_component(components.Mortal)
        self.world.register_component(components.CanGetPregnant)
        self.world.register_component(components.Deceased)
        self.world.register_component(components.Retired)
        self.world.register_component(components.Residence)
        self.world.register_component(components.Resident)
        self.world.register_component(components.Vacant)
        self.world.register_component(components.Building)
        self.world.register_component(components.Position2D)
        self.world.register_component(StatusManager)
        self.world.register_component(components.FrequentedLocations)
        self.world.register_component(Settlement, factory=SettlementFactory())
        self.world.register_component(EventHistory)
        self.world.register_component(components.MarriageConfig)
        self.world.register_component(components.AgingConfig)
        self.world.register_component(components.ReproductionConfig)
        self.world.register_component(components.Name, factory=NameFactory())
        self.world.register_component(components.OperatingHours)
        self.world.register_component(components.Lifespan)
        self.world.register_component(components.Age)
        self.world.register_component(components.CharacterSpawnTable)
        self.world.register_component(components.BusinessSpawnTable)
        self.world.register_component(components.ResidenceSpawnTable)
        self.world.register_component(components.Gender)
        self.world.register_component(components.LifeStage)

        # Event listeners
        GameObject.on(JoinSettlementEvent, on_adult_join_settlement)
        GameObject.on(BecomeYoungAdultEvent, join_workforce_when_young_adult)
        GameObject.on(DeathEvent, deactivate_relationships_on_death)
        GameObject.on(DepartEvent, deactivate_relationships_on_depart)
        GameObject.on_any(add_event_to_personal_history)

        # Load plugins from the config
        for entry in self.config.plugins:
            self.load_plugin(entry)

    @property
    def date(self) -> SimDateTime:
        """The current date of the simulation."""
        return self.world.get_resource(SimDateTime)

    def load_plugin(self, plugin: PluginConfig) -> None:
        """Load a plugin.

        Parameters
        ----------
        plugin
            Configuration data for a plugin to load.
        """

        plugin_abs_path = os.path.abspath(plugin.path)
        sys.path.insert(0, plugin_abs_path)

        plugin_module = importlib.import_module(plugin.name)
        plugin_info: Optional[PluginInfo] = getattr(plugin_module, "plugin_info", None)
        plugin_setup_fn: Optional[Callable[[Neighborly], None]] = getattr(
            plugin_module, "setup", None
        )

        if plugin_info is None:
            raise PluginSetupError(
                f"Cannot find 'plugin_info' dict in plugin: {plugin.name}."
            )

        if plugin_setup_fn is None:
            raise PluginSetupError(
                f"'setup' function not found for plugin: {plugin.name}"
            )

        if not callable(plugin_setup_fn):
            raise PluginSetupError(
                f"'setup' function is not callable in plugin: {plugin.name}"
            )

        if plugin_info.required_version is not None:
            if re.fullmatch(r"^<=[0-9]+.[0-9]+.[0-9]+$", plugin_info.required_version):
                if VERSION > plugin_info.required_version:
                    raise PluginSetupError(
                        f"Plugin {plugin_info.name} requires {plugin_info.required_version}"
                    )
            elif re.fullmatch(
                r"^>=[0-9]+.[0-9]+.[0-9]+$", plugin_info.required_version
            ):
                if VERSION < plugin_info.required_version:
                    raise PluginSetupError(
                        f"Plugin {plugin_info.name} requires {plugin_info.required_version}"
                    )
            elif re.fullmatch(r"^>[0-9]+.[0-9]+.[0-9]+$", plugin_info.required_version):
                if VERSION <= plugin_info.required_version:
                    raise PluginSetupError(
                        f"Plugin {plugin_info.name} requires {plugin_info.required_version}"
                    )
            elif re.fullmatch(r"^<[0-9]+.[0-9]+.[0-9]+$", plugin_info.required_version):
                if VERSION > plugin_info.required_version:
                    raise PluginSetupError(
                        f"Plugin {plugin_info.name} requires {plugin_info.required_version}"
                    )
            elif re.fullmatch(
                r"^==[0-9]+.[0-9]+.[0-9]+$", plugin_info.required_version
            ):
                if VERSION != plugin_info.required_version:
                    raise PluginSetupError(
                        f"Plugin {plugin_info.name} requires {plugin_info.required_version}"
                    )

        plugin_setup_fn(self)

        # Remove the given plugin path from the front
        # of the system path to prevent module resolution bugs
        sys.path.pop(0)

    def run_for(self, time_delta: Union[int, TimeDelta]) -> None:
        """Run the simulation for a given number of simulated years.

        Parameters
        ----------
        time_delta
            Simulated years to run the simulation for.
        """
        if isinstance(time_delta, int):
            stop_date = self.world.get_resource(SimDateTime).copy() + TimeDelta(
                years=time_delta
            )
        else:
            stop_date = self.world.get_resource(SimDateTime).copy() + time_delta

        self.run_until(stop_date)

    def run_until(self, stop_date: SimDateTime) -> None:
        """Run the simulation until a specific date is reached.

        Parameters
        ----------
        stop_date
            The date to stop stepping the simulation.
        """
        try:
            current_date = self.world.get_resource(SimDateTime)
            while stop_date > current_date:
                self.step()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep."""
        self.world.step()

    def register_component(
        self,
        component_type: Type[Component],
        name: Optional[str] = None,
        factory: Optional[IComponentFactory] = None,
    ) -> None:
        """Register a component type with the  simulation.

        Registers a component class type with the simulation's World instance.
        This allows content authors to use the Component in YAML files and
        EntityPrefabs.

        Parameters
        ----------
        component_type
            The type of component to add
        name
            A name to register the component type under (defaults to name of class)
        factory
            A factory instance used to construct this component type
            (defaults to DefaultComponentFactory())
        """

        self.world.register_component(component_type, name, factory)

    def add_resource(self, resource: Any) -> None:
        """Add a shared resource.

        Parameters
        ----------
        resource
            An instance of the shared resource.
        """

        self.world.add_resource(resource)

    def add_system(self, system: ISystem) -> None:
        """Add a simulation system.

        Parameters
        ----------
        system
            The system to add.
        """

        self.world.add_system(system)
