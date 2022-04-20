from typing import Set, List, Tuple, Optional
from xml.etree import ElementTree as ET

from neighborly.ai.behavior_tree import BehaviorTree, AbstractBTNode
from neighborly.ai.character_behavior import register_behavior, get_node_factory_for_type
from neighborly.loaders import AnyPath


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
