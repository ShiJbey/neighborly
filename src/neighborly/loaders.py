"""Utility functions to help users load configuration data from files
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Protocol, Tuple

import yaml

from neighborly.core.activity import Activity, register_activity
from neighborly.core.business import BusinessConfig
from neighborly.core.engine import NeighborlyEngine, EntityArchetypeSpec, ComponentSpec

AnyPath = Union[str, Path]


def load_activity_definitions(
        yaml_str: Optional[str] = None, filepath: Optional[AnyPath] = None
) -> None:
    """Loads new activity types from given YAML data"""
    if yaml_str and filepath:
        raise ValueError("Only supply YAML string or file path not both")

    if yaml_str:
        yaml_data: Dict[str, Dict[str, Any]] = yaml.safe_load(yaml_str)
    elif filepath:
        with open(filepath, "r") as f:
            yaml_data: Dict[str, Dict[str, Any]] = yaml.safe_load(f)
    else:
        raise ValueError("No YAML string or file path given")

    for name, data in yaml_data.items():
        register_activity(Activity(name, tuple(data["traits"])))


def load_structure_definitions(
        yaml_str: Optional[str] = None, filepath: Optional[AnyPath] = None
) -> None:
    if yaml_str and filepath:
        raise ValueError("Only supply YAML string or file path not both")

    if yaml_str:
        structures_raw: Dict[str, Dict[str, Any]] = yaml.safe_load(yaml_str)
    elif filepath:
        with open(filepath, "r") as f:
            structures_raw: Dict[str, Dict[str, Any]] = yaml.safe_load(f)
    else:
        raise ValueError("No YAML string or file path given")

    # HElPER FUNCTIONS
    def _get_business_config(
            data: Dict[str, Any], **kwargs
    ) -> Optional[BusinessConfig]:
        config: Optional[Dict[str, Any]] = data.get("business")

        if config is None:
            return

        return BusinessConfig(**kwargs, **config)

    # END HELPER FUNCTIONS

    for name, data in structures_raw.items():
        register_structure_def(name, data)


def load_names(
        namespace: str,
        names: Optional[List[str]] = None,
        filepath: Optional[AnyPath] = None,
) -> None:
    """Load names a list of names from a text file or given list"""
    from neighborly.core.name_generation import register_rule
    if names:
        register_rule(namespace, names)
    elif filepath:
        with open(filepath, "r") as f:
            register_rule(namespace, f.read().splitlines())
    else:
        raise ValueError("Need to supply names list or path to file containing names")


class SpecificationNode:
    """Holds information about how to create a type of object"""

    __slots__ = "_extends", "_children", "_attributes", "_type"

    def __init__(self, type_name: str, **kwargs):
        self._type: str = type_name


class IDataLoader(Protocol):

    def load(self, engine: NeighborlyEngine) -> None:
        """Load the definitions"""
        raise NotImplementedError()


class XmlDataLoader:
    """Load Neighborly Component and Archetype definitions from an XMl

    Not fully supported. For now, please use the YAML loader
    """

    __slots__ = "_raw_data"

    def __init__(
            self,
            str_data: Optional[str] = None,
            filepath: Optional[AnyPath] = None
    ) -> None:
        raise NotImplementedError()
        # if str_data:
        #     self._raw_data: ET.ElementTree = ET.parse(str_data)
        # elif filepath:
        #     self._raw_data: ET.ElementTree = ET.parse(filepath)
        # else:
        #     raise ValueError("No data string or file path given")

    def load(self, engine: NeighborlyEngine) -> None:
        """Load the definitions"""
        root = self._raw_data.getroot()
        # Now we change into an intermediate representation
        # Each archetype needs to be saved as dict of trees
        # where each specification node

        for child in root:
            # For each subsection process the data
            if child.tag == "Characters":
                print(f"Importing ({len(child)}) character archetypes from XML")
            if child.tag == "Activities":
                print(f"Importing ({len(child)}) activities from XML")
                self._load_activity_data(child)

    @staticmethod
    def _load_activity_data(activities: ET.Element) -> None:
        """Process data related to defining activities"""
        for child in activities:
            # Add a specification node
            traits_list: Tuple[str] = tuple(map(lambda trait: str(trait).strip(), child.attrib["traits"].split(',')))
            register_activity(Activity(child.attrib["name"], trait_names=traits_list))


class YamlDataLoader:
    """Load Neighborly Component and Archetype definitions from an YAML"""

    __slots__ = "_raw_data"

    def __init__(
            self,
            str_data: Optional[str] = None,
            filepath: Optional[AnyPath] = None
    ) -> None:
        if str_data:
            self._raw_data: Dict[str, Any] = yaml.safe_load(str_data)
        elif filepath:
            with open(filepath, "r") as f:
                self._raw_data: Dict[str, Any] = yaml.safe_load(f)
        else:
            raise ValueError("No data string or file path given")

    def load(self, engine: NeighborlyEngine) -> None:
        """Load the definitions"""

        # Now we change into an intermediate representation
        # Each archetype needs to be saved as dict of trees
        # where each specification node
        for subsection, data in self._raw_data.items():
            if subsection == "Characters":
                print(f"Importing ({len(data)}) character archetypes from YAML")
                self._load_character_data(engine, data)
            if subsection == "Activities":
                print(f"Importing ({len(data)}) activities from XML")
                self._load_activity_data(data)

    @staticmethod
    def _load_activity_data(activities: Dict[str, Dict[str, Any]]) -> None:
        """Process data related to defining activities"""
        for activity_name, attrs in activities.items():
            register_activity(Activity(activity_name, trait_names=attrs["traits"]))

    @staticmethod
    def _load_character_data(engine: NeighborlyEngine, characters: Dict[str, Dict[str, Any]]) -> None:
        """Process data related to defining character archetypes"""
        for archetype_name, data in characters.items():
            archetype = EntityArchetypeSpec(archetype_name)

            if data.get("default"):
                engine.add_character_archetype(archetype, name="default")

            if data.get("extends"):
                parent = engine.get_character_archetype(data["extends"])

                # Add all the parents components to this instance
                for component_name, component_spec in parent.get_components().items():
                    archetype.add_component(component_spec)

            components = {component_name: params for component_name, params in data.items() if type(params) is dict}

            for component_name, params in components.items():
                # Check if there is an existing node
                default_params: Dict[str, Any] = {}

                if component_name in archetype.get_components():
                    default_params.update(archetype.get_components()[component_name].get_attributes())

                component_spec = ComponentSpec(component_name, {**default_params, **params})

                archetype.add_component(component_spec)

            engine.add_character_archetype(archetype)
