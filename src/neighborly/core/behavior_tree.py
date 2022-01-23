from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Any, Dict, Optional


class InvalidNodeState(Exception):
    """Raise this error when an invalid node state is reached during evaluation"""

    def __init__(self, node_state: str) -> None:
        super().__init__()
        self.node_state = node_state

    def __repr__(self) -> str:
        return f'InvalidNodeState(node_state={self.node_state})'

    def __str__(self) -> str:
        return f'Encountered invalid node state "{self.node_state}"'


class MissingBlackboardError(Exception):
    """Raise this error when an invalid node state is reached during evaluation"""

    def __init__(self) -> None:
        super().__init__()

    def __repr__(self) -> str:
        return f'MissingBlackboard()'

    def __str__(self) -> str:
        return f'Node blackboard is not set'


class BlackboardKeyNotFound(Exception):
    """Could not find a given key in the blackboard"""

    def __init__(self, key: str) -> None:
        super().__init__()
        self._key = key
        self.message = f'BlackboardKeyNotFound("{key}" could not be found in Blackboard)'

    def __repr__(self) -> str:
        return f'BlackboardKeyNotFound(key="{self._key}")'

    def __str__(self) -> str:
        return self.message


class Blackboard:
    """
    Dictionary of key/value pairs used while executing
    behavior trees
    """

    def __init__(self, values: Optional[Dict[str, Any]] = None) -> None:
        self._values: Dict[str, Any] = {}
        if values:
            for key, val in values.items():
                self._values[key] = val

    def get_value(self, key: str, required: bool = True, default: Optional[Any] = None) -> Any:
        if key not in self._values and required:
            raise BlackboardKeyNotFound(key)
        return self._values.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        self._values[key] = value

    def unset_value(self, key) -> None:
        del self._values[key]

    def clear(self) -> None:
        self._values.clear()


class NodeState(Enum):
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILURE = 'failure'


class AbstractBTNode(ABC):

    def __init__(self) -> None:
        self._state: 'NodeState' = NodeState.SUCCESS

    @property
    def state(self) -> 'NodeState':
        """Get the state of this node after execution"""
        return self._state

    @abstractmethod
    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        """Run the logic encapsulated in this node"""
        pass


class SequenceBTNode(AbstractBTNode):

    def __init__(self, nodes: List[AbstractBTNode]) -> None:
        super().__init__()
        self._nodes: List[AbstractBTNode] = nodes

    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        any_child_running: bool = False
        for node in self._nodes:
            res = node.evaluate(blackboard)
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

    def __init__(self, nodes: List[AbstractBTNode]) -> None:
        super().__init__()
        self._nodes: List[AbstractBTNode] = nodes

    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        for node in self._nodes:
            res = node.evaluate(blackboard)
            if res == NodeState.SUCCESS:
                self._state = NodeState.SUCCESS
                return self._state
            elif res == NodeState.FAILURE:
                break
            elif res == NodeState.RUNNING:
                self._state = NodeState.RUNNING
                return self._state
            else:
                raise InvalidNodeState(str(res))

        self._state = NodeState.FAILURE
        return self._state


class DecoratorBTNode(AbstractBTNode, ABC):

    def __init__(self, node: AbstractBTNode) -> None:
        super().__init__()
        self._node = node


class InverterNode(DecoratorBTNode):

    def __init__(self, node: AbstractBTNode) -> None:
        super().__init__(node)

    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        res = self._node.evaluate(blackboard)
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

    def __init__(self, root: AbstractBTNode) -> None:
        super().__init__()
        self._root = root

    @property
    def root(self) -> 'AbstractBTNode':
        return self._root

    def evaluate(self, blackboard: 'Blackboard') -> 'NodeState':
        """Evaluate the behavior tree"""
        res = self._root.evaluate(blackboard)
        self._state = res
        return res
