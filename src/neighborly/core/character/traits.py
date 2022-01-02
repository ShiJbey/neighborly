"""
Propensities can have a non-negative integer value between
0 and 100 inclusive

This model of propensity traits is borrowed from Dwarf Fortress:
https://dwarffortresswiki.org/index.php/DF2014:Personality_trait

All characters will have a propensities to help them make decisions
about what actions to take and how to respond to other characters
"""
from typing import Dict, Optional
import numpy as np
import numpy.typing as npt

TRAIT_MAX = 100
TRAIT_MIN = 0

AMBITION_TRAIT = "ambition"
ANGER_TRAIT = "anger"
ANXIETY_TRAIT = "anxiety"  # TBD
BASHFUL_TRAIT = "bashful"
CHEER_TRAIT = "cheer"
CONFIDENT_TRAIT = "confidence"
CURIOUS_TRAIT = "curious"
DEPRESSION_TRAIT = "depression"
ENVY_TRAIT = "envy"
FRIENDLYNESS_TRAIT = "friendlyness"
GREED_TRAIT = "greed"
HATE_TRAIT = "hate"
LOVE_TRAIT = "love"
LUST_TRAIT = "lust"
PRIDE_TRAIT = "pride"
RASH_TRAIT = "rash"
SINGLEMINDED_TRAIT = "singleminded"
SOCIAL_TRAIT = "social"    # Not from DF
STRESS_TRAIT = "stress"    # TBD


ALL_TRAITS = [
    AMBITION_TRAIT,
    ANGER_TRAIT,
    ANXIETY_TRAIT,
    BASHFUL_TRAIT,
    CHEER_TRAIT,
    CONFIDENT_TRAIT,
    CURIOUS_TRAIT,
    DEPRESSION_TRAIT,
    ENVY_TRAIT,
    FRIENDLYNESS_TRAIT,
    GREED_TRAIT,
    HATE_TRAIT,
    LOVE_TRAIT,
    LUST_TRAIT,
    PRIDE_TRAIT,
    RASH_TRAIT,
    SINGLEMINDED_TRAIT,
    SOCIAL_TRAIT,
    STRESS_TRAIT,
]


_TRAIT_INDICES: Dict[str, int] = {
    label: index for index, label in enumerate(ALL_TRAITS)}


class CharacterTraits:
    """
    Manages a character's propensity towards taking certain actions.
    """

    __slots__ = "_traits"

    def __init__(self, defaults: Optional[Dict[str, int]] = None) -> None:
        self._traits: npt.NDArray[np.uint8] = np.array(
            [50] * len(ALL_TRAITS), dtype=np.uint8)

        if defaults:
            for trait, value in defaults.items():
                self._traits[_TRAIT_INDICES[trait]] = max(
                    TRAIT_MIN, min(TRAIT_MAX, value))

    @property
    def traits(self) -> npt.NDArray[np.uint8]:
        return self._traits

    def __getitem__(self, trait: str) -> int:
        return self._traits[_TRAIT_INDICES[trait]]

    def __setitem__(self, trait: str, value: int) -> None:
        self._traits[_TRAIT_INDICES[trait]] = max(
            TRAIT_MIN, min(TRAIT_MAX, value))
