"""Utility functions to help users load configuration data from files
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set

import yaml

from neighborly.ai.behavior_tree import BehaviorTree, AbstractBTNode
from neighborly.ai.character_behavior import get_node_factory_for_type, register_behavior
from neighborly.core.activity import Activity, register_activity
from neighborly.core.engine import NeighborlyEngine, ComponentSpec, EntityArchetypeSpec
from neighborly.core.relationship import load_relationship_tags

AnyPath = Union[str, Path]


def load_names(
        rule_name: str,
        names: Optional[List[str]] = None,
        filepath: Optional[AnyPath] = None,
) -> None:
    """Load names a list of names from a text file or given list"""
    from neighborly.core.name_generation import register_rule
    if names:
        register_rule(rule_name, names)
    elif filepath:
        with open(filepath, "r") as f:
            register_rule(rule_name, f.read().splitlines())
    else:
        raise ValueError(
            "Need to supply names list or path to file containing names")


class YamlDataLoader:
    """Load Neighborly Component and Archetype definitions from an YAML"""

    __slots__ = "_raw_data"

    def __init__(
            self,
            str_data: Optional[str] = None,
            filepath: Optional[AnyPath] = None,
    ) -> None:
        self._raw_data: Dict[str, Any] = {}

        if str_data:
            self._raw_data = yaml.safe_load(str_data)
        elif filepath:
            with open(filepath, "r") as f:
                self._raw_data = yaml.safe_load(f)
        else:
            raise ValueError("No data string or file path given")

    def load(self, engine: NeighborlyEngine) -> None:
        """Load the definitions"""

        # Now we change into an intermediate representation
        # Each archetype needs to be saved as dict of trees
        # where each specification node
        for section, data in self._raw_data.items():
            if section == "Characters":
                self._load_character_data(engine, data)
            elif section == "Activities":
                self._load_activity_data(data)
            elif section == "Places":
                self._load_place_data(engine, data)
            elif section == "Residences":
                self._load_place_data(engine, data)
            elif section == "Businesses":
                self._load_place_data(engine, data)
            elif section == "RelationshipTags":
                self._load_relationship_tag_data(data)
            else:
                print(f"WARNING:: Skipping unsupported section '{section}'")

    @staticmethod
    def _load_activity_data(activities: List[Dict[str, Any]]) -> None:
        """Process data related to defining activities"""
        for data in activities:
            register_activity(
                Activity(data['name'], trait_names=data["traits"]))

    @staticmethod
    def _load_character_data(engine: NeighborlyEngine, characters: List[Dict[str, Any]]) -> None:
        """Process data related to defining character archetypes"""
        for data in characters:
            archetype = EntityArchetypeSpec(
                data['name'],
                attributes={
                    'name': data['name'],
                    'tags': data['tags'] if 'tags' in data else [],
                }
            )

            if data.get("default"):
                engine.add_character_archetype(archetype, name="default")

            if data.get("inherits"):
                parent = engine.get_character_archetype(data["inherits"])

                if parent.get_attributes().get('default') and parent.get_type() == archetype.get_type():
                    engine.add_character_archetype(archetype, name="default")

                # Add all the parents components to this instance
                for component_name, component_spec in parent.get_components().items():
                    archetype.add_component(component_spec)

            if 'components' not in data:
                raise ValueError("Entity spec missing component definitions")

            for component in data['components']:
                # Check if there is an existing node
                default_params: Dict[str, Any] = {}

                component_name = component['type']

                if component_name in archetype.get_components():
                    default_params.update(archetype.get_components()[
                                              component_name].get_attributes())

                params = component['options'] if 'options' in component else {}

                component_spec = ComponentSpec(
                    component_name, {**default_params, **params})

                archetype.add_component(component_spec)

            engine.add_character_archetype(archetype)

    @staticmethod
    def _load_place_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = EntityArchetypeSpec(
                name=data['name'],
                attributes={
                    'name': data['name'],
                    'tags': data['tags'] if 'tags' in data else [],
                }
            )

            if data.get("default"):
                engine.add_place_archetype(archetype, name="default")

            if data.get("inherits"):
                parent = engine.get_place_archetype(data["inherits"])

                # Add all the parents components to this instance
                for component_name, component_spec in parent.get_components().items():
                    archetype.add_component(component_spec)

            if 'components' not in data:
                raise ValueError("Entity spec missing component definitions")

            for component in data['components']:
                # Check if there is an existing node
                default_params: Dict[str, Any] = {}

                component_name = component['type']

                if component_name in archetype.get_components():
                    default_params.update(archetype.get_components()[
                                              component_name].get_attributes())

                params = component['options'] if 'options' in component else {}

                component_spec = ComponentSpec(
                    component_name, {**default_params, **params})

                archetype.add_component(component_spec)

            engine.add_place_archetype(archetype)

    @staticmethod
    def _load_business_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = EntityArchetypeSpec(
                name=data['name'],
                attributes={
                    'name': data['name'],
                    'tags': data['tags'] if 'tags' in data else [],
                }
            )

            if data.get("default"):
                engine.add_business_archetype(archetype, name="default")

            if data.get("inherits"):
                parent = engine.get_business_archetype(data["inherits"])

                # Add all the parents components to this instance
                for component_name, component_spec in parent.get_components().items():
                    archetype.add_component(component_spec)

            if 'components' not in data:
                raise ValueError("Entity spec missing component definitions")

            for component in data['components']:
                # Check if there is an existing node
                default_params: Dict[str, Any] = {}

                component_name = component['type']

                if component_name in archetype.get_components():
                    default_params.update(archetype.get_components()[
                                              component_name].get_attributes())

                params = component['options'] if 'options' in component else {}

                component_spec = ComponentSpec(
                    component_name, {**default_params, **params})

                archetype.add_component(component_spec)

            engine.add_business_archetype(archetype)

    @staticmethod
    def _load_residence_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = EntityArchetypeSpec(
                name=data['name'],
                attributes={
                    'name': data['name'],
                    'tags': data['tags'] if 'tags' in data else [],
                }
            )

            if data.get("default"):
                engine.add_residence_archetype(archetype, name="default")

            if data.get("inherits"):
                parent = engine.get_residence_archetype(data["inherits"])

                # Add all the parents components to this instance
                for component_name, component_spec in parent.get_components().items():
                    archetype.add_component(component_spec)

            if 'components' not in data:
                raise ValueError("Entity spec missing component definitions")

            for component in data['components']:
                # Check if there is an existing node
                default_params: Dict[str, Any] = {}

                component_name = component['type']

                if component_name in archetype.get_components():
                    default_params.update(archetype.get_components()[
                                              component_name].get_attributes())

                params = component['options'] if 'options' in component else {}

                component_spec = ComponentSpec(
                    component_name, {**default_params, **params})

                archetype.add_component(component_spec)

            engine.add_residence_archetype(archetype)

    @staticmethod
    def _load_relationship_tag_data(relationship_tags: List[Dict[str, Any]]) -> None:
        load_relationship_tags(relationship_tags)


class XmlBehaviorLoader:
    __slots__ = "_data_tree"

    def __init__(self, filepath: AnyPath) -> None:
        self._data_tree = ET.parse(filepath)

    def load(self) -> None:
        # Check that the root node has the behavior tag.
        root = self._data_tree.getroot()

        if root.tag != "Behaviors":
            raise ValueError("Root tag of XML must be '<Behaviors>'")

        # Create a new behavior tree for each behavior node
        for child in root:
            register_behavior(self.construct_behavior(child))

    @staticmethod
    def construct_behavior(el: ET.Element) -> BehaviorTree:
        behavior_tree: BehaviorTree = BehaviorTree(el.attrib["type"])

        # Perform DFS, linking child nodes to their parent
        visited: Set[ET.Element] = set()
        stack: List[Tuple[Optional[AbstractBTNode], ET.Element]] = list()

        stack.append((None, el))

        while stack:
            bt_node, xml_node = stack.pop()
            if xml_node not in visited:
                visited.add(xml_node)

                if bt_node:
                    new_node = get_node_factory_for_type(xml_node.tag).create(
                        **xml_node.attrib
                    )
                    bt_node.add_child(new_node)
                else:
                    new_node = behavior_tree

                for child in reversed(xml_node):
                    stack.append((new_node, child))

        return behavior_tree
