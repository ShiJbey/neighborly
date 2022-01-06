from typing import Dict, Protocol

import numpy as np
import numpy.typing as npt


def clamp(value: int, minimum: int, maximum: int) -> int:
    return min(maximum, max(minimum, value))


class Personality(Protocol):
    """
    Personalities are additional character traits that affect
    relationships and decision making. They are intended to be
    one of the methods for users to customize agent behavior
    """

    def get_trait_modifiers(self) -> Dict[str, int]:
        raise NotImplementedError()


class OceanPersonality:
    """
    Personality based on the "Big Five"/O.C.E.A.N model
    """

    __slots__ = "_traits"

    TRAIT_MAX = 50
    TRAIT_MIN = -50

    def __init__(self,
                 openness: int = 0,
                 conscientiousness: int = 0,
                 extraversion: int = 0,
                 agreeableness: int = 0,
                 neuroticism: int = 0) -> None:

        self._traits: npt.NDArray[np.int32] = np.zeros([
            clamp(openness, self.TRAIT_MIN, self.TRAIT_MAX),
            clamp(conscientiousness, self.TRAIT_MIN, self.TRAIT_MAX),
            clamp(extraversion, self.TRAIT_MIN, self.TRAIT_MAX),
            clamp(agreeableness, self.TRAIT_MIN, self.TRAIT_MAX),
            clamp(neuroticism, self.TRAIT_MIN, self.TRAIT_MAX),
        ], dtype=np.int32)

    def get_trait_modifiers(self) -> Dict[str, int]:
        raise NotImplementedError()
