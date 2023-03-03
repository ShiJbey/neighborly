from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional, Union

from neighborly.core.ecs import GameObject, World
from neighborly.core.event import Event
from neighborly.core.roles import Role, RoleList
from neighborly.core.time import SimDateTime


class Action(Event, ABC):
    """User-facing class for implementing behaviors around actions"""

    initiator: str = ""
    base_priority: int = 1

    __slots__ = "_roles"

    def __init__(
        self,
        timestamp: SimDateTime,
        roles: Union[RoleList, Dict[str, GameObject]],
    ) -> None:
        """
        Parameters
        ----------
        timestamp: SimDateTime
            Timestamp for when this event
        roles: Dict[str, GameObject
            The names of roles mapped to GameObjects
        """
        super().__init__(timestamp)
        self._roles: RoleList = RoleList()

        if isinstance(roles, RoleList):
            self._roles = roles
        else:
            for role, gameobject in roles.items():
                self._roles.add_role(Role(role, gameobject))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this LifeEvent to a dictionary"""
        return {
            **super().to_dict(),
            "roles": [role.to_dict() for role in self._roles],
        }

    def iter_roles(self) -> Iterator[Role]:
        return self._roles.__iter__()

    def get_priority(self) -> float:
        """Get the probability of an instance of this event happening

        Returns
        -------
        float
            The probability of the event given the GameObjects bound
            to the roles in the LifeEventInstance
        """
        return self.base_priority

    @abstractmethod
    def execute(self) -> bool:
        """Executes the LifeEvent instance, emitting an event"""
        raise NotImplementedError

    def is_valid(self, world: World) -> bool:
        """Check that all gameobjects still meet the preconditions for their roles"""
        return self.instantiate(world, bindings=self._roles) is not None

    def get_initiator(self) -> GameObject:
        return self._roles[self.initiator]

    def __getitem__(self, role_name: str) -> GameObject:
        return self._roles[role_name]

    def __repr__(self) -> str:
        return "{}(timestamp={}, roles=[{}])".format(
            self.get_type(), str(self.get_timestamp()), self._roles
        )

    def __str__(self) -> str:
        return "{} [at {}] : {}".format(
            self.get_type(),
            str(self.get_timestamp()),
            ", ".join([str(role) for role in self._roles]),
        )

    @classmethod
    @abstractmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[Action]:
        """Attempts to create a new LifeEvent instance

        Parameters
        ----------
        world: World
            Neighborly world instance
        bindings: Dict[str, GameObject], optional
            Suggested bindings of role names mapped to GameObjects

        Returns
        -------
        Optional[LifeEventInstance]
            An instance of this life event if all roles are bound successfully
        """
        raise NotImplementedError
