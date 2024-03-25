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
)
from neighborly.ecs import World
from neighborly.effects.effects import (
    AddLocationPreference,
    AddSocialRule,
    IncreaseSkill,
    StatBuff,
)
from neighborly.helpers.traits import register_trait_def
from neighborly.libraries import (
    BusinessLibrary,
    CharacterLibrary,
    DistrictLibrary,
    EffectLibrary,
    JobRoleLibrary,
    LifeEventLibrary,
    PreconditionLibrary,
    ResidenceLibrary,
    SettlementLibrary,
    SkillLibrary,
    TraitLibrary,
)
from neighborly.life_event import EventConsiderations, GlobalEventHistory
from neighborly.preconditions.defaults import (
    AtLeastLifeStage,
    HasTrait,
    SkillRequirement,
    TargetHasTrait,
    TargetIsSex,
    TargetLifeStageLT,
)
from neighborly.systems import (
    AgingSystem,
    ChildBirthSystem,
    CompileBusinessDefsSystem,
    CompileCharacterDefsSystem,
    CompileDistrictDefsSystem,
    CompileResidenceDefsSystem,
    CompileSettlementDefsSystem,
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
    LifeEventSystem,
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
        self._init_preconditions()
        self._init_traits()
        self._init_logging()

    def _init_resources(self) -> None:
        """Initialize built-in resources."""
        self.world.resource_manager.add_resource(self._config)
        self.world.resource_manager.add_resource(random.Random(self._config.seed))
        self.world.resource_manager.add_resource(SimDate())
        self.world.resource_manager.add_resource(DataTables())
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
        self.world.resource_manager.add_resource(EffectLibrary())
        self.world.resource_manager.add_resource(SkillLibrary(DefaultSkillDef))
        self.world.resource_manager.add_resource(PreconditionLibrary())
        self.world.resource_manager.add_resource(LifeEventLibrary())
        self.world.resource_manager.add_resource(Tracery(self._config.seed))
        self.world.resource_manager.add_resource(GlobalEventHistory())
        self.world.resource_manager.add_resource(EventConsiderations())

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
            system=InstantiateTraitsSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=InstantiateJobRolesSystem(), system_group=InitializationSystems
        )
        self.world.system_manager.add_system(
            system=InstantiateSkillsSystem(), system_group=InitializationSystems
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
            system=HealthDecaySystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=ChildBirthSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=MeetNewPeopleSystem(), system_group=UpdateSystems
        )
        self.world.system_manager.add_system(
            system=LifeEventSystem(), system_group=UpdateSystems
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
            system=DeathSystem(), system_group=UpdateSystems
        )

    def _init_effects(self) -> None:
        """Initialize built-in Effect definitions."""
        self._world.resource_manager.get_resource(EffectLibrary).add_effect_type(
            StatBuff
        )
        self._world.resource_manager.get_resource(EffectLibrary).add_effect_type(
            IncreaseSkill
        )
        self._world.resource_manager.get_resource(EffectLibrary).add_effect_type(
            AddLocationPreference
        )
        self._world.resource_manager.get_resource(EffectLibrary).add_effect_type(
            AddSocialRule
        )

    def _init_preconditions(self) -> None:
        """Initialize built-in precondition definitions."""
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(HasTrait)
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(SkillRequirement)
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(AtLeastLifeStage)
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(TargetHasTrait)
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(TargetIsSex)
        self.world.resource_manager.get_resource(
            PreconditionLibrary
        ).add_precondition_type(TargetLifeStageLT)

    def _init_traits(self) -> None:
        """Initialize built-in trait definitions"""
        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="employee",
                display_name="Employee",
                description="The target of this relationship is an employee.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="coworker",
                display_name="Coworker",
                description="The target of this relationship is a coworker.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="departed",
                display_name="Departed",
                description="The character has departed the simulation.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="deceased",
                display_name="Deceased",
                description="The character has died.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="retired",
                display_name="Retired",
                description="The character has retired from working.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="family",
                display_name="Family",
                description="These characters are related",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="parent",
                display_name="Parent",
                description="The target of this relationship is the owner's parent",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="child",
                display_name="Child",
                description="The target of this relationship is the owner's child",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="sibling",
                display_name="Sibling",
                description="The target of this relationship is the owner's sibling",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="spouse",
                display_name="Spouse",
                description="The target of this relationship is the owner's spouse",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="dating",
                display_name="dating",
                description="The relationship target and owner are dating.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="crush",
                display_name="Crush",
                description="The owner of this relationship has a crush on the target.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="live_together",
                display_name="Live Together",
                description="The owner of this relationship lives with the target.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="friend",
                display_name="Friend",
                description="The owner of this relationship is friends with target.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="enemy",
                display_name="Enemy",
                description="The owner of this relationship is enemies with target.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="widow",
                display_name="Widow",
                description="The target of the relationship is the widow of the owner.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="step_parent",
                display_name="Step Parent",
                description="Target is the step parent of the owner.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="step_child",
                display_name="Step Child",
                description="Target is the step child of the owner.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="step_sibling",
                display_name="Step Sibling",
                description="Target is the step sibling of the owner.",
                spawn_frequency=0,
            ),
        )

        register_trait_def(
            self.world,
            DefaultTraitDef(
                definition_id="biological_parent",
                display_name="Biological Parent",
                description="Target is the biological parent of the owner.",
                spawn_frequency=0,
            ),
        )

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
            "data_tables": self.world.resource_manager.get_resource(
                DataTables
            ).to_dict(),
        }

        return json.dumps(
            serialized_data,
            indent=indent,
        )
