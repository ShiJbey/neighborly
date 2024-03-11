"""Neighborly ECS System.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator, Optional, Type, TypeVar

from neighborly.ecs.errors import SystemNotFoundError

if TYPE_CHECKING:
    from neighborly.ecs.world import World


_ST = TypeVar("_ST", bound="System")


class ISystem(ABC):
    """Abstract Interface for ECS systems."""

    @abstractmethod
    def set_active(self, value: bool) -> None:
        """Toggle if this system is active and will update.

        Parameters
        ----------
        value
            The new active status.
        """
        raise NotImplementedError

    @abstractmethod
    def on_add(self, world: World) -> None:
        """Lifecycle method called when the system is added to the world.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def on_start_running(self, world: World) -> None:
        """Lifecycle method called before checking if a system will update.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def on_destroy(self, world: World) -> None:
        """Lifecycle method called when a system is removed from the world.

        Parameters
        ----------
        world
            The world instance the system was removed from.
        """
        raise NotImplementedError

    @abstractmethod
    def on_update(self, world: World) -> None:
        """Lifecycle method called each when stepping the simulation.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        raise NotImplementedError

    @abstractmethod
    def on_stop_running(self, world: World) -> None:
        """Lifecycle method called after a system updates.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        raise NotImplementedError

    @abstractmethod
    def should_run_system(self, world: World) -> bool:
        """Checks if this system should run this simulation step."""
        raise NotImplementedError


class System(ISystem, ABC):
    """Base class for systems, providing implementation for most lifecycle methods."""

    __slots__ = ("_active",)

    _active: bool
    """Will this system update during the next simulation step."""

    def __init__(self) -> None:
        super().__init__()
        self._active = True

    def set_active(self, value: bool) -> None:
        """Toggle if this system is active and will update.

        Parameters
        ----------
        value
            The new active status.
        """
        self._active = value

    def on_add(self, world: World) -> None:
        """Lifecycle method called when the system is added to the world.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def on_start_running(self, world: World) -> None:
        """Lifecycle method called before checking if a system will update.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def on_destroy(self, world: World) -> None:
        """Lifecycle method called when a system is removed from the world.

        Parameters
        ----------
        world
            The world instance the system was removed from.
        """
        return

    def on_stop_running(self, world: World) -> None:
        """Lifecycle method called after a system updates.

        Parameters
        ----------
        world
            The world instance the system is mounted to.
        """
        return

    def should_run_system(self, world: World) -> bool:
        """Checks if this system should run this simulation step."""
        return self._active


class SystemGroup(System, ABC):
    """A group of ECS systems that run as a unit.

    SystemGroups allow users to better structure the execution order of their systems.
    """

    __slots__ = ("_children",)

    _children: list[tuple[int, System]]
    """The systems that belong to this group"""

    def __init__(self) -> None:
        super().__init__()
        self._children = []

    def set_active(self, value: bool) -> None:
        super().set_active(value)
        for _, child in self._children:
            child.set_active(value)

    def iter_children(self) -> Iterator[tuple[int, System]]:
        """Get an iterator for the group's children.

        Returns
        -------
        Iterator[tuple[SystemBase]]
            An iterator for the child system collection.
        """
        return iter(self._children)

    def add_child(self, system: System, priority: int = 0) -> None:
        """Add a new system as a sub_system of this group.

        Parameters
        ----------
        system
            The system to add to this group.
        priority
            The priority of running this system relative to its siblings.
        """
        self._children.append((priority, system))
        self._children.sort(key=lambda pair: pair[0], reverse=True)

    def remove_child(self, system_type: Type[System]) -> None:
        """Remove a child system.

        If for some reason there are more than one instance of the given system type,
        this method will remove the first instance it finds.

        Parameters
        ----------
        system_type
            The class type of the system to remove.
        """
        children_to_remove = [
            pair for pair in self._children if isinstance(pair[1], system_type)
        ]

        if children_to_remove:
            self._children.remove(children_to_remove[0])

    def on_update(self, world: World) -> None:
        """Run all sub-systems.

        Parameters
        ----------
        world
            The world instance the system is updating
        """
        for _, child in self._children:
            child.on_start_running(world)
            if child.should_run_system(world):
                child.on_update(world)
            child.on_stop_running(world)


class SystemManager(SystemGroup):
    """Manages system instances for a single world instance."""

    __slots__ = ("_world",)

    _world: World
    """The world instance associated with the SystemManager."""

    def __init__(self, world: World) -> None:
        super().__init__()
        self._world = world

    def add_system(
        self,
        system: System,
        priority: int = 0,
        system_group: Optional[Type[SystemGroup]] = None,
    ) -> None:
        """Add a System instance.

        Parameters
        ----------
        system
            The system to add.
        priority
            The priority of the system relative to the others in its system group.
        system_group
            The class of the group to add this system to
        """

        if system_group is None:
            self.add_child(system, priority)
            return

        stack = [child for _, child in self._children]

        while stack:
            current_sys = stack.pop()

            if isinstance(current_sys, system_group):
                current_sys.add_child(system)
                system.on_add(self._world)
                return

            if isinstance(current_sys, SystemGroup):
                for _, child in current_sys.iter_children():
                    stack.append(child)

        raise SystemNotFoundError(system_group.__name__)

    def get_system(self, system_type: Type[_ST]) -> _ST:
        """Attempt to get a System of the given type.

        Parameters
        ----------
        system_type
            The type of the system to retrieve.

        Returns
        -------
        _ST or None
            The system instance if one is found.
        """
        stack: list[tuple[SystemGroup, System]] = [
            (self, child) for _, child in self._children
        ]

        while stack:
            _, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                return current_sys

            if isinstance(current_sys, SystemGroup):
                for _, child in current_sys.iter_children():
                    stack.append((current_sys, child))

        raise SystemNotFoundError(system_type.__name__)

    def remove_system(self, system_type: Type[System]) -> None:
        """Remove all instances of a system type.

        Parameters
        ----------
        system_type
            The type of the system to remove.

        Notes
        -----
        This function performs a Depth-first search through
        the tree of system groups to find the one with the
        matching type.

        No exception is raised if it does not find a matching
        system.
        """

        stack: list[tuple[SystemGroup, System]] = [
            (self, c) for _, c in self.iter_children()
        ]

        while stack:
            group, current_sys = stack.pop()

            if isinstance(current_sys, system_type):
                group.remove_child(system_type)
                current_sys.on_destroy(self._world)

            else:
                if isinstance(current_sys, SystemGroup):
                    for _, child in current_sys.iter_children():
                        stack.append((current_sys, child))

    def update_systems(self) -> None:
        """Update all systems in the manager."""
        self.on_update(self._world)
