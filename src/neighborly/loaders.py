"""Utility functions to help users load configuration data from files
"""
import copy
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple, Set

import yaml

from neighborly.ai.behavior_tree import BehaviorTree, AbstractBTNode
from neighborly.ai.character_behavior import get_node_factory_for_type, register_behavior
from neighborly.core.activity import Activity, register_activity
from neighborly.core.business import BusinessDefinition
from neighborly.core.engine import NeighborlyEngine, ComponentSpec, EntityArchetypeSpec
from neighborly.core.relationship import RelationshipTag

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


class MissingComponentSpecError(Exception):
    """Error raised when an entity archetype is missing an expected component"""

    def __init__(self, component: str) -> None:
        super().__init__(f"Missing spec for component: '{component}'")
        self.message = f"Missing spec for component: '{component}'"

    def __str__(self):
        return self.message

    def __repr__(self):
        return self.message


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
                self._load_residence_data(engine, data)
            elif section == "Businesses":
                self._load_business_data(engine, data)
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
    def _load_entity_archetype(engine: NeighborlyEngine, data: Dict[str, Any]) -> EntityArchetypeSpec:
        archetype = EntityArchetypeSpec(
            data['name'],
            is_template=data.get('template', False),
            attributes={
                'name': data['name'],
                'tags': data.get('tags', []),
                'inherits': data.get('inherits', None),
            }
        )

        if archetype["inherits"]:
            parent = engine.get_character_archetype(archetype["inherits"])

            # Copy component specs from the parent
            for component_spec in parent.get_components().values():
                archetype.add_component(copy.deepcopy(component_spec))

        if 'components' not in data:
            raise ValueError("Entity spec missing component definitions")

        for component in data['components']:
            component_name = component['type']

            options: Dict[str, Any] = component.get('options', {})

            component = archetype.try_component(component_name)
            if component:
                component.update(options)
            else:
                component = ComponentSpec(component_name, {**options})

            archetype.add_component(component)

        return archetype

    @staticmethod
    def _load_character_data(engine: NeighborlyEngine, characters: List[Dict[str, Any]]) -> None:
        """Process data related to defining character archetypes"""
        for data in characters:
            archetype = YamlDataLoader._load_entity_archetype(engine, data)

            character_component = archetype.try_component('GameCharacter')
            if character_component:
                # Create and register a new character config from
                # the options
                character_component['config_name'] = archetype.get_type()
                # GameCharacter.register_config(
                #     archetype.get_type(),
                #     CharacterType(**{
                #         'config_name': archetype.get_type(),
                #         'name': character_component.get_attribute('name'),
                #         'lifecycle': character_component.get_attribute('lifecycle'),
                #         # 'gender_overrides': character_component.get_attribute('gender_overrides'),
                #     })
                # )
            else:
                raise MissingComponentSpecError('GameCharacter')

            engine.add_character_archetype(archetype)

    @staticmethod
    def _load_place_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = YamlDataLoader._load_entity_archetype(engine, data)
            engine.add_place_archetype(archetype)

    @staticmethod
    def _load_business_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = YamlDataLoader._load_entity_archetype(engine, data)

            business_component = archetype.try_component('Business')
            if business_component:
                # Create and register a new character config from
                # the options
                if business_component.get_attribute("business_type") is None:
                    BusinessDefinition.register_type(
                        BusinessDefinition(**{
                            **business_component.get_attributes(),
                            'name': archetype.get_type(),
                        })
                    )
                    business_component.update(
                        {'business_type': archetype.get_type()})
            elif not archetype.is_template:
                raise MissingComponentSpecError('Business')

            engine.add_business_archetype(archetype)

    @staticmethod
    def _load_residence_data(engine: NeighborlyEngine, places: List[Dict[str, Any]]) -> None:
        """Process information regarding place archetypes"""
        for data in places:
            archetype = YamlDataLoader._load_entity_archetype(engine, data)
            engine.add_residence_archetype(archetype)

    @staticmethod
    def _load_relationship_tag_data(relationship_tags: List[Dict[str, Any]]) -> None:
        """Load list of dictionary objects defining relaitonship tags"""
        if not isinstance(relationship_tags, list):
            raise TypeError(
                f"Expected List of dicts but was {type(relationship_tags).__name__}")

        for entry in relationship_tags:
            # Convert the dictionary to an object
            tag = RelationshipTag(**entry)
            RelationshipTag.register_tag(tag)


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
