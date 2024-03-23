"""Default Skill Definition.

"""

from neighborly.defs.base_types import SkillDef
from neighborly.ecs import GameObject, World


class DefaultSkillDef(SkillDef):
    """The default implementation of a skill definition."""

    def instantiate(self, world: World) -> GameObject:
        raise NotImplementedError()
