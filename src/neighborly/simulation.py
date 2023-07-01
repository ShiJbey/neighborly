from __future__ import annotations

import importlib
import os
import random
import re
import sys
from dataclasses import dataclass
from typing import Callable, Optional, Union

import neighborly.core.relationship as relationship
import neighborly.factories as factories
import neighborly.systems as systems
from neighborly.__version__ import VERSION
from neighborly.components.activity import Activities, ActivityLibrary, ActivityType
from neighborly.components.business import (
    Business,
    ClosedForBusiness,
    InTheWorkforce,
    JobRequirementLibrary,
    JobRequirements,
    Occupation,
    OccupationLibrary,
    OccupationType,
    OpenForBusiness,
    OperatingHours,
    ServiceLibrary,
    Services,
    SocialStatusLevel,
    WorkHistory,
)
from neighborly.components.character import (
    AgingConfig,
    CanAge,
    CanGetPregnant,
    Deceased,
    Departed,
    GameCharacter,
    Gender,
    LifeStage,
    MarriageConfig,
    Mortal,
    ReproductionConfig,
    Retired,
    RoleTracker,
    Virtues,
)
from neighborly.components.items import Item, ItemLibrary, ItemType
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.shared import (
    Age,
    Building,
    CurrentSettlement,
    Description,
    FrequentedBy,
    FrequentedLocations,
    Lifespan,
    Location,
    Name,
    Position2D,
)
from neighborly.components.spawn_table import (
    BusinessSpawnTable,
    CharacterSpawnTable,
    ResidenceSpawnTable,
)
from neighborly.config import NeighborlyConfig, PluginConfig
from neighborly.core.ai.brain import AIBrain, Goals
from neighborly.core.ecs import Active, GameObjectPrefab, World
from neighborly.core.life_event import EventHistory, EventLog, RandomLifeEventLibrary
from neighborly.core.location_bias import LocationBiasRuleLibrary
from neighborly.core.settlement import Settlement
from neighborly.core.status import StatusManager
from neighborly.core.time import SimDateTime, TimeDelta
from neighborly.core.tracery import Tracery
from neighborly.data_collection import DataCollector
from neighborly.event_listeners import (
    add_event_to_personal_history,
    deactivate_relationships_on_death,
    deactivate_relationships_on_depart,
    join_workforce_when_young_adult,
    on_adult_join_settlement,
    print_life_events,
)
from neighborly.events import (
    BecomeYoungAdultEvent,
    DeathEvent,
    DepartEvent,
    JoinSettlementEvent,
)
from neighborly.factories.activity import ActivitiesFactory
from neighborly.factories.business import (
    JobRequirementsFactory,
    OperatingHoursFactory,
    ServicesFactory,
)
from neighborly.factories.settlement import SettlementFactory
from neighborly.factories.shared import NameFactory
from neighborly.factories.spawn_table import (
    CharacterSpawnTableFactory,
    BusinessSpawnTableFactory,
    ResidenceSpawnTableFactory,
)


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

        # Seed RNG for libraries we don't control
        random.seed(self.config.seed)

        # Add default resources
        self.world.resource_manager.add_resource(self.config)
        self.world.resource_manager.add_resource(random.Random(self.config.seed))
        self.world.resource_manager.add_resource(self.config.start_date.copy())
        self.world.resource_manager.add_resource(Tracery(self.config.seed))
        self.world.resource_manager.add_resource(EventLog())
        self.world.resource_manager.add_resource(relationship.SocialRuleLibrary())
        self.world.resource_manager.add_resource(LocationBiasRuleLibrary())
        self.world.resource_manager.add_resource(DataCollector())
        self.world.resource_manager.add_resource(RandomLifeEventLibrary())
        self.world.resource_manager.add_resource(ItemLibrary())
        self.world.resource_manager.add_resource(OccupationLibrary())
        self.world.resource_manager.add_resource(JobRequirementLibrary())
        self.world.resource_manager.add_resource(ActivityLibrary())
        self.world.resource_manager.add_resource(ServiceLibrary())

        # Set the relationship schema
        self.world.gameobject_manager.add_prefab(
            GameObjectPrefab(
                name="relationship",
                components={**self.config.relationship_schema.components},
            )
        )

        # Add default top-level system groups (in execution order)
        self.world.system_manager.add_system(systems.InitializationSystemGroup())
        self.world.system_manager.add_system(systems.EarlyUpdateSystemGroup())
        self.world.system_manager.add_system(systems.UpdateSystemGroup())
        self.world.system_manager.add_system(systems.LateUpdateSystemGroup())

        # Initialization systems
        self.world.system_manager.add_system(
            systems.InitializeActivitiesSystem(),
            priority=9999,
            system_group=systems.InitializationSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.InitializeServicesSystem(),
            priority=9999,
            system_group=systems.InitializationSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.InitializeOccupationTypesSystem(),
            priority=9999,
            system_group=systems.InitializationSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.InitializeItemTypeSystem(),
            priority=9999,
            system_group=systems.InitializationSystemGroup,
        )

        # Add default early-update subgroups (in execution order)
        self.world.system_manager.add_system(
            systems.DataCollectionSystemGroup(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.StatusUpdateSystemGroup(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.GoalSuggestionSystemGroup(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.RelationshipUpdateSystemGroup(),
            system_group=systems.EarlyUpdateSystemGroup,
        )

        # Add early-update systems (in execution order)
        self.world.system_manager.add_system(
            systems.MeetNewPeopleSystem(), system_group=systems.EarlyUpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.RandomLifeEventSystem(), system_group=systems.EarlyUpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.UpdateFrequentedLocationSystem(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.AIRoutineSystem(), system_group=systems.GoalSuggestionSystemGroup
        )

        # Add relationship-update systems (in execution order)
        # self.world.systems.add_system(systems.EvaluateSocialRulesSystem())
        self.world.system_manager.add_system(
            systems.RelationshipUpdateSystem(),
            system_group=systems.RelationshipUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.FriendshipStatSystem(),
            system_group=systems.RelationshipUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.RomanceStatSystem(),
            system_group=systems.RelationshipUpdateSystemGroup,
        )

        # Add update systems (in execution order)
        self.world.system_manager.add_system(
            systems.CharacterAgingSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.AIActionSystem(), system_group=systems.UpdateSystemGroup
        )

        # Add status-update systems (in execution order)
        self.world.system_manager.add_system(
            systems.PregnantStatusSystem(), system_group=systems.StatusUpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.UnemployedStatusSystem(),
            system_group=systems.StatusUpdateSystemGroup,
        )

        # Time actually sits outside any group and runs last
        self.world.system_manager.add_system(systems.TimeSystem(), priority=-9999)

        # Register components
        self.world.gameobject_manager.register_component(Active)
        self.world.gameobject_manager.register_component(AIBrain)
        self.world.gameobject_manager.register_component(Goals)
        self.world.gameobject_manager.register_component(
            GameCharacter, factory=factories.GameCharacterFactory()
        )
        self.world.gameobject_manager.register_component(
            relationship.RelationshipManager
        )
        self.world.gameobject_manager.register_component(relationship.Relationship)
        self.world.gameobject_manager.register_component(relationship.Friendship)
        self.world.gameobject_manager.register_component(relationship.Romance)
        self.world.gameobject_manager.register_component(relationship.InteractionScore)
        self.world.gameobject_manager.register_component(Location)
        self.world.gameobject_manager.register_component(FrequentedBy)
        self.world.gameobject_manager.register_component(CurrentSettlement)
        self.world.gameobject_manager.register_component(
            Virtues, factory=factories.VirtuesFactory()
        )
        self.world.gameobject_manager.register_component(
            Activities, factory=ActivitiesFactory()
        )
        self.world.gameobject_manager.register_component(ActivityType)
        self.world.gameobject_manager.register_component(Occupation)
        self.world.gameobject_manager.register_component(WorkHistory)
        self.world.gameobject_manager.register_component(
            Services, factory=ServicesFactory()
        )
        self.world.gameobject_manager.register_component(ClosedForBusiness)
        self.world.gameobject_manager.register_component(OpenForBusiness)
        self.world.gameobject_manager.register_component(
            Business, factory=factories.BusinessFactory()
        )
        self.world.gameobject_manager.register_component(InTheWorkforce)
        self.world.gameobject_manager.register_component(Departed)
        self.world.gameobject_manager.register_component(CanAge)
        self.world.gameobject_manager.register_component(Mortal)
        self.world.gameobject_manager.register_component(CanGetPregnant)
        self.world.gameobject_manager.register_component(Deceased)
        self.world.gameobject_manager.register_component(Retired)
        self.world.gameobject_manager.register_component(Residence)
        self.world.gameobject_manager.register_component(Resident)
        self.world.gameobject_manager.register_component(Vacant)
        self.world.gameobject_manager.register_component(Building)
        self.world.gameobject_manager.register_component(Position2D)
        self.world.gameobject_manager.register_component(StatusManager)
        self.world.gameobject_manager.register_component(FrequentedLocations)
        self.world.gameobject_manager.register_component(
            Settlement, factory=SettlementFactory()
        )
        self.world.gameobject_manager.register_component(EventHistory)
        self.world.gameobject_manager.register_component(MarriageConfig)
        self.world.gameobject_manager.register_component(AgingConfig)
        self.world.gameobject_manager.register_component(ReproductionConfig)
        self.world.gameobject_manager.register_component(Name, factory=NameFactory())
        self.world.gameobject_manager.register_component(
            OperatingHours, factory=OperatingHoursFactory()
        )
        self.world.gameobject_manager.register_component(Lifespan)
        self.world.gameobject_manager.register_component(Age)
        self.world.gameobject_manager.register_component(
            CharacterSpawnTable, factory=CharacterSpawnTableFactory()
        )
        self.world.gameobject_manager.register_component(
            BusinessSpawnTable, factory=BusinessSpawnTableFactory()
        )
        self.world.gameobject_manager.register_component(
            ResidenceSpawnTable, factory=ResidenceSpawnTableFactory()
        )
        self.world.gameobject_manager.register_component(Gender)
        self.world.gameobject_manager.register_component(LifeStage)
        self.world.gameobject_manager.register_component(ItemType)
        self.world.gameobject_manager.register_component(Description)
        self.world.gameobject_manager.register_component(Item)
        self.world.gameobject_manager.register_component(OccupationType)
        self.world.gameobject_manager.register_component(SocialStatusLevel)
        self.world.gameobject_manager.register_component(
            JobRequirements, factory=JobRequirementsFactory()
        )
        self.world.gameobject_manager.register_component(RoleTracker)

        # Event listeners
        self.world.event_manager.on_event(JoinSettlementEvent, on_adult_join_settlement)
        self.world.event_manager.on_event(
            BecomeYoungAdultEvent, join_workforce_when_young_adult
        )
        self.world.event_manager.on_event(DeathEvent, deactivate_relationships_on_death)
        self.world.event_manager.on_event(
            DepartEvent, deactivate_relationships_on_depart
        )
        self.world.event_manager.on_any_event(add_event_to_personal_history)

        if self.config.verbose:
            self.world.event_manager.on_any_event(print_life_events)

        # Load plugins from the config
        for entry in self.config.plugins:
            self.load_plugin(entry)

    @property
    def date(self) -> SimDateTime:
        """The current date of the simulation."""
        return self.world.resource_manager.get_resource(SimDateTime)

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
            stop_date = self.world.resource_manager.get_resource(
                SimDateTime
            ).copy() + TimeDelta(years=time_delta)
        else:
            stop_date = (
                self.world.resource_manager.get_resource(SimDateTime).copy()
                + time_delta
            )

        self.run_until(stop_date)

    def run_until(self, stop_date: SimDateTime) -> None:
        """Run the simulation until a specific date is reached.

        Parameters
        ----------
        stop_date
            The date to stop stepping the simulation.
        """
        try:
            current_date = self.world.resource_manager.get_resource(SimDateTime)
            while stop_date > current_date:
                self.step()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep."""
        self.world.step()
