from __future__ import annotations

import random
from typing import Dict, Optional, Type

from neighborly.core.archetypes import (
    BusinessArchetypes,
    CharacterArchetypes,
    ResidenceArchetypes,
)
from neighborly.core.business import OccupationTypes
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
        "_character_archetypes",
        "_residence_archetypes",
        "_business_archetypes",
        "_occupation_types",
        "_inheritable_components",
    )

    def __init__(self, seed: Optional[int] = None) -> None:
        random.seed(seed)
        self._rng: random.Random = random.Random(seed)
        self._name_generator: TraceryNameFactory = TraceryNameFactory()
        self._component_types: Dict[str, Type[Component]] = {}
        self._character_archetypes: CharacterArchetypes = CharacterArchetypes()
        self._residence_archetypes: ResidenceArchetypes = ResidenceArchetypes()
        self._business_archetypes: BusinessArchetypes = BusinessArchetypes()
        self._occupation_types: OccupationTypes = OccupationTypes()

    @property
    def rng(self) -> random.Random:
        return self._rng

    @property
    def name_generator(self) -> TraceryNameFactory:
        return self._name_generator

    @property
    def character_archetypes(self) -> CharacterArchetypes:
        return self._character_archetypes

    @property
    def residence_archetypes(self) -> ResidenceArchetypes:
        return self._residence_archetypes

    @property
    def business_archetypes(self) -> BusinessArchetypes:
        return self._business_archetypes

    @property
    def occupation_types(self) -> OccupationTypes:
        return self._occupation_types

    def get_component(self, component_name: str) -> Type[Component]:
        return self._component_types[component_name]

    def add_component(self, component_type: Type[Component]) -> None:
        self._component_types[component_type.__name__] = component_type
