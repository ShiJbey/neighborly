"""
Talk of the Town uses a Big 5 personality model
to make character decisions and determine
compatibility in social interactions
"""
from typing import Any, Dict, Optional

from neighborly.core.ecs import Component
from neighborly.core.engine import (
    AbstractFactory,
    ComponentDefinition,
    NeighborlyEngine,
)

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

    def __repr__(self) -> str:
        return self.to_dict().__repr__()


class BigFivePersonalityFactory(AbstractFactory):
    """Creates instances of BigFivePersonality components"""

    def __init__(self) -> None:
        super().__init__("BigFivePersonality")

    def create(self, spec: ComponentDefinition, **kwargs) -> BigFivePersonality:
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

        return BigFivePersonality(
            openness, conscientiousness, extroversion, agreeableness, neuroticism
        )


def personality_from_parents(
    parent_a: BigFivePersonality, parent_b: Optional[BigFivePersonality] = None
) -> BigFivePersonality:
    """
    Create a new BigFivePersonality instance using the personality
    models from parents

    Parameters
    ----------
    parent_a : BigFivePersonality
        Personality model for the first parent
    parent_b : Optional[BigFivePersonality]
        Optional personality model for a second parent

    Returns
    -------
    BigFivePersonality
        The final generated personality model
    """

    raise NotImplementedError()
