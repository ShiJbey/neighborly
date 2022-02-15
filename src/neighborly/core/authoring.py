from abc import ABC
from typing import Optional, Dict, Any, List, Protocol

from neighborly.core.ecs import Component


class AbstractFactory(ABC):
    """Abstract class for factory instances

    Attributes
    ----------
    _type: str
        The name of the type of component the factory instantiates
    """

    __slots__ = "_type"

    def __init__(self, name: str) -> None:
        self._type = name

    def get_type(self) -> str:
        """Return the name of the type this factory creates"""
        return self._type


class ComponentSpec:
    """Collection of Key-Value pairs used to instantiate instances of components"""

    __slots__ = "_children", "_node_type", "_attributes", "_parent"

    def __init__(self, node_type: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        self._node_type: str = node_type
        self._attributes: Dict[str, Any] = attributes if attributes else {}
        self._parent: Optional["ComponentSpec"] = None
        self._children: List["ComponentSpec"] = []

    def get_type(self) -> str:
        return self._node_type

    def set_parent(self, node: "ComponentSpec") -> None:
        self._parent = node

    def add_child(self, node: "ComponentSpec") -> None:
        self._children.append(node)

    def get_attributes(self) -> Dict[str, Any]:
        return self._attributes

    def __getitem__(self, key: str) -> Any:
        if key in self._attributes:
            return self._attributes[key]
        elif self._parent:
            return self._parent[key]
        raise KeyError(key)

    def __contains__(self, attribute_name: str) -> bool:
        return attribute_name in self._attributes


class EntityArchetypeSpec:
    """Collection of Component specs used to instantiate instances of entities"""

    __slots__ = "_type", "_components", "_attributes"

    def __init__(
            self,
            name: str,
            components: Optional[Dict[str, ComponentSpec]] = None,
            attributes: Optional[Dict[str, Any]] = None
    ) -> None:
        self._type: str = name
        self._components: Dict[str, ComponentSpec] = components if components else {}
        self._attributes: Dict[str, Any] = attributes if attributes else {}

    def get_components(self) -> Dict[str, ComponentSpec]:
        """Return the ComponentSpecs that make up this archetype"""
        return self._components

    def get_type(self) -> str:
        """Get the type of archetype this is"""
        return self._type

    def get_attributes(self) -> Dict[str, Any]:
        """Get the type of archetype this is"""
        return self._attributes

    def add_component(self, node: ComponentSpec) -> None:
        """Add (or overwrites) a component spec attached to this archetype"""
        self._components[node.get_type()] = node


class ComponentFactory(Protocol):
    """Interface for Factory classes that are used to construct entity components"""

    def get_type(self) -> str:
        """Return the name of the type this factory creates"""
        raise NotImplementedError()

    def create(self, spec: ComponentSpec) -> Component:
        """Create component instance"""
        raise NotImplementedError()
