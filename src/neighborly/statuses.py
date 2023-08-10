"""Neighborly's Status System

Statuses are components added GameObjects and represent temporary states like mood, 
unemployment, pregnancies, etc. Statuses are components. So, they can be queried in
system operations using world.get_components(...)'. We keep track of all the statuses
currently applied to a character using the 'Statuses' component.

"""

from __future__ import annotations

from abc import ABC
from typing import Any, ClassVar, Dict, Iterator

from ordered_set import OrderedSet

from neighborly.ecs import Component, ISerializable


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

    def on_add(self) -> None:
        self.gameobject.get_component(Statuses).add_status(self)

    def on_remove(self) -> None:
        self.gameobject.get_component(Statuses).remove_status(self)

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

    def clear(self) -> None:
        """Remove all non persistent statuses."""
        for status in reversed(self._statuses):
            if status.is_persistent is False:
                self.gameobject.remove_component(type(status))
                self.remove_status(status)

    def __str__(self) -> str:
        return ", ".join([type(s).__name__ for s in self._statuses])

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__, [type(s).__name__ for s in self._statuses]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"statuses": [type(s).__name__ for s in self._statuses]}
