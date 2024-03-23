"""Default Trait Definition."""

from neighborly.defs.base_types import TraitDef
from neighborly.ecs import GameObject, World


class DefaultTraitDef(TraitDef):
    """Default trait definition."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()
