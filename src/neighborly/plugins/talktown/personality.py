"""
Talk of the Town uses a Big 5 personality model
to make entity decisions and determine
compatibility in social interactions
"""
from __future__ import annotations

from typing import Any, Dict

from neighborly.core.ecs import Component, World
from neighborly.core.engine import NeighborlyEngine

BIG_FIVE_FLOOR = -1.0
BIG_FIVE_CAP = 1.0


class BigFivePersonality(Component):
    """Relationship model"""

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

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extroversion": self.extroversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
        }

    @classmethod
    def create(cls, world: World, **kwargs: Any) -> BigFivePersonality:
        """Create new instance given component spec"""
        engine: NeighborlyEngine = kwargs["engine"]

        openness: float = (
            engine.rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)
        ) + BIG_FIVE_FLOOR

        conscientiousness: float = (
            engine.rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)
        ) + BIG_FIVE_FLOOR

        extroversion: float = (
            engine.rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)
        ) + BIG_FIVE_FLOOR

        agreeableness: float = (
            engine.rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)
        ) + BIG_FIVE_FLOOR

        neuroticism: float = (
            engine.rng.random() * (BIG_FIVE_CAP - BIG_FIVE_FLOOR)
        ) + BIG_FIVE_FLOOR

        return cls(
            openness, conscientiousness, extroversion, agreeableness, neuroticism
        )

    def __repr__(self) -> str:
        return self.to_dict().__repr__()
