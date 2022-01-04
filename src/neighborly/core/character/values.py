from typing import Dict, Optional
from enum import Enum

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
    LIESURE_TIME = "liesure-time"
    LOYALTY = "loyalty"
    LUST = "lust"
    MATERIAL = "material"
    NATURE = "nature"
    PEACE = "peace"
    POWER = "power"
    RELIABILITY = "reliability"
    ROMANCE = "romance"
    SINGLEMINDED = "singleminded"
    SOCIAL = "social"
    SELF_CONTROL = "self-control"
    TRADITION = "tradition"
    TRANQUILITY = "tranquility"


_VALUE_INDICES: Dict[str, int] = {
    str(value_trait.value): index for index, value_trait in enumerate(ValueTrait)}


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

    def __init__(self, overrides: Optional[Dict[str, int]] = None, default: int = 0) -> None:
        self._traits: npt.NDArray[np.int8] = np.array(
            [default] * len(_VALUE_INDICES.keys()), dtype=np.int8)

        if overrides:
            for trait, value in overrides.items():
                self._traits[_VALUE_INDICES[trait]] = max(
                    TRAIT_MIN, min(TRAIT_MAX, value))

    @property
    def traits(self) -> npt.NDArray[np.int8]:
        return self._traits

    @staticmethod
    def calculate_compatibility(traits_a: 'CharacterValues', traits_b: 'CharacterValues') -> int:
        # Cosine similarity is a value between -1 and 1
        cos_sim: float = np.dot(traits_a.traits, traits_b.traits) / (
            np.linalg.norm(traits_a.traits) * np.linalg.norm(traits_b.traits))
        # Convert this to a score to be on the range [-50, 50]
        return round(cos_sim * 50)

    def __getitem__(self, trait: str) -> int:
        return self._traits[_VALUE_INDICES[trait]]

    def __setitem__(self, trait: str, value: int) -> None:
        self._traits[_VALUE_INDICES[trait]] = max(
            TRAIT_MIN, min(TRAIT_MAX, value))

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._traits.__repr__())
