"""The main simulation class.

This module contains class definitions for creating simulation instances.

"""

from __future__ import annotations

import json
import logging
import pathlib
import random
from typing import Optional

from neighborly.config import SimulationConfig
from neighborly.datetime import SimDate
from neighborly.defs.defaults import (
    DefaultBusinessDef,
    DefaultCharacterDef,
    DefaultDistrictDef,
    DefaultJobRoleDef,
    DefaultResidenceDef,
    DefaultSettlementDef,
    DefaultSkillDef,
    DefaultSpeciesDef,
    DefaultTraitDef,
    default_district_name_factory,
    default_settlement_name_factory,
    generate_any_first_name,
    generate_feminine_first_name,
    generate_last_name,
    generate_masculine_first_name,
)
from neighborly.ecs import World
from neighborly.factories.business import BusinessFactory
from neighborly.factories.character import CharacterFactory
from neighborly.factories.location import (
    FrequentedLocationsFactory,
    LocationFactory,
    LocationPreferencesFactory,
)
from neighborly.factories.settlement import DistrictFactory, SettlementFactory
from neighborly.factories.shared import AgeFactory, AgentFactory
from neighborly.factories.skills import SkillsFactory
from neighborly.factories.spawn_table import (
    BusinessSpawnTableFactory,
    CharacterSpawnTableFactory,
    ResidenceSpawnTableFactory,
)
from neighborly.factories.stats import StatsFactory
from neighborly.factories.traits import TraitsFactory
from neighborly.libraries import (
    ActionConsiderationLibrary,
    BusinessLibrary,
    BusinessNameFactories,
    CharacterLibrary,
    CharacterNameFactories,
    DistrictLibrary,
    DistrictNameFactories,
    JobRoleLibrary,
    LocationPreferenceLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SettlementNameFactories,
    SkillLibrary,
    SocialRuleLibrary,
    TraitLibrary,
)
from neighborly.life_event import GlobalEventHistory
from neighborly.systems import (
    AgingSystem,
    BusinessLifespanSystem,
    CharacterLifespanSystem,
    ChildBirthSystem,
    CompileBusinessDefsSystem,
    CompileCharacterDefsSystem,
    CompileDistrictDefsSystem,
    CompileJobRoleDefsSystem,
    CompileResidenceDefsSystem,
    CompileSettlementDefsSystem,
    CompileSkillDefsSystem,
    CompileTraitDefsSystem,
    DataCollectionSystems,
    EarlyUpdateSystems,
    InitializationSystems,
    InitializeSettlementSystem,
    JobRoleMonthlyEffectsSystem,
    LateUpdateSystems,
    LifeStageSystem,
    PassiveReputationChange,
    PassiveRomanceChange,
    SpawnNewBusinessesSystem,
    SpawnNewResidentSystem,
    SpawnResidentialBuildingsSystem,
    UpdateFrequentedLocationSystem,
    UpdateSystems,
)
from neighborly.tracery import Tracery


