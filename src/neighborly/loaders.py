"""
Utility functions to help users load configuration data from files
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Union

import yaml

from neighborly.core.activity import Activity, ActivityLibrary
from neighborly.core.archetypes import (
    BaseBusinessArchetype,
    BaseCharacterArchetype,
    BaseResidenceArchetype,
    BusinessArchetypes,
    CharacterArchetypes,
    ResidenceArchetypes,
)
from neighborly.core.business import ServiceTypes

logger = logging.getLogger(__name__)


class ISectionLoader(Protocol):
    """Interface for a function that loads a specific subsection of the YAML data file"""

    def __call__(self, data: Any) -> None:
        raise NotImplementedError()


class YamlDataLoader:
    """Load Neighborly Component and Archetype definitions from an YAML"""

    _section_loaders: Dict[str, ISectionLoader] = {}

    def load(
        self,
        yaml_str: Optional[str] = None,
        filepath: Optional[Union[str, Path]] = None,
    ) -> None:
        """
        Load each section of that YAML datafile

        Parameters
        ----------
        yaml_str: Optional[str]
            YAML data inside a Python string
        filepath: Optional[Union[str, Path]]
            Path to YAML file with data to load
        """
        if yaml_str:
            raw_data: Dict[str, Any] = yaml.safe_load(yaml_str)
        elif filepath:
            with open(filepath, "r") as f:
                raw_data: Dict[str, Any] = yaml.safe_load(f)
        else:
            raise ValueError("No data string or file path given")

        for section, data in raw_data.items():
            if section in self._section_loaders:
                self._section_loaders[section](data)
            else:
                logger.warning(f"skipping unsupported YAML section '{section}'.")

    @classmethod
    def add_section_loader(cls, section_name: str, loader_fn: ISectionLoader) -> None:
        """Add a function to load a section of YAML"""
        if section_name in cls._section_loaders:
            logger.warning(f"Overwriting existing loader for section: {section_name}")
        cls._section_loaders[section_name] = loader_fn

    @classmethod
    def section_loader(cls, section_name: str):
        """Decorator function for registering functions that load various sections of the YAML data"""

        def decorator(loader_fn: ISectionLoader) -> ISectionLoader:
            cls.add_section_loader(section_name, loader_fn)
            return loader_fn

        return decorator


@YamlDataLoader.section_loader("Characters")
def _load_character_archetypes(data: List[Dict[str, Any]]) -> None:
    """Process data defining entity archetypes"""
    for archetype_data in data:
        CharacterArchetypes.add(
            archetype_data["name"], BaseCharacterArchetype(**archetype_data)
        )


@YamlDataLoader.section_loader("Businesses")
def _load_business_archetypes(data: List[Dict[str, Any]]) -> None:
    """Process data defining business archetypes"""
    for archetype_data in data:
        BusinessArchetypes.add(
            archetype_data["name"], BaseBusinessArchetype(**archetype_data)
        )


@YamlDataLoader.section_loader("Residences")
def _load_residence_data(data: List[Dict[str, Any]]) -> None:
    """Process data defining residence archetypes"""
    for archetype_data in data:
        ResidenceArchetypes.add(
            archetype_data["name"], BaseResidenceArchetype(**archetype_data)
        )


@YamlDataLoader.section_loader("Activities")
def _load_activity_data(data: List[Dict[str, Any]]) -> None:
    """Process data defining activities"""
    for entry in data:
        ActivityLibrary.add(Activity(entry["name"], trait_names=entry["traits"]))


@YamlDataLoader.section_loader("Services")
def _load_business_services(data: List[Dict[str, Any]]) -> None:
    """Load business services from YAML"""
    for entry in data:
        ServiceTypes.add(entry["name"])
