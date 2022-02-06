import os
import pathlib
import sys
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple

import neighborly.ai.behavior_tree as bt


class AbstractFactory(ABC):
    __slots__ = "_type"

    def __init__(self, _type: str) -> None:
        self._type = _type

    def get_type(self) -> str:
        return self._type


class BehaviorNodeFactory(AbstractFactory, ABC):
    def __init__(self, _type: str) -> None:
        super().__init__(_type)

    @abstractmethod
    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        raise NotImplementedError()


class InverterNodeFactory(BehaviorNodeFactory):
    def __init__(self) -> None:
        super().__init__("Inverter")

    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        return bt.InverterNode()


class SequenceNodeFactory(BehaviorNodeFactory):
    def __init__(self) -> None:
        super().__init__("Sequence")

    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        return bt.SequenceBTNode()


class SelectorNodeFactory(BehaviorNodeFactory):
    def __init__(self) -> None:
        super().__init__("Selector")

    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        return bt.SelectorBTNode()


class PrintNode(bt.AbstractBTNode):
    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def evaluate(self, blackboard: bt.Blackboard) -> bt.NodeState:
        print(self.message)
        self._state = bt.NodeState.SUCCESS
        return self._state


class PrintNodeFactory(BehaviorNodeFactory):
    def __init__(self) -> None:
        super().__init__("Print")

    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        return PrintNode(kwargs["message"])


class WillPassNode(bt.AbstractBTNode):
    def __init__(self, value: bool) -> None:
        super().__init__()
        self.value = value

    def evaluate(self, blackboard: bt.Blackboard) -> bt.NodeState:
        if self.value and self._children:
            self._state = self._children[0].evaluate(blackboard)
        else:
            self._state = bt.NodeState.FAILURE
        return self._state


class WillPassNodeFactory(BehaviorNodeFactory):
    def __init__(self) -> None:
        super().__init__("WillPass")

    def create(self, **kwargs) -> bt.AbstractBTNode:
        """Create node instance"""
        str_value: str = str(kwargs["value"]).lower().strip()

        if str_value in ("true", "yes"):
            value = True
        elif str_value in ("false", "no"):
            value = False
        else:
            raise ValueError(f"Value '{str_value}' for WillPassNode not recognized")

        return WillPassNode(value)


_node_factories: Dict[str, BehaviorNodeFactory] = {}


def register_node_factory(factory: BehaviorNodeFactory) -> None:
    global _node_factories
    _node_factories[factory.get_type()] = factory


def get_node_factory_for_type(type_name: str) -> BehaviorNodeFactory:
    return _node_factories[type_name]


def construct_behavior(el: ET.Element) -> bt.BehaviorTree:
    behavior_tree: bt.BehaviorTree = bt.BehaviorTree(el.attrib["type"])

    # Perform DFS, linking child nodes to their parent
    visited: Set[ET.Element] = set()
    stack: List[Tuple[Optional[bt.AbstractBTNode], ET.Element]] = list()

    stack.append((None, el))

    while stack:
        bt_node, xml_node = stack.pop()
        if xml_node not in visited:
            visited.add(xml_node)

            new_node: Optional[bt.AbstractBTNode] = None
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


_behavior_bank: Dict[str, bt.BehaviorTree] = {}


def register_behavior(tree: bt.BehaviorTree) -> None:
    """Add behavior tree to lookup table"""
    global _behavior_bank
    _behavior_bank[tree.get_type()] = tree


def get_behavior(type_name: str) -> bt.BehaviorTree:
    return _behavior_bank[type_name]


if __name__ == "__main__":
    register_node_factory(SequenceNodeFactory())
    register_node_factory(SelectorNodeFactory())
    register_node_factory(InverterNodeFactory())
    register_node_factory(PrintNodeFactory())
    register_node_factory(WillPassNodeFactory())

    xml_path = pathlib.Path(os.path.abspath(__file__)).parent / "behaviors.xml"

    tree = ET.parse(xml_path)

    # Check that the root node has the behavior tag.
    root = tree.getroot()

    if root.tag != "Behaviors":
        print("Root tag of XML must be '<Behaviors>'")
        sys.exit(1)

    # Create a new behavior tree for each behavior node
    for child in root:
        register_behavior(construct_behavior(child))

    get_behavior("make pizza").evaluate(bt.Blackboard())
