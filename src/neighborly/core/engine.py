from typing import Any, Dict, Optional

import esper

from neighborly.core.authoring import AbstractFactory, CreationData


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
        "_component_defs",
    )

    def __init__(self) -> None:
        self._component_factories: Dict[str, AbstractFactory[Any]] = {}
        self._character_archetypes: Dict[str, Dict[str, Any]] = {}
        self._place_archetypes: Dict[str, Dict[str, Any]] = {}

    def add_character_archetype(self, name: str, data: Dict[str, Any]) -> None:
        self._character_archetypes[name] = data

    def add_place_archetype(self, name: str, data: Dict[str, Any]) -> None:
        self._place_archetypes[name] = data

    def register_component_factory(self, name: str, factory: AbstractFactory):
        self._component_factories[name] = factory

    def create_character(self, world: esper.World, name: str, **kwargs) -> int:

        # character_id = world.create_entity()

        # character = GameCharacter.create(
        #     config=_character_config_registry[config_name], age_range=age_range
        # )

        # world.add_component(character_id, GameObject(str(character.name)))
        # world.add_component(character_id, character)
        # world.add_component(character_id, Routine())

        # return character_id, character
        ...
