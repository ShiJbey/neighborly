"""
Talk of the Town uses a Big 5 personality model
to make entity decisions and determine
compatibility in social interactions
"""
from __future__ import annotations

import random
from typing import Any, Dict, Optional, cast

from neighborly.core.ecs import Component, IComponentFactory, World

BIG_FIVE_FLOOR = -1.0
BIG_FIVE_CAP = 1.0


class BigFivePersonality(Component):
    __slots__ = (
        "openness",
        "conscientiousness",
        "extroversion",
        "agreeableness",
        "neuroticism",
    )

    def __init__(
        self,
        openness: float = 0,
        conscientiousness: float = 0,
        extroversion: float = 0,
        agreeableness: float = 0,
        neuroticism: float = 0,
    ) -> None:
        super().__init__()
        self.openness: float = openness
        self.conscientiousness: float = conscientiousness
        self.extroversion: float = extroversion
        self.agreeableness: float = agreeableness
        self.neuroticism: float = neuroticism

    @classmethod
    def from_parents(
        cls, world: World, parent_a: Optional[Component], parent_b: Optional[Component]
    ) -> Component:
        """Build a new instance of the component using instances from the parents"""
        parent_a = cast(BigFivePersonality, parent_a)
        parent_b = cast(BigFivePersonality, parent_b)
        rng = world.get_resource(random.Random)

        openness: float = clamp(
            (
                (parent_a.openness + parent_b.openness / 2.0)
                + (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR))
                + BIG_FIVE_FLOOR
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        conscientiousness: float = clamp(
            (
                (parent_a.conscientiousness + parent_b.conscientiousness / 2.0)
                + (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR))
                + BIG_FIVE_FLOOR
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        extroversion: float = clamp(
            (
                (parent_a.extroversion + parent_b.extroversion / 2.0)
                + (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR))
                + BIG_FIVE_FLOOR
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        agreeableness: float = clamp(
            (
                (parent_a.agreeableness + parent_b.agreeableness / 2.0)
                + (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR))
                + BIG_FIVE_FLOOR
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        neuroticism: float = clamp(
            (
                (parent_a.neuroticism + parent_b.neuroticism / 2.0)
                + (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR))
                + BIG_FIVE_FLOOR
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        return BigFivePersonality(
            openness, conscientiousness, extroversion, agreeableness, neuroticism
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extroversion": self.extroversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

    def __repr__(self) -> str:
        return self.to_dict().__repr__()


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a floating point value within a min,max range"""
    return min(maximum, max(minimum, value))


class BigFivePersonalityFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Component:
        rng = world.get_resource(random.Random)

        openness: float = clamp(
            kwargs.get(
                "openness",
                (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)) + BIG_FIVE_FLOOR,
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        conscientiousness: float = clamp(
            kwargs.get(
                "conscientiousness",
                (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)) + BIG_FIVE_FLOOR,
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        extroversion: float = clamp(
            kwargs.get(
                "extroversion",
                (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)) + BIG_FIVE_FLOOR,
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        agreeableness: float = clamp(
            kwargs.get(
                "agreeableness",
                (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)) + BIG_FIVE_FLOOR,
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        neuroticism: float = clamp(
            kwargs.get(
                "neuroticism",
                (rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)) + BIG_FIVE_FLOOR,
            ),
            BIG_FIVE_FLOOR,
            BIG_FIVE_CAP,
        )

        return BigFivePersonality(
            openness, conscientiousness, extroversion, agreeableness, neuroticism
        )
