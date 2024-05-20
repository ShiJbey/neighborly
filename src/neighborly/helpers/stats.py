"""Helper functions for modifying GameObject Stats.

"""

from __future__ import annotations

from neighborly.components.stats import Stat, Stats
from neighborly.ecs import GameObject


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
