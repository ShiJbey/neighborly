"""Special components and behavior tree nodes for implementing character behaviors"""

from abc import ABC, abstractmethod
from typing import Protocol, Dict

from neighborly.ai.behavior_tree import (
    BehaviorTree,
    SelectorBTNode,
    NodeState,
    Blackboard,
    DecoratorBTNode,
    AbstractBTNode,
)
from neighborly.core.ecs import World
from neighborly.core.engine import AbstractFactory, NeighborlyEngine


class CharacterBehavior(BehaviorTree):
    """Wraps a behavior tree and manages a single behavior that a character can perform"""


class IBehaviorSelectorNode(Protocol):
    """Abstract base class for nodes that select which behavior character will perform"""

    def choose_behavior(self) -> CharacterBehavior:
        """Choose a behavior to perform"""
        raise NotImplementedError()

    def get_available_behaviors(self) -> Dict[str, CharacterBehavior]:
        """Get all behaviors whose preconditions pass"""
        raise NotImplementedError()

    def get_all_behaviors(self) -> Dict[str, CharacterBehavior]:
        """Get all behaviors available to the selector"""
        raise NotImplementedError()


class PriorityNode(DecoratorBTNode):
    """Wraps a single subtree with a priority value"""

    __slots__ = "_priority"

    def __init__(self, priority: int = 0) -> None:
        super().__init__()
        self._priority = priority

    def get_priority(self) -> int:
        """Returns the priority of this tree"""
        return self._priority

    def evaluate(self, blackboard: Blackboard) -> NodeState:
        """Runs the underlying behavior tree"""
        self._state = self._children[0].evaluate(blackboard)
        return self._state


class PrioritySelectorNode(SelectorBTNode):
    """Evaluates subtrees in priority order and stops at the first successful evaluation"""

    def add_child(self, node: AbstractBTNode) -> None:
        """Add a child node to this node"""
        if not isinstance(node, PriorityNode):
            raise TypeError("Only Priority Nodes may be children of Priority Selectors")
        self._children.append(node)
        self._children.sort(
            key=lambda n: n.get_priority() if hasattr(n, "get_priority") else 0
        )


class RandomSelectorNode(SelectorBTNode):
    def evaluate(self, blackboard: Blackboard) -> NodeState:
        world: World = blackboard.get_value("world")
        engine = world.get_resource(NeighborlyEngine)
        engine.get_rng().shuffle(self._children)
        return super().evaluate(blackboard)


class BehaviorNodeFactory(AbstractFactory, ABC):
    def __init__(self, _type: str) -> None:
        super().__init__(_type)

    @abstractmethod
    def create(self, **kwargs) -> AbstractBTNode:
        """Create node instance"""
        raise NotImplementedError()


_node_factories: Dict[str, BehaviorNodeFactory] = {}
_behavior_bank: Dict[str, BehaviorTree] = {}


def register_node_factory(factory: BehaviorNodeFactory) -> None:
    global _node_factories
    _node_factories[factory.get_type()] = factory


def get_node_factory_for_type(type_name: str) -> BehaviorNodeFactory:
    return _node_factories[type_name]


def register_behavior(tree: BehaviorTree) -> None:
    """Add behavior tree to lookup table"""
    global _behavior_bank
    _behavior_bank[tree.get_type()] = tree


def get_behavior(type_name: str) -> BehaviorTree:
    return _behavior_bank[type_name]
