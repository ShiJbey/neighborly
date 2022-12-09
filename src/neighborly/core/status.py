"""
Statuses are temporary conditions attributed to
GameObjects. They are stored within the ECS
hierarchy as children to their associated GameObject.
"""

from abc import ABC, abstractmethod
from typing import Callable, Dict, Optional, Type, TypeVar

from neighborly.core.ecs import Component, GameObject, World


class Status(Component):
    """Tags a GameObject as being a status and holds callback functions"""

    def __init__(
        self,
        is_expired: Callable[[World, GameObject], bool],
        on_update: Optional[Callable[[World, GameObject, int], None]] = None,
        on_expire: Optional[Callable[[World, GameObject], None]] = None,
    ) -> None:
        super().__init__()
        self.is_expired: Callable[[World, GameObject], bool] = is_expired
        self.on_update: Optional[Callable[[World, GameObject, int], None]] = on_update
        self.on_expire: Optional[Callable[[World, GameObject], None]] = on_expire


class StatusType(Component):
    """Empty base class for status-related components"""

    @staticmethod
    @abstractmethod
    def is_expired(world: World, status: GameObject) -> bool:
        raise NotImplementedError


class IOnUpdate(ABC):
    @staticmethod
    @abstractmethod
    def on_update(world: World, status: GameObject, elapsed_hours: int) -> None:
        raise NotImplementedError


class IOnExpire(ABC):
    @staticmethod
    @abstractmethod
    def on_expire(world: World, status: GameObject) -> None:
        raise NotImplementedError


_ST = TypeVar("_ST", bound=StatusType)


class StatusManager(Component):
    """
    Helper component that tracks what statuses
    are attached to a GameObject

    Attributes
    ----------
    status_types: Dict[int, Type[StatusType]]
        List of the StatusTypes attached to the GameObject
    """

    __slots__ = "status_types"

    def __init__(self) -> None:
        super().__init__()
        self.status_types: Dict[int, Type[StatusType]] = {}

    def add(self, status_id: int, status_type: Type[StatusType]) -> None:
        self.status_types[status_id] = status_type

    def remove(self, status_id: int) -> None:
        """Removes record of status with the given ID"""
        del self.status_types[status_id]

    def remove_type(self, status_type: Type[StatusType]) -> None:
        status_to_remove: Optional[int] = None

        for s_id, s_type in self.status_types.items():
            if s_type == status_type:
                status_to_remove = s_id
                break

        if status_to_remove is not None:
            self.remove(status_to_remove)

    def __contains__(self, item: Type[StatusType]) -> bool:
        return item in self.status_types.values()


def add_status(world: World, gameobject: GameObject, status_type: StatusType) -> None:
    """Adds a new status to the given GameObject"""

    status_component = Status(is_expired=status_type.is_expired)

    if isinstance(status_type, IOnUpdate):
        status_component.on_update = status_type.on_update

    if isinstance(status_type, IOnExpire):
        status_component.on_expire = status_type.on_expire

    status = world.spawn_gameobject([status_component, status_type])
    gameobject.add_child(status)

    if not gameobject.has_component(StatusManager):
        gameobject.add_component(StatusManager())

    gameobject.get_component(StatusManager).add(status.id, type(status_type))


def get_status(gameobject: GameObject, status_type_type: Type[_ST]) -> _ST:
    return gameobject.get_component_in_child(status_type_type)[1]


def remove_status(gameobject: GameObject, status: GameObject) -> None:
    """Removes a status from the given GameObject"""
    gameobject.remove_child(status)
    if status_manager := gameobject.try_component(StatusManager):
        status_manager.remove(status.id)
    status.destroy()


def has_status(gameobject: GameObject, status_type: Type[StatusType]) -> bool:
    """Return True if the given gameobject has a status of the given type"""
    if status_manager := gameobject.try_component(StatusManager):
        return status_type in status_manager
    else:
        return any(c.has_component(status_type) for c in gameobject.children)
