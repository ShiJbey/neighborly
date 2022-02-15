from collections import defaultdict
from typing import Dict, List, Optional, DefaultDict

from neighborly.core.authoring import ComponentFactory, ComponentSpec, EntityArchetypeSpec
from neighborly.core.ecs import GameObject, Component
from neighborly.core.rng import RandNumGenerator, DefaultRNG
from neighborly.factories.factories import RoutineFactory, GameCharacterFactory, LocationFactory


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
        "_component_specs",
        "_rng"
    )

    def __init__(self, rng: Optional[RandNumGenerator] = None) -> None:
        self._component_specs: DefaultDict[str, Dict[str, ComponentSpec]] = defaultdict(dict)
        self._component_factories: Dict[str, ComponentFactory] = {}
        self._character_archetypes: Dict[str, EntityArchetypeSpec] = {}
        self._place_archetypes: Dict[str, EntityArchetypeSpec] = {}
        self._rng: RandNumGenerator = rng if rng else DefaultRNG()

    def get_rng(self) -> RandNumGenerator:
        return self._rng

    def add_character_archetype(self, archetype: EntityArchetypeSpec, name: Optional[str] = None) -> None:
        if name:
            self._character_archetypes[name] = archetype
        else:
            self._character_archetypes[archetype.get_type()] = archetype

    def get_character_archetype(self, archetype_name: str) -> EntityArchetypeSpec:
        return self._character_archetypes[archetype_name]

    def add_place_archetype(self, archetype: EntityArchetypeSpec, name: Optional[str] = None) -> None:
        if name:
            self._place_archetypes[name] = archetype
        else:
            self._place_archetypes[archetype.get_type()] = archetype

    def get_place_archetype(self, archetype_name: str) -> EntityArchetypeSpec:
        return self._place_archetypes[archetype_name]

    def add_component_factory(self, factory: ComponentFactory) -> None:
        self._component_factories[factory.get_type()] = factory

    def get_component_factory(self, type_name: str) -> ComponentFactory:
        return self._component_factories[type_name]

    def create_character(self, archetype_name: str) -> GameObject:

        archetype = self._character_archetypes[archetype_name]

        components: List[Component] = []

        for name, spec in archetype.get_components().items():
            factory = self.get_component_factory(name)
            components.append(factory.create(spec))

        gameobject = GameObject(name=archetype_name, components=components)

        return gameobject

    def create_place(self, archetype_name: str) -> GameObject:
        archetype: EntityArchetypeSpec = self._place_archetypes[archetype_name]

        components: List[Component] = []

        for name, spec in archetype.get_components().items():
            factory = self.get_component_factory(name)
            components.append(factory.create(spec))

        gameobject = GameObject(name=archetype_name, components=components)

        return gameobject


def create_default_engine(rng: Optional[RandNumGenerator] = None) -> NeighborlyEngine:
    engine = NeighborlyEngine(rng)
    engine.add_component_factory(GameCharacterFactory())
    engine.add_component_factory(RoutineFactory())
    engine.add_component_factory(LocationFactory())
    return engine
