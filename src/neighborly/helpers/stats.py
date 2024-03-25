"""Helper functions for modifying GameObject Stats.

"""

from __future__ import annotations

from neighborly.components.stats import Stat, Stats
from neighborly.ecs import GameObject


def add_stat(
    gameobject: GameObject,
    stat_id: str,
    stat: Stat,
) -> Stat:
    """Add a new stat to the gameobject.

    Parameters
    ----------
    gameobject
        The GameObject to add a stat to.
    stat_id
        The ID to associate the stat with.
    stat
        The stat instance to add.

    Returns
    -------
    Stat
        The newly created stat.
    """
    gameobject.get_component(Stats).add_stat(stat_id, stat)

    gameobject.world.rp_db.insert(f"{gameobject.uid}.stats.{stat_id}!{stat.value}")

    return stat


def has_stat(gameobject: GameObject, stat_id: str) -> bool:
    """Check if a GameObject has a stat.

    Parameters
    ----------
    gameobject
        The GameObject to check.
    stat_id
        The definition ID of a stat to check for.

    Returns
    -------
    bool
        True if the GameObject has the stat. False otherwise.
    """
    return gameobject.get_component(Stats).has_stat(stat_id)


def get_stat(gameobject: GameObject, stat_id: str) -> Stat:
    """Get a GameObject's stat.

    Parameters
    ----------
    gameobject
        A GameObject.
    stat_id
        The definition ID of a stat to retrieve.

    Returns
    -------
    Stat
        The stat.
    """
    return gameobject.get_component(Stats).get_stat(stat_id)


def remove_stat(gameobject: GameObject, stat_id: str) -> bool:
    """Remove a stat from a GameObject.

    Parameters
    ----------
    gameobject
        A GameObject.
    stat_id
        The definition ID of a stat to remove.

    Returns
    -------
    bool
        True if the stat was removed successfully. False otherwise.
    """
    if gameobject.get_component(Stats).remove_stat(stat_id):

        gameobject.world.rp_db.delete(f"{gameobject.uid}.stats.{stat_id}")

        return True

    return False
