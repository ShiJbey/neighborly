from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
import numpy.typing as npt

from neighborly.core.ecs import Component, World
from neighborly.core.engine import NeighborlyEngine

TRAIT_MAX = 50
TRAIT_MIN = -50


class ValueTrait(Enum):
    ADVENTURE = "adventure"
    AMBITION = "ambition"
    EXCITEMENT = "excitement"
    COMMERCE = "commerce"
    CONFIDENCE = "confidence"
    CURIOSITY = "curiosity"
    FAMILY = "family"
    FRIENDSHIP = "friendship"
    WEALTH = "wealth"
    HEALTH = "health"
    INDEPENDENCE = "independence"
    KNOWLEDGE = "knowledge"
    LEISURE_TIME = "leisure-time"
    LOYALTY = "loyalty"
    LUST = "lust"
    MATERIAL_THINGS = "material things"
    NATURE = "nature"
    PEACE = "peace"
    POWER = "power"
    RELIABILITY = "reliability"
    ROMANCE = "romance"
    SINGLE_MINDEDNESS = "single mindedness"
    SOCIAL = "social"
    SELF_CONTROL = "self-control"
    TRADITION = "tradition"
    TRANQUILITY = "tranquility"


_VALUE_INDICES: Dict[str, int] = {
    str(value_trait.value): index for index, value_trait in enumerate(ValueTrait)
}


class PersonalValues(Component):
    """
    Values are what an entity believes in. They are used
    for decision-making and relationship compatibility among
    other things.

    Individual values are integers on the range [-50,50], inclusive.

    This model of entity values is borrowed from Dwarf Fortress'
    model of entity beliefs/values outlined at the following link
    https://dwarffortresswiki.org/index.php/DF2014:Personality_trait
    """

    __slots__ = "_traits"

    def __init__(
        self, overrides: Optional[Dict[str, int]] = None, default: int = 0
    ) -> None:
        super().__init__()
        self._traits: npt.NDArray[np.int32] = np.array(  # type: ignore
            [default] * len(_VALUE_INDICES.keys()), dtype=np.int32
        )

        if overrides:
            for trait, value in overrides.items():
                self._traits[_VALUE_INDICES[trait]] = max(
                    TRAIT_MIN, min(TRAIT_MAX, value)
                )

    @property
    def traits(self) -> npt.NDArray[np.int32]:
        return self._traits

    @staticmethod
    def compatibility(
        character_a: PersonalValues, character_b: PersonalValues
    ) -> float:
        # Cosine similarity is a value between -1 and 1
        cos_sim: float = np.dot(character_a.traits, character_b.traits) / (  # type: ignore
            np.linalg.norm(character_a.traits) * np.linalg.norm(character_b.traits)  # type: ignore
        )

        return cos_sim

    def get_high_values(self, n: int = 3) -> List[str]:
        """Return the value names associated with the n values"""
        # This code is adapted from https://stackoverflow.com/a/23734295

        ind = np.argpartition(self.traits, -n)[-n:]  # type: ignore

        value_names = list(_VALUE_INDICES.keys())

        return [value_names[i] for i in ind]

    def __getitem__(self, trait: str) -> int:
        return self._traits[_VALUE_INDICES[trait]]

    def __setitem__(self, trait: str, value: int) -> None:
        self._traits[_VALUE_INDICES[trait]] = max(TRAIT_MIN, min(TRAIT_MAX, value))

    def __str__(self) -> str:
        return f"Values Most: {self.get_high_values()}"

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._traits.__repr__())

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            **{trait.name: self._traits[i] for i, trait in enumerate(list(ValueTrait))},
        }

    @classmethod
    def create(cls, world: World, **kwargs: Any) -> Component:
        engine = world.get_resource(NeighborlyEngine)
        n_likes: int = kwargs.get("n_likes", 3)
        n_dislikes: int = kwargs.get("n_dislikes", 3)

        traits = [
            str(trait.value)
            for trait in engine.rng.sample(list(ValueTrait), n_likes + n_dislikes)
        ]

        # select likes and dislikes
        high_values = engine.rng.sample(traits, n_likes)

        low_values = list(filter(lambda t: t not in high_values, traits))

        # Generate values for each ([30,50] for high values, [-50,-30] for dislikes)
        values_overrides: Dict[str, int] = {}

        for trait in high_values:
            values_overrides[trait] = engine.rng.randint(30, 50)

        for trait in low_values:
            values_overrides[trait] = engine.rng.randint(-50, -30)

        return PersonalValues(values_overrides)
