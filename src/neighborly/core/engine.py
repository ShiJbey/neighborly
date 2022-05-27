from abc import ABC
from typing import Any, Optional, Protocol, Dict, List

from neighborly.core.ecs import Component, GameObject
from neighborly.core.rng import IRandNumGenerator
from neighborly.core.utils.tracery import set_grammar_rng


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


class ComponentDefinition:
    """
    Collection of Key-Value pairs passed to factories when to
    instantiating instances of components
    """

    __slots__ = "_component_type", "_attributes"

    def __init__(
        self,
        component_type: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._component_type: str = component_type
        self._attributes: Dict[str, Any] = attributes if attributes else {}

    def get_type(self) -> str:
        """Returns the name of the type of component this spec is for"""
        return self._component_type

    def get_attributes(self) -> Dict[str, Any]:
        """Get all the attributes associated with this definition"""
        return self._attributes

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get a specific attribute associated with this definition"""
        return self._attributes.get(key, default)

    def update(self, new_attributes: Dict[str, Any]) -> None:
        """Update the attributes using a given Dict of values"""
        self._attributes.update(new_attributes)

    def __getitem__(self, key: str) -> Any:
        """Set an attribute using a str key"""
        return self._attributes[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Set an attribute using a str key"""
        self._attributes[key] = value


class EntityArchetypeDefinition:
    """Collection of Component specs used to instantiate instances of entities"""

    __slots__ = (
        "_name",
        "_components",
        "_attributes",
        "_is_template",
    )

    def __init__(
        self,
        name: str,
        components: Optional[Dict[str, ComponentDefinition]] = None,
        is_template: bool = False,
    ) -> None:
        self._name: str = name
        self._is_template: bool = is_template
        self._components: Dict[str, ComponentDefinition] = (
            components if components else {}
        )

    def is_template(self) -> bool:
        return self._is_template

    def get_components(self) -> Dict[str, ComponentDefinition]:
        """Return the ComponentSpecs that make up this archetype"""
        return self._components

    def try_component(self, name: str) -> Optional[ComponentDefinition]:
        """Try to get a component definition by name"""
        return self._components.get(name, None)

    def get_name(self) -> str:
        """Get the type of archetype this is"""
        return self._name

    def get_attributes(self) -> Dict[str, Any]:
        """Get the type of archetype this is"""
        return self._attributes

    def add_component(self, node: ComponentDefinition) -> None:
        """Add (or overwrites) a component spec attached to this archetype"""
        self._components[node.get_type()] = node

    def has_component(self, *components: str) -> bool:
        """Return True if this archetype has the given components"""
        return all([c in self._components for c in components])

    def __getitem__(self, attribute: str) -> Any:
        """Get a value from this archetype's attributes"""
        return self._attributes[attribute]


class IComponentFactory(Protocol):
    """Interface for Factory classes that are used to construct entity components"""

    def get_type(self) -> str:
        """Return the name of the type this factory creates"""
        raise NotImplementedError()

    def create(self, spec: ComponentDefinition, **kwargs) -> Component:
        """Create component instance"""
        raise NotImplementedError()


class NeighborlyEngine:
    """Manages all the factories for creating entities and archetypes

    Attributes
    ----------
    _component_factories: Dict[str, AbstractFactory[Any]]
        Map of component class names to factories that produce them
    _character_archetypes: Dict[str, Dict[str, Any]]
        Map of archetype names to their specification data
    _place_archetypes: Dict[str, Dict[str, Any]]
        Map of archetype names to their specification data
    """

    __slots__ = (
        "_component_factories",
        "_character_archetypes",
        "_place_archetypes",
        "_business_archetypes",
        "_residence_archetypes",
        "_rng",
    )

    def __init__(self, rng: IRandNumGenerator) -> None:
        self._component_factories: Dict[str, IComponentFactory] = {}
        self._character_archetypes: Dict[str, EntityArchetypeDefinition] = {}
        self._business_archetypes: Dict[str, EntityArchetypeDefinition] = {}
        self._residence_archetypes: Dict[str, EntityArchetypeDefinition] = {}
        self._place_archetypes: Dict[str, EntityArchetypeDefinition] = {}
        self._rng: IRandNumGenerator = rng
        set_grammar_rng(self._rng)

    def get_rng(self) -> IRandNumGenerator:
        return self._rng

    def add_character_archetype(self, archetype: EntityArchetypeDefinition) -> None:
        self._character_archetypes[archetype.get_name()] = archetype

    def get_character_archetype(self, archetype_name: str) -> EntityArchetypeDefinition:
        return self._character_archetypes[archetype_name]

    def get_character_archetypes(self) -> List[EntityArchetypeDefinition]:
        return list(self._character_archetypes.values())

    def add_place_archetype(self, archetype: EntityArchetypeDefinition) -> None:
        self._place_archetypes[archetype.get_name()] = archetype

    def add_residence_archetype(self, archetype: EntityArchetypeDefinition) -> None:
        self._residence_archetypes[archetype.get_name()] = archetype

    def add_business_archetype(self, archetype: EntityArchetypeDefinition) -> None:
        self._business_archetypes[archetype.get_name()] = archetype

    def get_place_archetype(self, archetype_name: str) -> EntityArchetypeDefinition:
        return self._place_archetypes[archetype_name]

    def get_business_archetype(self, archetype_name: str) -> EntityArchetypeDefinition:
        return self._business_archetypes[archetype_name]

    def get_residence_archetype(self, archetype_name: str) -> EntityArchetypeDefinition:
        return self._residence_archetypes[archetype_name]

    def get_residence_archetypes(self) -> List[EntityArchetypeDefinition]:
        return list(self._residence_archetypes.values())

    def filter_place_archetypes(self, options: Dict[str, Any]) -> List[str]:
        """Retrieve a set of place archetypes based on given options"""
        results: List[str] = []

        include: List[str] = options.get("include", [])
        exclude: List[str] = options.get("exclude", [])

        for _, spec in self._place_archetypes.items():
            if spec.has_component(*include) and not spec.has_component(*exclude):
                results.append(spec.get_name())

        return results

    def add_component_factory(self, factory: IComponentFactory) -> None:
        self._component_factories[factory.get_type()] = factory

    def get_component_factory(self, type_name: str) -> IComponentFactory:
        return self._component_factories[type_name]

    def create_character(self, archetype_name: str, **kwargs) -> GameObject:
        archetype = self._character_archetypes[archetype_name]
        return self.create_entity(archetype, **kwargs)

    def create_place(self, archetype_name: str, **kwargs) -> GameObject:
        archetype = self._place_archetypes[archetype_name]
        return self.create_entity(archetype, **kwargs)

    def create_business(self, archetype_name: str, **kwargs) -> GameObject:
        archetype = self._business_archetypes[archetype_name]
        return self.create_entity(archetype, **kwargs)

    def create_residence(self, archetype_name: str, **kwargs) -> GameObject:
        archetype = self._residence_archetypes[archetype_name]
        return self.create_entity(archetype, **kwargs)

    def create_entity(
        self, archetype: EntityArchetypeDefinition, **kwargs
    ) -> GameObject:
        """Create a new GameObject and attach the components in the spec"""
        components: List[Component] = []

        for name, spec in archetype.get_components().items():
            factory = self.get_component_factory(name)
            components.append(factory.create(spec, **{**kwargs, "rng": self.get_rng()}))

        gameobject = GameObject(
            archetype_name=archetype.get_name(), components=components
        )

        return gameobject
