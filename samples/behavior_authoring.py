import os
import pathlib

import neighborly.ai.behavior_tree as bt
from neighborly.ai.character_behavior import register_node_factory, get_behavior, BehaviorNodeFactory
from neighborly.ai.loader import XmlBehaviorLoader


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


if __name__ == "__main__":
    register_node_factory(SequenceNodeFactory())
    register_node_factory(SelectorNodeFactory())
    register_node_factory(InverterNodeFactory())
    register_node_factory(PrintNodeFactory())
    register_node_factory(WillPassNodeFactory())

    xml_path = pathlib.Path(os.path.abspath(__file__)).parent / "behaviors.xml"

    XmlBehaviorLoader(xml_path).load()

    get_behavior("make pizza").evaluate(bt.Blackboard())
