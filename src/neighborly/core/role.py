from __future__ import annotations

from abc import abstractmethod
from typing import Optional, Protocol

from neighborly import GameObject, World
from neighborly.core.event import Event, EventRole


class IRoleType(Protocol):
    """
    Interface for defining roles that GameObjects can be bound to when executing life
    events
    """

    @abstractmethod
    def fill_role(
        self, world: World, event: Event, candidate: Optional[GameObject] = None
    ) -> Optional[EventRole]:
        """
        Attempt to bind a role to a GameObject

        Parameters
        ----------
        world: World
            Current World instance

        event: Event
            The event that we are binding a role for

        candidate: Optional[GameObject] (optional)
            ID of the GameObject we want to bind this role to.
            If not specified, the role will search for a Gameobject that matches

        Returns
        -------
        Optional[EventRole]
        """
        raise NotImplementedError


class RoleBinderFn(Protocol):
    """Callable that returns a GameObject that meets requirements for a given Role"""

    def __call__(
        self, world: World, event: Event, candidate: Optional[GameObject] = None
    ) -> Optional[GameObject]:
        raise NotImplementedError


class RoleFilterFn(Protocol):
    """Function that filters GameObjects for an EventRole"""

    def __call__(self, world: World, gameobject: GameObject) -> bool:
        raise NotImplementedError
