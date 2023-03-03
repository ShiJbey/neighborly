from typing import Type, TypeVar

from neighborly.core.ecs import GameObject
from neighborly.core.status import StatusComponent, StatusManager
from neighborly.core.time import SimDateTime

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
    """
    Check for a status of a given type

    Parameters
    ----------
    gameobject: GameObject
        The GameObject to add the status to
    status_type: Type[Status]
        The status type to remove

    Returns
    -------
    bool
        Return True if the GameObject has a status
        of the given type
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
    statuses_to_remove = status_tracker.get_all()

    for status_type in statuses_to_remove:
        if not status_type.is_persistent:
            remove_status(gameobject, status_type)
