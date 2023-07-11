"""
trait.py

Statuses represent temporary states of being for game objects. They are meant to
be paired with systems and updated every time step and may be used to represent
temporary states like mood, unemployment, pregnancies, etc.

"""

from abc import ABC
from typing import Any, ClassVar, Dict, Iterator, Type, TypeVar

from ordered_set import OrderedSet

from neighborly.core.ecs import Component, GameObject, ISerializable


class IStatus(Component, ISerializable, ABC):
    """A component that tracks a temporary state of being for a GameObject."""

    __slots__ = "year_created"

    year_created: int
    """The year the status was created."""

    is_persistent: ClassVar[bool] = False
    """If this status type persists even when a GameObject is no longer active."""

    def __init__(self, year_created: int) -> None:
        super().__init__()
        self.year_created = year_created

    def to_dict(self) -> Dict[str, Any]:
        return {"year_created": str(self.year_created)}

    def __str__(self) -> str:
        return "{}(year_created={})".format(self.__class__.__name__, self.year_created)

    def __repr__(self) -> str:
        return "{}(year_created={})".format(self.__class__.__name__, self.year_created)


class Statuses(Component, ISerializable):
    """Manages the state of statuses attached to the GameObject."""

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

    def remove_status(self, status: IStatus) -> None:
        """Remove a status from the tracker.

        Parameters
        ----------
        status
            The status to be removed from the GameObject.
        """
        self._statuses.remove(status)

    def has_status(self, status: IStatus) -> bool:
        """Check if a status is attached to a GameObject"""
        return status in self._statuses

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


_ST = TypeVar("_ST", bound=IStatus)


def add_status(gameobject: GameObject, status: IStatus) -> None:
    """Add a status to the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the status to.
    status
        The status to add.
    """
    gameobject.get_component(Statuses).add_status(status)
    gameobject.add_component(status)


def get_status(gameobject: GameObject, status_type: Type[_ST]) -> _ST:
    """Get a status from the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the status to.
    status_type
        The type status of status to retrieve.

    Returns
    -------
    Status
        The instance of the desired status type.
    """
    return gameobject.get_component(status_type)


def remove_status(gameobject: GameObject, status_type: Type[IStatus]) -> None:
    """Remove a status from the given GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the status to.
    status_type
        The status type to remove.
    """
    if status := gameobject.try_component(status_type):
        gameobject.get_component(Statuses).remove_status(status)
        gameobject.remove_component(status_type)


def has_status(gameobject: GameObject, status_type: Type[IStatus]) -> bool:
    """Check for a status of a given type.

    Parameters
    ----------
    gameobject
        The GameObject to add the status to.
    status_type
        The status type to remove.

    Returns
    -------
    bool
        True if the GameObject has a status of the given type, False otherwise.
    """
    return gameobject.has_component(status_type)


def clear_statuses(gameobject: GameObject) -> None:
    """Remove all statuses from a GameObject.

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to clear statuses from
    """
    status_manager = gameobject.get_component(Statuses)
    statuses_to_remove = list(status_manager.iter_statuses())

    for status in statuses_to_remove:
        if not status.is_persistent:
            remove_status(gameobject, type(status))
