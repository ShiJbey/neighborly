"""Skill System Helper Functions.

"""

from neighborly.components.skills import Skills
from neighborly.components.stats import Stat
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
    library = gameobject.world.resource_manager.get_resource(SkillLibrary)
    skill = library.get_definition(skill_id)
    gameobject.get_component(Skills).add_skill(skill.definition_id, base_value)


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
    return skill_id in gameobject.get_component(Skills).skills


def get_skill(gameobject: GameObject, skill_id: str) -> Stat:
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
    return gameobject.get_component(Skills).skills[skill_id]
