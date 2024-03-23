"""Skill System Helper Functions.

"""

from neighborly.components.skills import SkillEntry, Skills
from neighborly.components.stats import StatModifier
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

    if skill_id not in library.definitions:
        raise KeyError(f"No skill found: {skill_id!r}")

    gameobject.get_component(Skills).entries.append(
        SkillEntry(name=skill_id, base_value=base_value, is_discrete=True)
    )


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
    skill_entries = gameobject.get_component(Skills).entries

    for entry in skill_entries:
        if entry.name == skill_id:
            return True

    return False


def get_skill(gameobject: GameObject, skill_id: str) -> SkillEntry:
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
    skill_entries = gameobject.get_component(Skills).entries

    for entry in skill_entries:
        if entry.name == skill_id:
            return entry

    raise KeyError(f"Could not find skill: {skill_id!r}")


def add_skill_modifier(
    gameobject: GameObject, name: str, modifier: StatModifier
) -> None:
    """Add a modifier to a stat."""

    raise NotImplementedError()


def remove_skill_modifiers_from_source(
    gameobject: GameObject, name: str, source: object
) -> None:
    """Remove all stat modifiers from a given source."""

    raise NotImplementedError()
