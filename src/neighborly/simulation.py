"""The main simulation class.

This module contains class definitions for creating simulation instances.

"""

from __future__ import annotations

import json
import logging
import pathlib
import random
from typing import Optional

import tqdm

from neighborly.config import SimulationConfig
from neighborly.datetime import MONTHS_PER_YEAR, SimDate
from neighborly.ecs import World
from neighborly.effects.effects import (
    AddLocationPreference,
    AddRelationshipModifier,
    AddSkillModifier,
    AddStatModifier,
    AddStatModifierToOwner,
    AddStatModifierToTarget,
    AddToBaseSkill,
    AddToBaseStat,
)
from neighborly.factories.business import BusinessFactory, DefaultBusinessFactory
from neighborly.factories.character import (
    CharacterFactory,
    DefaultCharacterFactory,
    DefaultChildFactory,
    SpeciesFactory,
)
from neighborly.factories.location import (
    FrequentedLocationsFactory,
    LocationFactory,
    LocationPreferencesFactory,
)
from neighborly.factories.relationships import (
    RelationshipModifiersFactory,
    RelationshipsFactory,
)
from neighborly.factories.settlement import (
    DefaultDistrictFactory,
    DefaultSettlementFactory,
    DistrictFactory,
    SettlementFactory,
)
from neighborly.factories.shared import (
    AgeFactory,
    ModifiersFactory,
    PersonalEventHistoryFactory,
)
from neighborly.factories.skills import SkillsFactory
from neighborly.factories.spawn_table import (
    BusinessSpawnTableFactory,
    CharacterSpawnTableFactory,
    DistrictSpawnTableFactory,
)
from neighborly.factories.stats import (
    DisciplineFactory,
    FertilityFactory,
    LifespanFactory,
    SociabilityFactory,
    StatsFactory,
    StewardshipFactory,
)
from neighborly.factories.traits import TraitsFactory
from neighborly.libraries import (
    ActionConsiderationLibrary,
    BusinessLibrary,
    BusinessNameFactories,
    CharacterLibrary,
    CharacterNameFactories,
    DistrictLibrary,
    DistrictNameFactories,
    EffectLibrary,
    JobRoleLibrary,
    PreconditionLibrary,
    SettlementLibrary,
    SettlementNameFactories,
    SkillLibrary,
    SpeciesLibrary,
    TraitLibrary,
)
from neighborly.life_event import GlobalEventHistory
from neighborly.preconditions.defaults import (
    AreOppositeSex,
    AreSameSex,
    HasTrait,
    IsSex,
    LifeStageRequirement,
    OwnerHasTrait,
    OwnerIsSex,
    OwnerLifeStageRequirement,
    OwnerSkillRequirement,
    OwnerStatRequirement,
    SkillRequirement,
    StatRequirement,
    TargetHasTrait,
    TargetIsSex,
    TargetLifeStageRequirement,
    TargetSkillRequirement,
    TargetStatRequirement,
)
from neighborly.systems import (
    AgingSystem,
    BusinessLifespanSystem,
    CharacterLifespanSystem,
    ChildBirthSystem,
    CompileBusinessDefsSystem,
    CompileCharacterDefsSystem,
    CompileDistrictDefsSystem,
    CompileJobRoleDefsSystem,
    CompileSettlementDefsSystem,
    CompileSkillDefsSystem,
    CompileSpeciesDefsSystem,
    CompileTraitDefsSystem,
    HouseholdSystem,
    InitializeSettlementSystem,
    LifeStageSystem,
    SpawnNewResidentSystem,
    TickModifiersSystem,
    TickTraitsSystem,
    TimeSystem,
    UpdateFrequentedLocationSystem,
)


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
        self._init_effect_precondition_factories()

    def _init_resources(self) -> None:
        """Initialize built-in resources."""
        self.world.resource_manager.add_resource(self._config)
        self.world.resource_manager.add_resource(random.Random(self._config.seed))
        self.world.resource_manager.add_resource(SimDate())
        self.world.resource_manager.add_resource(
            CharacterLibrary(
                factory=DefaultCharacterFactory(), child_factory=DefaultChildFactory()
            )
        )
        self.world.resource_manager.add_resource(JobRoleLibrary())
        self.world.resource_manager.add_resource(
            BusinessLibrary(factory=DefaultBusinessFactory())
        )
        self.world.resource_manager.add_resource(
            DistrictLibrary(factory=DefaultDistrictFactory())
        )
        self.world.resource_manager.add_resource(
            SettlementLibrary(factory=DefaultSettlementFactory())
        )
        self.world.resource_manager.add_resource(TraitLibrary())
        self.world.resource_manager.add_resource(SpeciesLibrary())
        self.world.resource_manager.add_resource(SkillLibrary())
        self.world.resource_manager.add_resource(SettlementNameFactories())
        self.world.resource_manager.add_resource(EffectLibrary())
        self.world.resource_manager.add_resource(PreconditionLibrary())
        self.world.resource_manager.add_resource(DistrictNameFactories())
        self.world.resource_manager.add_resource(CharacterNameFactories())
        self.world.resource_manager.add_resource(BusinessNameFactories())
        self.world.resource_manager.add_resource(GlobalEventHistory())
        self.world.resource_manager.add_resource(ActionConsiderationLibrary())

    def _init_systems(self) -> None:
        """Initialize built-in systems."""
        # Add content initialization systems
        self.world.system_manager.add_system(CompileTraitDefsSystem())
        self.world.system_manager.add_system(CompileSpeciesDefsSystem())
        self.world.system_manager.add_system(CompileJobRoleDefsSystem())
        self.world.system_manager.add_system(CompileSkillDefsSystem())
        self.world.system_manager.add_system(CompileDistrictDefsSystem())
        self.world.system_manager.add_system(CompileSettlementDefsSystem())
        self.world.system_manager.add_system(CompileCharacterDefsSystem())
        self.world.system_manager.add_system(CompileBusinessDefsSystem())
        self.world.system_manager.add_system(InitializeSettlementSystem())

        # Add core update systems
        self.world.system_manager.add_system(TickModifiersSystem())
        self.world.system_manager.add_system(TickTraitsSystem())
        self.world.system_manager.add_system(SpawnNewResidentSystem())
        self.world.system_manager.add_system(UpdateFrequentedLocationSystem())
        self.world.system_manager.add_system(AgingSystem())
        self.world.system_manager.add_system(LifeStageSystem())
        self.world.system_manager.add_system(ChildBirthSystem())
        self.world.system_manager.add_system(CharacterLifespanSystem())
        self.world.system_manager.add_system(BusinessLifespanSystem())
        self.world.system_manager.add_system(HouseholdSystem())

        # Late Update Systems
        self.world.system_manager.add_system(TimeSystem())

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
        self.world.gameobjects.add_component_factory(SkillsFactory())
        self.world.gameobjects.add_component_factory(TraitsFactory())
        self.world.gameobjects.add_component_factory(StatsFactory())
        self.world.gameobjects.add_component_factory(CharacterSpawnTableFactory())
        self.world.gameobjects.add_component_factory(BusinessSpawnTableFactory())
        self.world.gameobjects.add_component_factory(DistrictSpawnTableFactory())
        self.world.gameobjects.add_component_factory(RelationshipsFactory())
        self.world.gameobjects.add_component_factory(PersonalEventHistoryFactory())
        self.world.gameobjects.add_component_factory(LifespanFactory())
        self.world.gameobjects.add_component_factory(FertilityFactory())
        self.world.gameobjects.add_component_factory(StewardshipFactory())
        self.world.gameobjects.add_component_factory(SociabilityFactory())
        self.world.gameobjects.add_component_factory(DisciplineFactory())
        self.world.gameobjects.add_component_factory(SpeciesFactory())
        self.world.gameobjects.add_component_factory(ModifiersFactory())
        self.world.gameobjects.add_component_factory(RelationshipModifiersFactory())

    def _init_effect_precondition_factories(self) -> None:
        """Add effect factories to the library."""

        effect_library = self.world.resources.get_resource(EffectLibrary)

        effect_library.add_effect_type(AddStatModifier)
        effect_library.add_effect_type(AddSkillModifier)
        effect_library.add_effect_type(AddToBaseStat)
        effect_library.add_effect_type(AddToBaseSkill)
        effect_library.add_effect_type(AddLocationPreference)
        effect_library.add_effect_type(AddStatModifierToOwner)
        effect_library.add_effect_type(AddStatModifierToTarget)
        effect_library.add_effect_type(AddRelationshipModifier)

        precondition_library = self.world.resources.get_resource(PreconditionLibrary)

        precondition_library.add_precondition_type(HasTrait)
        precondition_library.add_precondition_type(OwnerHasTrait)
        precondition_library.add_precondition_type(TargetHasTrait)
        precondition_library.add_precondition_type(AreSameSex)
        precondition_library.add_precondition_type(AreOppositeSex)
        precondition_library.add_precondition_type(SkillRequirement)
        precondition_library.add_precondition_type(OwnerSkillRequirement)
        precondition_library.add_precondition_type(TargetSkillRequirement)
        precondition_library.add_precondition_type(StatRequirement)
        precondition_library.add_precondition_type(OwnerStatRequirement)
        precondition_library.add_precondition_type(TargetStatRequirement)
        precondition_library.add_precondition_type(LifeStageRequirement)
        precondition_library.add_precondition_type(OwnerLifeStageRequirement)
        precondition_library.add_precondition_type(TargetLifeStageRequirement)
        precondition_library.add_precondition_type(IsSex)
        precondition_library.add_precondition_type(OwnerIsSex)
        precondition_library.add_precondition_type(TargetIsSex)

    def _init_logging(self) -> None:
        """Initialize simulation logging."""
        if self.config.logging_enabled:
            if self.config.log_to_terminal is False:
                # Output the logs to a file
                log_path = pathlib.Path(self.config.log_file_path)

                logging.basicConfig(
                    filename=log_path,
                    encoding="utf-8",
                    level=self.config.log_level,
                    format="%(message)s",
                    force=True,
                    filemode="w",
                )
            else:
                logging.basicConfig(
                    level=self.config.log_level,
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
        self._world.initialize()

    def step(self) -> None:
        """Advance the simulation one time step (month)."""
        self._world.step()

    def run_for(self, years: int) -> None:
        """Run the simulation for a given number of years."""

        total_time_steps: int = years * MONTHS_PER_YEAR

        if self.config.log_to_terminal:

            for _ in range(total_time_steps):
                self._world.step()
        else:
            for _ in tqdm.trange(total_time_steps):
                self._world.step()

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
