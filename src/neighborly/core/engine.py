from __future__ import annotations

import random
from typing import Dict, Optional, Type

import neighborly.core.utils.tracery as tracery
from neighborly.core.ecs import Component
from neighborly.core.name_generation import TraceryNameFactory


class NeighborlyEngine:
    """
    An engine stores and instantiates entity archetypes for characters, businesses,
    residences, and other places.

    There should only be one NeighborlyEngine instance per simulation. It is designed
    to handle the internal logic of determining when to create certain entities. For
    example, the engine creates characters entities using spawn multipliers associated
    with each archetype.
    """

    __slots__ = (
        "_rng",
        "_name_generator",
        "_component_types",
    )

    def __init__(self, seed: Optional[int] = None) -> None:
        self._rng: random.Random = random.Random(seed)
        self._name_generator: TraceryNameFactory = TraceryNameFactory()
        tracery.set_grammar_rng(self._rng)
        self._component_types: Dict[str, Type[Component]] = {}

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def name_generator(self) -> TraceryNameFactory:
        return self._name_generator

    def get_component(self, component_name: str) -> Type[Component]:
        return self._component_types[component_name]

    def add_component(self, component_type: Type[Component]) -> None:
        self._component_types[component_type.__name__] = component_type
