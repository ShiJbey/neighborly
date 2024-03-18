"""Default Skill Definition.

"""

from neighborly.components.skills import Skill
from neighborly.defs.base_types import SkillDef
from neighborly.ecs import GameObject, World


class DefaultSkillDef(SkillDef):
    """The default implementation of a skill definition."""

    def instantiate(self, world: World) -> GameObject:

        skill = world.gameobjects.spawn_gameobject(name=self.display_name)

        skill.add_component(
            Skill(
                definition_id=self.definition_id,
                display_name=self.display_name,
                description=self.description,
            )
        )

        return skill
