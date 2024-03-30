"""Helper functions for modifying GameObject Stats.

"""

from __future__ import annotations

from typing import Optional

from neighborly.components.stats import Stat, Stats
from neighborly.ecs import GameObject


def add_stat(
    gameobject: GameObject,
    stat_id: str,
    base_value: float,
    bounds: Optional[tuple[float, float]] = None,
    is_discrete: bool = False,
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
    return gameobject.get_component(Stats).add_stat(
        stat_id, base_value=base_value, bounds=bounds, is_discrete=is_discrete
    )


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
