from __future__ import annotations

import importlib
import logging
import os
import pathlib
import random
import re
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import neighborly.core.relationship as relationship
import neighborly.systems as systems
from neighborly.__version__ import VERSION
from neighborly.components.business import (
    BossOf,
    Business,
    BusinessOwner,
    ClosedForBusiness,
    CoworkerOf,
    EmployeeOf,
    InTheWorkforce,
    Occupation,
    OpenForBusiness,
    Services,
    Unemployed,
    WorkHistory,
)
from neighborly.components.character import (
    CanAge,
    CanGetOthersPregnant,
    CanGetPregnant,
    Deceased,
    Departed,
    Female,
    GameCharacter,
    Gender,
    Immortal,
    LifeStage,
    Male,
    NonBinary,
    Retired,
    Virtues,
)
from neighborly.components.culture import Culture
from neighborly.components.items import Item, ItemLibrary, ItemType
from neighborly.components.residence import Residence, Resident, Vacant
from neighborly.components.role import Roles
from neighborly.components.shared import (
    Age,
    Building,
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Lifespan,
    Location,
    Name,
    Position2D,
)
from neighborly.components.species import Species
from neighborly.components.trait import TraitLibrary, Traits, register_trait
from neighborly.config import NeighborlyConfig, PluginConfig
from neighborly.core.ai.brain import AIBrain, Goals
from neighborly.core.ecs import Active, GameObjectPrefab, World
from neighborly.core.life_event import EventHistory, EventLog, RandomLifeEventLibrary
from neighborly.core.location_preference import LocationPreferenceRuleLibrary
from neighborly.core.settlement import Settlement
from neighborly.core.status import Statuses
from neighborly.core.time import SimDateTime
from neighborly.core.tracery import Tracery
from neighborly.data_collection import DataCollector
from neighborly.event_listeners import (
    add_event_to_personal_history,
    deactivate_relationships_on_death,
    deactivate_relationships_on_depart,
    join_workforce_when_young_adult,
    log_life_event,
    on_adult_join_settlement,
)
from neighborly.events import (
    BecomeYoungAdultEvent,
    DeathEvent,
    DepartEvent,
    JoinSettlementEvent,
)
from neighborly.factories.business import BusinessFactory, ServicesFactory
from neighborly.factories.character import (
    GameCharacterFactory,
    GenderFactory,
    VirtuesFactory,
)
from neighborly.factories.culture import CultureFactory
from neighborly.factories.settlement import SettlementFactory
from neighborly.factories.shared import NameFactory
from neighborly.factories.species import SpeciesFactory
from neighborly.factories.trait import TraitsFactory
from neighborly.spawn_table import (
    BusinessSpawnTable,
    CharacterSpawnTable,
    ResidenceSpawnTable,
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
        self.world.resource_manager.add_resource(SimDateTime())
        self.world.resource_manager.add_resource(Tracery(self.config.seed))
        self.world.resource_manager.add_resource(EventLog())
        self.world.resource_manager.add_resource(relationship.SocialRuleLibrary())
        self.world.resource_manager.add_resource(LocationPreferenceRuleLibrary())
        self.world.resource_manager.add_resource(DataCollector())
        self.world.resource_manager.add_resource(RandomLifeEventLibrary())
        self.world.resource_manager.add_resource(ItemLibrary())
        self.world.resource_manager.add_resource(TraitLibrary())
        self.world.resource_manager.add_resource(CharacterSpawnTable())
        self.world.resource_manager.add_resource(BusinessSpawnTable())
        self.world.resource_manager.add_resource(ResidenceSpawnTable())

        # Set the default relationship prefab
        self.world.gameobject_manager.add_prefab(
            GameObjectPrefab(
                name="relationship",
                components={
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {},
                },
            )
        )

        # Set the default settlement prefab
        self.world.gameobject_manager.add_prefab(
            GameObjectPrefab(
                name="settlement",
                components={
                    "Name": {
                        "value": self.config.settings.get("settlement_name", "#settlement_name#")
                    },
                    "Settlement": {
                        "width": self.config.settings.get("map_width", 5),
                        "length": self.config.settings.get("map_length", 5),
                    },
                    "Age": {},
                    "Location": {}
                },
            )
        )

        # Add default top-level system groups (in execution order)
        self.world.system_manager.add_system(systems.InitializationSystemGroup())
        self.world.system_manager.add_system(systems.EarlyUpdateSystemGroup())
        self.world.system_manager.add_system(systems.UpdateSystemGroup())
        self.world.system_manager.add_system(systems.LateUpdateSystemGroup())

        # Initialization systems
        self.world.system_manager.add_system(
            systems.InitializeItemTypeSystem(),
            priority=9999,
            system_group=systems.InitializationSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.InitializeSettlementSystem(),
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
            systems.MeetNewPeopleSystem(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.RandomLifeEventSystem(),
            system_group=systems.EarlyUpdateSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.UpdateFrequentedLocationSystem(),
            system_group=systems.EarlyUpdateSystemGroup,
        )

        # Add relationship-update systems (in execution order)
        self.world.system_manager.add_system(
            systems.EvaluateSocialRulesSystem(),
            system_group=systems.RelationshipUpdateSystemGroup,
        )

        # Goal suggestion systems
        self.world.system_manager.add_system(
            systems.DatingBreakUpSystem(),
            system_group=systems.GoalSuggestionSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.EndMarriageSystem(),
            system_group=systems.GoalSuggestionSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.MarriageSystem(), system_group=systems.GoalSuggestionSystemGroup
        )
        self.world.system_manager.add_system(
            systems.FindRomanceSystem(),
            system_group=systems.GoalSuggestionSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.FindOwnPlaceSystem(),
            system_group=systems.GoalSuggestionSystemGroup,
        )
        self.world.system_manager.add_system(
            systems.RetirementSystem(),
            system_group=systems.GoalSuggestionSystemGroup,
        )

        # Add update systems (in execution order)
        self.world.system_manager.add_system(
            systems.IncrementAgeSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.UpdateLifeStageSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.AIActionSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.DieOfOldAgeSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.GoOutOfBusinessSystem(), system_group=systems.UpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.PregnancySystem(), system_group=systems.UpdateSystemGroup
        )

        # Add status-update systems (in execution order)
        self.world.system_manager.add_system(
            systems.ChildBirthSystem(), system_group=systems.StatusUpdateSystemGroup
        )
        self.world.system_manager.add_system(
            systems.UnemployedStatusSystem(),
            system_group=systems.StatusUpdateSystemGroup,
        )

        # Time actually sits outside any group and runs last
        self.world.system_manager.add_system(systems.TimeSystem(), priority=-9999)

        # Register components
        self.world.gameobject_manager.register_component(Male)
        self.world.gameobject_manager.register_component(Female)
        self.world.gameobject_manager.register_component(NonBinary)
        self.world.gameobject_manager.register_component(Species, factory=SpeciesFactory())
        self.world.gameobject_manager.register_component(Culture, factory=CultureFactory())
        self.world.gameobject_manager.register_component(Active)
        self.world.gameobject_manager.register_component(AIBrain)
        self.world.gameobject_manager.register_component(Goals)
        self.world.gameobject_manager.register_component(
            GameCharacter, factory=GameCharacterFactory()
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
            Virtues, factory=VirtuesFactory()
        )
        self.world.gameobject_manager.register_component(Occupation)
        self.world.gameobject_manager.register_component(WorkHistory)
        self.world.gameobject_manager.register_component(
            Services, factory=ServicesFactory()
        )
        self.world.gameobject_manager.register_component(ClosedForBusiness)
        self.world.gameobject_manager.register_component(OpenForBusiness)
        self.world.gameobject_manager.register_component(
            Business, factory=BusinessFactory()
        )
        self.world.gameobject_manager.register_component(BusinessOwner)
        self.world.gameobject_manager.register_component(Unemployed)
        self.world.gameobject_manager.register_component(InTheWorkforce)
        self.world.gameobject_manager.register_component(BossOf)
        self.world.gameobject_manager.register_component(EmployeeOf)
        self.world.gameobject_manager.register_component(CoworkerOf)

        self.world.gameobject_manager.register_component(Departed)
        register_trait(self.world, CanAge)
        register_trait(self.world, CanGetPregnant)
        register_trait(self.world, CanGetOthersPregnant)
        register_trait(self.world, Immortal)
        self.world.gameobject_manager.register_component(Deceased)
        self.world.gameobject_manager.register_component(Retired)
        self.world.gameobject_manager.register_component(Residence)
        self.world.gameobject_manager.register_component(Resident)
        self.world.gameobject_manager.register_component(Vacant)
        self.world.gameobject_manager.register_component(Building)
        self.world.gameobject_manager.register_component(Position2D)
        self.world.gameobject_manager.register_component(Statuses)
        self.world.gameobject_manager.register_component(
            Traits, factory=TraitsFactory()
        )
        self.world.gameobject_manager.register_component(FrequentedLocations)
        self.world.gameobject_manager.register_component(
            Settlement, factory=SettlementFactory()
        )
        self.world.gameobject_manager.register_component(EventHistory)
        self.world.gameobject_manager.register_component(Name, factory=NameFactory())
        self.world.gameobject_manager.register_component(Lifespan)
        self.world.gameobject_manager.register_component(Age)
        self.world.gameobject_manager.register_component(Gender, factory=GenderFactory())
        self.world.gameobject_manager.register_component(LifeStage)
        self.world.gameobject_manager.register_component(ItemType)
        self.world.gameobject_manager.register_component(Item)
        self.world.gameobject_manager.register_component(Roles)

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

        if self.config.logging.logging_enabled:
            if self.config.logging.log_file_name is not None:
                # Output the logs to a file
                log_path = (
                    pathlib.Path(self.config.logging.log_directory)
                    / self.config.logging.log_file_name
                )

                logging.basicConfig(
                    filename=log_path,
                    encoding="utf-8",
                    level=self.config.logging.log_level,
                )
            else:
                logging.basicConfig(
                    level=self.config.logging.log_level,
                )

            self.world.event_manager.on_any_event(log_life_event)

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

    def run_for(self, years: int) -> None:
        """Run the simulation for a given number of simulated years.

        Parameters
        ----------
        years
            The number of years to run the simulation for.
        """
        try:
            for _ in range(years):
                self.step()
        except KeyboardInterrupt:
            print("\nStopping Simulation")

    def step(self) -> None:
        """Advance the simulation a single timestep."""
        self.world.step()
