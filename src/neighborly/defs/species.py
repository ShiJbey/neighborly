"""Default Species Definition."""

from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World


class SpeciesDef(TraitDef):
    """A definition for a species type."""

    adolescent_age: int
    """Age this species reaches adolescence."""
    young_adult_age: int
    """Age this species reaches young adulthood."""
    adult_age: int
    """Age this species reaches main adulthood."""
    senior_age: int
    """Age this species becomes a senior/elder."""
    lifespan: int
    """The number of years that this species lives."""
    can_physically_age: bool = True
    """Does this character go through the various life stages."""
    starting_health: int = 1000
    """The amount of health points this species starts with."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()
