from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class InvalidNodeState(Exception):
    """Raise this error when an invalid node state is reached during evaluation"""

    __slots__ = "node_state"

    def __init__(self, node_state: str) -> None:
        super().__init__()
        self.node_state = node_state

    def __repr__(self) -> str:
        return f"InvalidNodeState(node_state={self.node_state})"

    def __str__(self) -> str:
        return f'Encountered invalid node state "{self.node_state}"'


class NodeState(enum.IntEnum):
    RUNNING = 0
    SUCCESS = enum.auto()
    FAILURE = enum.auto()


class AbstractBTNode(ABC):
    """Abstract base class for all nodes in behavior tree"""

    __slots__ = "_state", "_children", "_blackboard"

    def __init__(self, blackboard: Optional[Dict[str, Any]] = None) -> None:
        self._state: NodeState = NodeState.FAILURE
        self._children: List[AbstractBTNode] = []
        self._blackboard: Dict[str, Any] = blackboard if blackboard else {}

    @property
    def blackboard(self) -> Dict[str, Any]:
        """Return the blackboard instance for the node"""
        return self._blackboard

    def set_blackboard(self, blackboard: Dict[str, Any]) -> None:
        """Set the blackboard instance for the node"""
        self._blackboard = blackboard

    def get_state(self) -> NodeState:
        """Get the state of this node after evaluation"""
        return self._state

    def add_child(self, node: AbstractBTNode) -> None:
        """Add a child node to this node"""
        self._children.append(node)
        node.set_blackboard(self.blackboard)

    @abstractmethod
    def evaluate(self) -> NodeState:
        """Run the logic encapsulated in this node"""
        raise NotImplementedError()


class SequenceBTNode(AbstractBTNode):
    """A behavior tree node that runs its children in the order they were added

    This node succeeds when all children succeed. If any child fails, evaluation
    stops with that child, and a FAILURE state is returned
    """

    def __init__(self, nodes: Optional[List[AbstractBTNode]] = None) -> None:
        super().__init__()

        if nodes:
            for node in nodes:
                self.add_child(node)

    def evaluate(self) -> NodeState:
        any_child_running: bool = False
        for node in self._children:
            res = node.evaluate()
            if res == NodeState.SUCCESS:
                pass
            elif res == NodeState.FAILURE:
                self._state = NodeState.FAILURE
                return self._state
            elif res == NodeState.RUNNING:
                any_child_running = True
            else:
                raise InvalidNodeState(str(res))
        self._state = NodeState.RUNNING if any_child_running else NodeState.SUCCESS
        return self._state


class SelectorBTNode(AbstractBTNode):
    """Runs child nodes in order and returns success when any child returns success"""

    def __init__(self, nodes: Optional[List[AbstractBTNode]] = None) -> None:
        super().__init__()
        if nodes:
            for node in nodes:
                self.add_child(node)

    def evaluate(self) -> NodeState:
        for node in self._children:
            res = node.evaluate()
            if res == NodeState.SUCCESS:
                self._state = NodeState.SUCCESS
                return self._state
            elif res == NodeState.FAILURE:
                continue
            elif res == NodeState.RUNNING:
                self._state = NodeState.RUNNING
                return self._state
            else:
                raise InvalidNodeState(str(res))

        self._state = NodeState.FAILURE
        return self._state


class DecoratorBTNode(AbstractBTNode, ABC):
    """Takes a single child and performs an operation on the output"""

    def __init__(self, node: AbstractBTNode) -> None:
        super().__init__()

        if node:
            self.add_child(node)


class InverterNode(DecoratorBTNode):
    """Inverts the child's output from FAILURE to SUCCESS for vice versa"""

    def evaluate(self) -> NodeState:
        res = self._children[0].evaluate()
        if res == NodeState.SUCCESS:
            self._state = NodeState.FAILURE
        elif res == NodeState.FAILURE:
            self._state = NodeState.SUCCESS
        else:
            self._state = NodeState.RUNNING
        return self._state


class BehaviorTree(AbstractBTNode):
    """
    Behavior trees perform an atomic behaviors. Tree execution
    cannot be interrupted, but it can end early in the case of
    failure
    """

    def __init__(self, root: Optional[AbstractBTNode] = None) -> None:
        super().__init__()
        if root:
            self.add_child(root)

    def add_child(self, node: AbstractBTNode) -> None:
        if self._children:
            raise ValueError("BehaviorTree already has a single child")
        return super().add_child(node)

    def evaluate(self) -> NodeState:
        """Evaluate the behavior tree"""
        self._state = self._children[0].evaluate()
        return self._state
