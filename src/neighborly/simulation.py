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
from neighborly.data_collection import DataCollectionSystems, DataTables
from neighborly.datetime import SimDate
from neighborly.defs.business import DefaultBusinessDef, DefaultJobRoleDef
from neighborly.defs.character import DefaultCharacterDef
from neighborly.defs.district import DefaultDistrictDef
from neighborly.defs.residence import DefaultResidenceDef
from neighborly.defs.settlement import DefaultSettlementDef
from neighborly.defs.skill import DefaultSkillDef
from neighborly.defs.trait import DefaultTraitDef
from neighborly.ecs import World
from neighborly.effects.effects import (
    AddRelationshipStatBuff,
    AddRelationshipTrait,
    AddSkillBuff,
    AddStatBuff,
    AddTrait,
    RemoveRelationshipTrait,
    RemoveTrait,
)
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
    JobRoleLibrary,
    LifeEventConsiderationLibrary,
    LifeEventLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.life_event import GlobalEventHistory
from neighborly.systems import (
    AgingSystem,
    ChildBirthSystem,
    DeathSystem,
    EarlyUpdateSystems,
    HealthDecaySystem,
    InitializationSystems,
    InitializeSettlementSystem,
    InstantiateJobRolesSystem,
    InstantiateSkillsSystem,
    InstantiateTraitsSystem,
    JobRoleMonthlyEffectsSystem,
    LateUpdateSystems,
    MeetNewPeopleSystem,
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
        self._init_effects()
        self._init_logging()

    def _init_resources(self) -> None:
        """Initialize built-in resources."""
        self.world.resources.add_resource(self._config)
        self.world.resources.add_resource(random.Random(self._config.seed))
        self.world.resources.add_resource(SimDate())
        self.world.resources.add_resource(DataTables())
        self.world.resources.add_resource(CharacterLibrary(DefaultCharacterDef))
        self.world.resources.add_resource(JobRoleLibrary(DefaultJobRoleDef))
        self.world.resources.add_resource(BusinessLibrary(DefaultBusinessDef))
        self.world.resources.add_resource(ResidenceLibrary(DefaultResidenceDef))
        self.world.resources.add_resource(DistrictLibrary(DefaultDistrictDef))
        self.world.resources.add_resource(SettlementLibrary(DefaultSettlementDef))
        self.world.resources.add_resource(TraitLibrary(DefaultTraitDef))
        self.world.resources.add_resource(EffectLibrary())
        self.world.resources.add_resource(SkillLibrary(DefaultSkillDef))
        self.world.resources.add_resource(LifeEventLibrary())
        self.world.resources.add_resource(Tracery(self._config.seed))
        self.world.resources.add_resource(GlobalEventHistory())
        self.world.resources.add_resource(LifeEventConsiderationLibrary())

    def _init_systems(self) -> None:
        """Initialize built-in systems."""
        # Add default top-level system groups (in execution order)
        self.world.systems.add_system(InitializationSystems())
        self.world.systems.add_system(DataCollectionSystems())
        self.world.systems.add_system(EarlyUpdateSystems())
        self.world.systems.add_system(UpdateSystems())
        self.world.systems.add_system(LateUpdateSystems())

        # Add content initialization systems
        self.world.systems.add_system(
            system=InstantiateTraitsSystem(), system_group=InitializationSystems
        )
        self.world.systems.add_system(
            system=InstantiateJobRolesSystem(), system_group=InitializationSystems
        )
        self.world.systems.add_system(
            system=InstantiateSkillsSystem(), system_group=InitializationSystems
        )
        self.world.systems.add_system(
            system=InitializeSettlementSystem(), system_group=InitializationSystems
        )

        # Add core update systems
        self.world.systems.add_system(
            system=SpawnNewResidentSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=SpawnResidentialBuildingsSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=SpawnNewBusinessesSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=UpdateFrequentedLocationSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(system=AgingSystem(), system_group=UpdateSystems)
        self.world.systems.add_system(
            system=HealthDecaySystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=ChildBirthSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=MeetNewPeopleSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=PassiveReputationChange(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=PassiveRomanceChange(), system_group=UpdateSystems
        )
        self.world.systems.add_system(
            system=JobRoleMonthlyEffectsSystem(), system_group=UpdateSystems
        )
        self.world.systems.add_system(system=DeathSystem(), system_group=UpdateSystems)

    def _init_effects(self) -> None:
        """Initialize built-in Effect definitions."""
        effect_library = self._world.resources.get_resource(EffectLibrary)

        effect_library.add_event(AddTrait)
        effect_library.add_event(RemoveTrait)
        effect_library.add_event(AddRelationshipTrait)
        effect_library.add_event(RemoveRelationshipTrait)
        effect_library.add_event(AddSkillBuff)
        effect_library.add_event(AddStatBuff)
        effect_library.add_event(AddRelationshipStatBuff)

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
        return self._world.resources.get_resource(SimDate)

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
        initialization_system_group = self.world.systems.get_system(
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
                str(g.uid): g.to_dict() for g in self.world.gameobjects.gameobjects
            },
            "events": self.world.resources.get_resource(GlobalEventHistory).to_dict(),
            "data_tables": self.world.resources.get_resource(DataTables).to_dict(),
        }

        return json.dumps(
            serialized_data,
            indent=indent,
        )
