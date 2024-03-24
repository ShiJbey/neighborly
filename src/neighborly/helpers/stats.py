"""Helper functions for modifying GameObject Stats.

"""

from __future__ import annotations

from neighborly.components.stats import Stat, StatModifier
from neighborly.ecs import GameObject


def add_stat(
    gameobject: GameObject,
    stat: Stat,
) -> Stat:
    """Add a new stat to the gameobject.

    Parameters
    ----------
    gameobject
        The GameObject to add a stat to.
    stat
        The stat to add.

    Returns
    -------
    Stat
        The newly created stat.
    """
    gameobject.world.session.add(stat)
    gameobject.world.session.flush()

    return stat


def has_stat(gameobject: GameObject, name: str) -> bool:
    """Check if a GameObject has a stat.

    Parameters
    ----------
    gameobject
        The GameObject to check.
    name
        The name of a stat to check for.

    Returns
    -------
    bool
        True if the GameObject has the stat. False otherwise.
    """
    gameobject.world.session.query()


def get_stat(gameobject: GameObject, name: str) -> Stat:
    """Get a GameObject's stat.

    Parameters
    ----------
    gameobject
        A GameObject.
    name
        The name of a stat to retrieve.

    Returns
    -------
    Stat
        The stat.
    """
    stats = gameobject.get_component(Stats)
    for entry in stats.entries:
        if entry.name == name:
            return entry

    raise KeyError(f"No stat with name: {name!r}")


def add_stat_modifier(
    gameobject: GameObject, name: str, modifier: StatModifier
) -> None:
    """Add a modifier to a stat."""

    raise NotImplementedError()


def remove_stat_modifiers_from_source(
    gameobject: GameObject, name: str, source: object
) -> None:
    """Remove all stat modifiers from a given source."""

    raise NotImplementedError()
