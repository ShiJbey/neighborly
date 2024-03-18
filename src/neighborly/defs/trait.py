"""Default Trait Definition."""

from neighborly.components.traits import Trait
from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World


class DefaultTraitDef(TraitDef):
    """Default trait definition."""

    def instantiate(self, world: World) -> GameObject:

        trait = world.gameobjects.spawn_gameobject(name=self.display_name)

        trait.add_component(
            Trait(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
                stat_modifiers=self.stat_modifiers,
                skill_modifiers=self.skill_modifiers,
                conflicting_traits=self.conflicts_with,
            )
        )

        return trait
