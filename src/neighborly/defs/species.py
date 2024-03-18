"""Default Species Definition."""

from neighborly.components.character import Species
from neighborly.components.traits import Trait
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

        species = world.gameobjects.spawn_gameobject(name=self.display_name)

        species.add_component(
            Trait(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                stat_modifiers=self.stat_modifiers,
                skill_modifiers=self.skill_modifiers,
                conflicting_traits=self.conflicts_with,
            )
        )
        species.add_component(
            Species(
                adolescent_age=self.adolescent_age,
                young_adult_age=self.young_adult_age,
                adult_age=self.adult_age,
                senior_age=self.senior_age,
                lifespan=self.lifespan,
                can_physically_age=self.can_physically_age,
            )
        )

        return species
