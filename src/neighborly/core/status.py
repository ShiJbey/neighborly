"""
status.py

Statuses represent temporary states of being for gameobjects. They are meant to
be paired with systems and updated every timestep and may be used to represent
temporary states like mood, unemployment, pregnancies, etc.
"""
from abc import ABC
from typing import Any, ClassVar, Dict, Iterator, Set, Type, TypeVar

from neighborly.core.ecs import Component, GameObject, ISerializable
from neighborly.core.time import SimDateTime


class StatusComponent(Component, ISerializable, ABC):
    """A component that tracks a temporary state of being for a GameObject."""

    is_persistent: ClassVar[bool] = False

    __slots__ = "created"

    created: SimDateTime
    """The date the status was created."""

    def __init__(self) -> None:
        super().__init__()
        self.created = SimDateTime(1, 1, 1)

    def set_created(self, timestamp: SimDateTime) -> None:
        """Set the creation timestamp.

        Parameters
        ----------
        timestamp
            The new timestamp.
        """
        self.created = timestamp.copy()

    def to_dict(self) -> Dict[str, Any]:
        return {"created": str(self.created)}

    def __str__(self) -> str:
        return f"Status::{self.__class__.__name__}"

    def __repr__(self) -> str:
        return "{}(created={})".format(self.__class__.__name__, self.created)


class StatusManager(Component, ISerializable):
    """Manages the state of statuses attached to the GameObject."""

    __slots__ = "_statuses"

    _statuses: Set[Type[StatusComponent]]
    """A set of status types attached to the GameObject."""

    def __init__(self) -> None:
        super().__init__()
        self._statuses = set()

    def add(self, status_type: Type[StatusComponent]) -> None:
        """Add a status type to the tracker.

        Parameters
        ----------
        status_type: Type[Component]
            The status type added to the GameObject
        """
        self._statuses.add(status_type)

    def remove(self, status_type: Type[StatusComponent]) -> None:
        """Remove a status type from the tracker

        Parameters
        ----------
        status_type: Type[Component]
            The status type to be removed from the GameObject
        """
        self._statuses.remove(status_type)

    def __contains__(self, item: Type[StatusComponent]) -> bool:
        """Check if a status type is attached to a GameObject"""
        return item in self._statuses

    def __iter__(self) -> Iterator[Type[StatusComponent]]:
        """Return iterator to active status types"""
        return self._statuses.__iter__()

    def __str__(self) -> str:
        return ", ".join([s.__name__ for s in self._statuses])

    def __repr__(self) -> str:
        return "{}({})".format(self.__class__.__name__, self._statuses)

    def to_dict(self) -> Dict[str, Any]:
        return {"statuses": [s.__name__ for s in self._statuses]}


_ST = TypeVar("_ST", bound=StatusComponent)


def add_status(gameobject: GameObject, status: StatusComponent) -> None:
    """
    Add a status to the given GameObject

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to add the status to
    status: Status
        The status to add
    """
    gameobject.get_component(StatusManager).add(type(status))
    status.set_created(gameobject.world.get_resource(SimDateTime))
    gameobject.add_component(status)


def get_status(gameobject: GameObject, status_type: Type[_ST]) -> _ST:
    """
    Get a status from the given GameObject

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to add the status to
    status_type: Type[Status]
        The type status of status to retrieve

    Returns
    -------
    Status
        The instance of the desired status type
    """
    return gameobject.get_component(status_type)


def remove_status(gameobject: GameObject, status_type: Type[StatusComponent]) -> None:
    """
    Remove a status from the given GameObject

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to add the status to
    status_type: Type[StatusComponentBase]
        The status type to remove
    """
    if has_status(gameobject, status_type):
        gameobject.remove_component(status_type)
        gameobject.get_component(StatusManager).remove(status_type)


def has_status(gameobject: GameObject, status_type: Type[StatusComponent]) -> bool:
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
    return status_type in gameobject.get_component(StatusManager)


def clear_statuses(gameobject: GameObject) -> None:
    """
    Remove all statuses from a GameObject

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to clear statuses from
    """
    status_tracker = gameobject.get_component(StatusManager)
    statuses_to_remove = list(status_tracker)

    for status_type in statuses_to_remove:
        if not status_type.is_persistent:
            remove_status(gameobject, status_type)