class Simulation:
    """A Neighborly simulation instance."""

    __slots__ = "_config", "_world"

    _config: SimulationConfig
    """Config parameters for the simulation."""
    _world: World
    """The simulation's ECS instance."""

    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        """
        Parameters
        ----------
        config
            Configuration parameters for the simulation, by default None.
            Simulation will use a default configuration if no config is
            provided.
        """
        self._config = config if config is not None else SimulationConfig()
        self._world = World()

        # Seed the global rng for third-party packages
        random.seed(self._config.seed)

        self._init_resources()
        self._init_systems()
        self._init_logging()
        self._init_component_factories()

    def _init_resources(self) -> None:
        """Initialize built-in resources."""
        self.world.resource_manager.add_resource(self._config)
        self.world.resource_manager.add_resource(random.Random(self._config.seed))
        self.world.resource_manager.add_resource(SimDate())
        self.world.resource_manager.add_resource(CharacterLibrary(DefaultCharacterDef))
        self.world.resource_manager.add_resource(JobRoleLibrary(DefaultJobRoleDef))
        self.world.resource_manager.add_resource(BusinessLibrary(DefaultBusinessDef))
        self.world.resource_manager.add_resource(ResidenceLibrary(DefaultResidenceDef))
        self.world.resource_manager.add_resource(DistrictLibrary(DefaultDistrictDef))
        self.world.resource_manager.add_resource(
            SettlementLibrary(DefaultSettlementDef)
        )
        self.world.resource_manager.add_resource(TraitLibrary(DefaultTraitDef))
        self.world.resource_manager.get_resource(TraitLibrary).add_definition_type(
            DefaultSpeciesDef
        )
        self.world.resource_manager.add_resource(SkillLibrary(DefaultSkillDef))
        self.world.resource_manager.add_resource(SocialRuleLibrary())
        self.world.resource_manager.add_resource(LocationPreferenceLibrary())
        self.world.resource_manager.add_resource(SettlementNameFactories())
        self.world.resources.get_resource(SettlementNameFactories).add_factory(
            "default", default_settlement_name_factory
        )
        self.world.resource_manager.add_resource(DistrictNameFactories())
        self.world.resources.get_resource(DistrictNameFactories).add_factory(
            "default", default_district_name_factory
        )
        self.world.resource_manager.add_resource(CharacterNameFactories())
        self.world.resources.get_resource(CharacterNameFactories).add_factory(
            "default-first", generate_any_first_name
        )
        self.world.resources.get_resource(CharacterNameFactories).add_factory(
            "masculine-first", generate_masculine_first_name
        )
        self.world.resources.get_resource(CharacterNameFactories).add_factory(
            "feminine-first", generate_feminine_first_name
        )
        self.world.resources.get_resource(CharacterNameFactories).add_factory(
            "default-last", generate_last_name
        )
        self.world.resource_manager.add_resource(BusinessNameFactories())
        self.world.resource_manager.add_resource(Tracery(self._config.seed))
        self.world.resource_manager.add_resource(GlobalEventHistory())
        self.world.resource_manager.add_resource(ActionConsiderationLibrary())

    def _init_systems(self) -> None:
        """Initialize built-in systems."""
        # Add default top-level system groups (in execution order)
        self.world.system_manager.add_system(InitializationSystems())
        self.world.system_manager.add_system(DataCollectionSystems())
        self.world.system_manager.add_system(EarlyUpdateSystems())
        self.world.system_manager.add_system(UpdateSystems())
        self.world.system_manager.add_system(LateUpdateSystems())

        # Add content initialization systems
        self.world.system_manager.add_system(
            system=CompileTraitDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileJobRoleDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileSkillDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileDistrictDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileSettlementDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileResidenceDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileCharacterDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=CompileBusinessDefsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=InitializeSettlementSystem(), system_group=InitializationSystems
        )

        # Add core update systems
        self.world.system_manager.add_system(
            system=SpawnNewResidentSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=SpawnResidentialBuildingsSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=SpawnNewBusinessesSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=UpdateFrequentedLocationSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=AgingSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=LifeStageSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=ChildBirthSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=PassiveReputationChange(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=PassiveRomanceChange(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=JobRoleMonthlyEffectsSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=CharacterLifespanSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=BusinessLifespanSystem(), system_group=UpdateSystems
        )

    def _init_component_factories(self) -> None:
        """Initialize built-in component factories."""
        self.world.gameobjects.add_component_factory(CharacterFactory())
        self.world.gameobjects.add_component_factory(BusinessFactory())
        self.world.gameobjects.add_component_factory(LocationFactory())
        self.world.gameobjects.add_component_factory(LocationPreferencesFactory())
        self.world.gameobjects.add_component_factory(FrequentedLocationsFactory())
        self.world.gameobjects.add_component_factory(SettlementFactory())
        self.world.gameobjects.add_component_factory(DistrictFactory())
        self.world.gameobjects.add_component_factory(AgeFactory())
        self.world.gameobjects.add_component_factory(AgentFactory())
        self.world.gameobjects.add_component_factory(SkillsFactory())
        self.world.gameobjects.add_component_factory(TraitsFactory())
        self.world.gameobjects.add_component_factory(StatsFactory())
        self.world.gameobjects.add_component_factory(CharacterSpawnTableFactory())
        self.world.gameobjects.add_component_factory(BusinessSpawnTableFactory())
        self.world.gameobjects.add_component_factory(ResidenceSpawnTableFactory())

    def _init_logging(self) -> None:
        """Initialize simulation logging."""
        if self.config.logging.logging_enabled:
            if self.config.logging.log_to_terminal is False:
                # Output the logs to a file
                log_path = pathlib.Path(self.config.logging.log_file_path)

                logging.basicConfig(
                    filename=log_path,
                    encoding="utf-8",
                    level=self.config.logging.log_level,
                    format="%(message)s",
                    force=True,
                )
            else:
                logging.basicConfig(
                    level=self.config.logging.log_level,
                    format="%(message)s",
                    force=True,
                )

    @property
    def date(self) -> SimDate:
        """The current date in the simulation."""
        return self._world.resource_manager.get_resource(SimDate)

    @property
    def world(self) -> World:
        """The simulation's ECS instance."""
        return self._world

    @property
    def config(self) -> SimulationConfig:
        """Config parameters for the simulation."""
        return self._config

    def initialize(self) -> None:
        """Run initialization systems only."""
        self.world.initialize_sql_database()

        initialization_system_group = self.world.system_manager.get_system(
            InitializationSystems
        )

        initialization_system_group.on_update(self.world)

        initialization_system_group.set_active(False)

    def step(self) -> None:
        """Advance the simulation one time step (month)."""
        self._world.step()
        self.date.increment_month()

    def to_json(self, indent: Optional[int] = None) -> str:
        """Export the simulation as a JSON string.

        Parameters
        ----------
        indent
            An optional amount of spaces to indent lines in the string.

        Returns
        -------
        str
            A JSON data string.
        """
        serialized_data = {
            "seed": self.config.seed,
            "gameobjects": {
                str(g.uid): g.to_dict()
                for g in self.world.gameobject_manager.gameobjects
            },
            "events": self.world.resource_manager.get_resource(
                GlobalEventHistory
            ).to_dict(),
        }

        return json.dumps(
            serialized_data,
            indent=indent,
        )
