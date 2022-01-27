"""
Interfaces and classes to assist in creating
modular, authorable content.


This code has been adapted from the C++ examples
in Game AI Pro 3:

Dill, Kevin. "Six Factory System Tricks For Extensibility and Library Reuse."
    Game AI Pro 3. CRC Press, 2017. 87-114.
"""


from typing import Any, Callable, Dict, Generic, Protocol, TypeVar, List, Optional, Type
from abc import abstractmethod, ABC
import logging


logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="Component")


class SpecificationNode:

    __slots__ = "_children", "_node_type", "_attributes"

    def __init__(self, node_type: str, **kwargs) -> None:
        self._node_type: str = node_type
        self._attributes: Dict[str, Any] = {**kwargs}
        self._children: List["SpecificationNode"] = []

    def get_type(self) -> str:
        return self._node_type

    def add_child(self, node: "SpecificationNode") -> None:
        self._children.append(node)

    def __getitem__(self, key: str) -> Any:
        return self._attributes[key]

    def get_attributes(self) -> Dict[str, Any]:
        """Return attributes dict"""
        return self._attributes


class CreationData(ABC):

    __slots__ = "_preload_fn", "_specification_node"

    def __init__(self, node: SpecificationNode) -> None:
        self._specification_node: SpecificationNode = node
        self._preload_fn: Optional[Callable[[Any], None]] = None

    def get_node(self) -> SpecificationNode:
        return self._specification_node

    def set_preload_function(self, fn: Callable[[Any], None]):
        self._preload_fn = fn

    def construct_object(self, cls_type: Type[_T]) -> _T:
        """Construct an object of a specified type"""

        obj: _T = cls_type()

        if self._preload_fn:
            self._preload_fn(obj)

        success: bool = obj.load_data(self)

        return obj


class Component(Protocol):
    """Abstract interface for all components in the system"""

    @abstractmethod
    def load_data(self, creation_data: CreationData) -> bool:
        """Load data to from creation data"""
        ...


class AbstractConstructor(ABC, Generic[_T]):
    @abstractmethod
    def create(self, creation_data: CreationData) -> Optional[_T]:
        """Create a new instance of the given instance using the creation data"""
        raise NotImplementedError


class AbstractFactory(ABC, Generic[_T]):

    __slots__ = "_constructors"

    def __init__(self) -> None:
        self._constructors: List[AbstractConstructor[_T]] = []

    def add_constructor(self, constructor: AbstractConstructor[_T]) -> None:
        """Add a constructor to this factory"""
        self._constructors.append(constructor)

    def create(self, creation_data: CreationData) -> Optional[_T]:
        """Create a new instance of the given instance using the creation data"""
        ret_val: Optional[_T] = None

        for i in range(len(self._constructors), 0, -1):
            ret_val = self._constructors[i].create(creation_data)
            if ret_val:
                break

        if ret_val is None:
            logging.error(
                "Factory failed to create object of type '{}'".format(
                    creation_data.get_node().get_type()
                )
            )

        return ret_val
