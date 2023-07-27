"""Neighborly's Status System

Statuses are components added GameObjects and represent temporary states like mood, 
unemployment, pregnancies, etc. Since, statuses are components so they can be queried in
system operations using world.get_components(...)'. We keep track of all the statuses
currently applied to a character using the 'Statuses' component.

"""

from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Dict, Iterator

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, GameObject, ISerializable


class IStatus(Component, ISerializable, ABC):
    """A component that tracks a temporary state of being for a GameObject."""

    __slots__ = "timestamp"

    timestamp: int
    """The year the status was created."""

    is_persistent: ClassVar[bool] = False
    """If this status type persists even when a GameObject is no longer active."""

    def __init__(self, timestamp: int) -> None:
        super().__init__()
        self.timestamp = timestamp

    def on_add(self, gameobject: GameObject) -> None:
        gameobject.get_component(Statuses).add_status(self)

    def on_remove(self, gameobject: GameObject) -> None:
        gameobject.get_component(Statuses).remove_status(self)

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": str(self.timestamp)}

    def __str__(self) -> str:
        return "{}(year_created={})".format(self.__class__.__name__, self.timestamp)

    def __repr__(self) -> str:
        return "{}(year_created={})".format(self.__class__.__name__, self.timestamp)


class Statuses(Component, ISerializable):
    """Tracks statuses attached to the GameObject."""

    __slots__ = "_statuses"

    _statuses: OrderedSet[IStatus]
    """A set of statuses attached to the GameObject."""

    def __init__(self) -> None:
        super().__init__()
        self._statuses = OrderedSet([])

    def add_status(self, status: IStatus) -> None:
        """Add a status to the tracker.

        Parameters
        ----------
        status
            The status added to the GameObject.
        """
        self._statuses.add(status)

    def remove_status(self, status: IStatus) -> bool:
        """Remove a status from the tracker.

        Parameters
        ----------
        status
            The status to be removed from the GameObject.

        Returns
        -------
        bool
            Returns True if the trait was removed, False otherwise.
        """
        try:
            self._statuses.remove(status)
            return True
        except ValueError:
            return False

    def iter_statuses(self) -> Iterator[IStatus]:
        """Return iterator to active status types"""
        return self._statuses.__iter__()

    def __str__(self) -> str:
        return ", ".join([type(s).__name__ for s in self._statuses])

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, [type(s).__name__ for s in self._statuses]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"statuses": [type(s).__name__ for s in self._statuses]}


def clear_statuses(gameobject: GameObject, clear_persistent: bool = False) -> bool:
    """Remove all statuses from a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to clear statuses from
    clear_persistent
        Should persistent statuses be cleared too (defaults to False)

    Returns
    -------
    bool
        Returns True if all statuses were removed successfully, False otherwise
    """
    statuses = gameobject.get_component(Statuses)
    successful = True
    for status in list(statuses.iter_statuses()):
        if clear_persistent or status.is_persistent is False:
            successful = gameobject.remove_component(type(status))
    return successful
