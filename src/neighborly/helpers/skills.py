"""Skill System Helper Functions.

"""

from neighborly.components.skills import Skill, SkillInstance, Skills
from neighborly.ecs import GameObject
from neighborly.libraries import SkillLibrary


def add_skill(gameobject: GameObject, skill_id: str, base_value: float = 0.0) -> None:
    """Add a new skill to a character with the given base value.

    Parameters
    ----------
    gameobject
        The character to add the skill to.
    skill_id
        The definition ID of the skill to add.
    base_value
        The base value of the skill when added.
    """
    library = gameobject.world.resources.get_resource(SkillLibrary)
    skill = library.get_skill(skill_id).get_component(Skill)
    gameobject.get_component(Skills).add_skill(skill, base_value)


def has_skill(gameobject: GameObject, skill_id: str) -> bool:
    """Check if a character has a skill.

    Parameters
    ----------
    gameobject
        The character to check.
    skill_id
        The ID of the skill to check for.

    Returns
    -------
    bool
        True if the character has the skill, False otherwise.
    """
    return gameobject.get_component(Skills).has_skill(skill_id)


def get_skill(gameobject: GameObject, skill_id: str) -> SkillInstance:
    """Get a character's skill stat.

    Parameters
    ----------
    gameobject
        The character to check.
    skill_id
        The ID of the skill to retrieve.

    Returns
    -------
    Stat
        The stat associated with this skill.
    """
    return gameobject.get_component(Skills).get_skill(skill_id)
