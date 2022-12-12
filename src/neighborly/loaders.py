"""
Utility functions to help users load configuration data from files
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Protocol, Sequence, Union

import pydantic
import yaml

from neighborly.engine import (
    BusinessArchetypeConfig,
    BusinessSpawnConfig,
    CharacterArchetypeConfig,
    CharacterSpawnConfig,
    ResidenceArchetypeConfig,
    ResidenceSpawnConfig,
)
from neighborly.simulation import Simulation

logger = logging.getLogger(__name__)


class IDataLoader(Protocol):
    """Interface for a function that loads a specific subsection of the YAML data file"""

    def __call__(self, sim: Simulation, data: Dict[str, Any]) -> None:
        raise NotImplementedError()


class NeighborlyYamlImporter:
    """Load Neighborly Component and Archetype definitions from an YAML"""

    __slots__ = "data"

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data: Dict[str, Any] = data

    @classmethod
    def from_path(cls, filepath: Union[str, Path]) -> NeighborlyYamlImporter:
        """Create a new importer instance using a file path"""
        with open(filepath, "r") as f:
            data: Dict[str, Any] = yaml.safe_load(f)
        return cls(data)

    @classmethod
    def from_str(cls, yaml_str: str) -> NeighborlyYamlImporter:
        """Create a new importer instance using a yaml string"""
        data: Dict[str, Any] = yaml.safe_load(yaml_str)
        return cls(data)

    def load(self, sim: Simulation, loaders: Sequence[IDataLoader]) -> None:
        """
        Load each section of that YAML datafile

        Parameters
        ----------
        sim: Simulation
            The simulation instance to load data into
        loaders: Sequence[IDataLoader]
            A function that loads information from the
            yaml data
        """
        for loader in loaders:
            loader(sim, self.data)


class YamlCharacterArchetypeConfig(pydantic.BaseModel):
    """
    Configuration information for character archetypes

    Attributes
    ------
    name: str
        The name of this particular configuration
    spawn_config: CharacterSpawnConfig
        Configuration data regarding how this archetype should be spawned
    base: str
        The name of the archetype to base this character
        archetype configuration on
    options: Dict[str, Any]
        Parameters to pass to the archetype's create function
        when spawning an instance of this archetype
    """

    name: str
    base: str
    spawn_config: CharacterSpawnConfig = pydantic.Field(
        default_factory=CharacterSpawnConfig
    )
    options: Dict[str, Any] = pydantic.Field(default_factory=dict)


class YamlBusinessArchetypeConfig(pydantic.BaseModel):
    """
    Configuration information for business archetypes

    Attributes
    ------
    name: str
        The name of this particular configuration
    spawn_config: BusinessSpawnConfig
        Configuration data regarding how this archetype should be spawned
    base: str
        The name of the archetype to base this business
        archetype configuration on
    options: Dict[str, Any]
        Parameters to pass to the archetype's create function
        when spawning an instance of this archetype
    """

    name: str
    base: str
    spawn_config: BusinessSpawnConfig = pydantic.Field(
        default_factory=BusinessSpawnConfig
    )
    options: Dict[str, Any] = pydantic.Field(default_factory=dict)


class YamlResidenceArchetypeConfig(pydantic.BaseModel):
    """
    Configuration information for business archetypes

    Attributes
    ------
    name: str
        The name of this particular configuration
    spawn_config: BusinessSpawnConfig
        Configuration data regarding how this archetype should be spawned
    base: str
        The name of the archetype to base this business
        archetype configuration on
    options: Dict[str, Any]
        Parameters to pass to the archetype's create function
        when spawning an instance of this archetype
    """

    name: str
    base: str
    spawn_config: BusinessSpawnConfig = pydantic.Field(
        default_factory=BusinessSpawnConfig
    )
    options: Dict[str, Any] = pydantic.Field(default_factory=dict)


def load_character_archetypes(sim: Simulation, data: Dict[str, Any]) -> None:
    """Process data defining character archetypes"""
    character_data: List[Dict[str, Any]] = data["Characters"]
    for archetype_data in character_data:
        yaml_archetype_config = YamlCharacterArchetypeConfig.parse_obj(archetype_data)

        base = sim.engine.character_archetypes.get(yaml_archetype_config.base)

        new_archetype = CharacterArchetypeConfig(
            name=yaml_archetype_config.name,
            factory=base.factory,
            spawn_config=CharacterSpawnConfig(
                **{
                    **base.spawn_config.dict(),
                    **yaml_archetype_config.spawn_config.dict(),
                }
            ),
            options={**base.options, **yaml_archetype_config.options},
        )

        sim.engine.character_archetypes.add(new_archetype)


def load_business_archetypes(sim: Simulation, data: Dict[str, Any]) -> None:
    """Process data defining business archetypes"""
    business_data: List[Dict[str, Any]] = data["Businesses"]
    for archetype_data in business_data:
        yaml_archetype_config = YamlBusinessArchetypeConfig.parse_obj(archetype_data)

        base = sim.engine.business_archetypes.get(yaml_archetype_config.base)

        new_archetype = BusinessArchetypeConfig(
            name=yaml_archetype_config.name,
            factory=base.factory,
            spawn_config=BusinessSpawnConfig(
                **{
                    **base.spawn_config.dict(),
                    **yaml_archetype_config.spawn_config.dict(),
                }
            ),
            options={**base.options, **yaml_archetype_config.options},
        )

        sim.engine.business_archetypes.add(new_archetype)


def load_residence_data(sim: Simulation, data: Dict[str, Any]) -> None:
    """Process data defining residence archetypes"""
    residence_data: List[Dict[str, Any]] = data["Residences"]
    for archetype_data in residence_data:
        yaml_archetype_config = YamlResidenceArchetypeConfig.parse_obj(archetype_data)

        base = sim.engine.residence_archetypes.get(yaml_archetype_config.base)

        new_archetype = ResidenceArchetypeConfig(
            name=yaml_archetype_config.name,
            factory=base.factory,
            spawn_config=ResidenceSpawnConfig(
                **{
                    **base.spawn_config.dict(),
                    **yaml_archetype_config.spawn_config.dict(),
                }
            ),
            options={**base.options, **yaml_archetype_config.options},
        )

        sim.engine.residence_archetypes.add(new_archetype)
