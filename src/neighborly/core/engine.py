from collections import defaultdict
from typing import Any, Dict, List, Optional, DefaultDict

import esper

from neighborly.core.authoring import ComponentFactory, ComponentSpec, EntityArchetypeSpec
from neighborly.core.business import BusinessConfig, Business
from neighborly.core.gameobject import GameObject
from neighborly.core.location import Location
from neighborly.core.name_generation import get_name


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
    )

    def __init__(self) -> None:
        self._component_specs: DefaultDict[str, Dict[str, ComponentSpec]] = defaultdict(dict)
        self._component_factories: Dict[str, ComponentFactory] = {}
        self._character_archetypes: Dict[str, EntityArchetypeSpec] = {}
        self._place_archetypes: DefaultDict[str, Dict[str, EntityArchetypeSpec]] = defaultdict(dict)

    def add_character_archetype(self, archetype: EntityArchetypeSpec, name: Optional[str] = None) -> None:
        if name:
            self._character_archetypes[name] = archetype
        else:
            self._character_archetypes[archetype.get_type()] = archetype

    def get_character_archetype(self, name: str) -> EntityArchetypeSpec:
        return self._character_archetypes[name]

    def add_place_archetype(self, archetype: EntityArchetypeSpec, name: Optional[str] = None) -> None:
        if name:
            self._character_archetypes[name] = archetype
        else:
            self._character_archetypes[archetype.get_type()] = archetype

    def register_component_factory(self, factory: ComponentFactory):
        self._component_factories[factory.get_type()] = factory

    def get_component_factory_for_type(self, type_name: str) -> ComponentFactory:
        return self._component_factories[type_name]

    def create_character(
            self,
            world: esper.World, archetype_name: str = "default"
    ) -> int:

        archetype = self._character_archetypes[archetype_name]

        components: List[Any] = []

        for name, spec in archetype.get_components().items():
            factory = self.get_component_factory_for_type(name)
            components.append(factory.create(spec))

        character_id = world.create_entity(*components)

        return character_id

    def create_place(self, world: esper.World, archetype_name: str, **kwargs) -> int:
        place_def = self._place_archetypes[archetype_name]

        structure_id = world.create_entity()

        location = Location(place_def["max capacity"], place_def["activities"])

        place_name = (
            get_name(place_def["name"]) if "name" in place_def else archetype_name
        )

        game_object = GameObject(place_name)

        world.add_component(structure_id, game_object)
        world.add_component(structure_id, location)

        if "Business" in place_def:
            business = Business(BusinessConfig(**place_def["Business"]), place_name)
            world.add_component(structure_id, business)

        return structure_id
