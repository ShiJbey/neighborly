"""Skill Component Factories.

"""

import random
from typing import Any

from neighborly.components.skills import Skills
from neighborly.ecs import Component, ComponentFactory, World
from neighborly.libraries import SkillLibrary


class SkillsFactory(ComponentFactory):
    """Create Skill instances."""

    __component__ = "Skills"

    def instantiate(self, world: World, /, **kwargs: Any) -> Component:

        rng = world.resource_manager.get_resource(random.Random)
        skill_library = world.resource_manager.get_resource(SkillLibrary)
        skills = Skills()

        skill_entries: list[dict[str, Any]] = kwargs.get("skills", [])

        for entry in skill_entries:
            base_value = 0

            if value := entry.get("value"):
                base_value = int(value)

            elif value_range := entry.get("value_range"):
                min_value, max_value = (int(x.strip()) for x in value_range.split("-"))
                base_value = rng.randint(min_value, max_value)

            if skill_id := entry.get("with_id"):
                skill = skill_library.get_definition(skill_id)
                skills.add_skill(skill.definition_id, base_value)

            elif skill_tags := entry.get("with_tags"):
                potential_skills = skill_library.get_definition_with_tags(skill_tags)

                if not potential_skills:
                    continue

                chosen_skill = rng.choice(potential_skills)

                skills.add_skill(chosen_skill.definition_id, base_value)

        return skills
