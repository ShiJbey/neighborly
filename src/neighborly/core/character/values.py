import random
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import numpy.typing as npt

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


class CharacterValues:
    """
    Values are what a character believes in and they are used
    for decision-making and relationship compatibility among
    other things.

    Individual values are integers on the range [-50,50], inclusive.

    This model of character values is borrowed from Dwarf Fortress'
    model of character beliefs/values outlined at the following link
    https://dwarffortresswiki.org/index.php/DF2014:Personality_trait
    """

    __slots__ = "_traits"

    def __init__(
            self, overrides: Optional[Dict[str, int]] = None, default: int = 0
    ) -> None:
        self._traits: npt.NDArray[np.int32] = np.array(
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
    def calculate_compatibility(
            traits_a: "CharacterValues", traits_b: "CharacterValues"
    ) -> int:
        # Cosine similarity is a value between -1 and 1
        cos_sim: float = np.dot(traits_a.traits, traits_b.traits) / (
                np.linalg.norm(traits_a.traits) * np.linalg.norm(traits_b.traits)
        )
        # Convert this to a score to be on the range [-50, 50]
        return round(cos_sim * 50)

    def get_high_values(self, n=3) -> List[str]:
        """Return the value names associated with the to n values"""
        # This code is adapted from https://stackoverflow.com/a/23734295

        ind = np.argpartition(self.traits, -n)[-n:]

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


def generate_character_values(n_likes: int = 3, n_dislikes: int = 3) -> CharacterValues:
    """Generate a new set of character values"""
    # Select Traits
    total_traits: int = n_likes + n_dislikes
    traits = [
        str(trait.value) for trait in random.sample(list(ValueTrait), total_traits)
    ]

    # select likes and dislikes
    high_values = random.sample(traits, n_likes)
    [traits.remove(trait) for trait in high_values]
    low_values = [*traits]

    # Generate values for each ([30,50] for high values, [-50,-30] for dislikes)
    values_overrides: Dict[str, int] = {}

    for trait in high_values:
        values_overrides[trait] = random.randint(30, 50)

    for trait in low_values:
        values_overrides[trait] = random.randint(-50, -30)

    return CharacterValues(values_overrides)
