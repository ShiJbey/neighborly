"""Neighborly's Role System.

Roles describe positions that characters hold in the simulation. Occupations are the 
most common type of role. Other roles might be things like being Spider-Man or
the Avatar.

"""

from __future__ import annotations

from abc import ABC
from typing import Any, Dict, Iterable, List, Type, TypeVar

from ordered_set import OrderedSet

from neighborly.ecs import Component, ISerializable


class IRole(Component, ABC):
    """An abstract base class for components representing character roles."""

    def on_add(self) -> None:
        self.gameobject.get_component(Roles).add_role(self)

    def on_remove(self) -> None:
        self.gameobject.get_component(Roles).remove_role(self)


_RT = TypeVar("_RT", bound=IRole)


class Roles(Component, ISerializable):
    """Tracks the roles currently held by this character."""

    __slots__ = "_roles"

    _roles: OrderedSet[IRole]
    """References to the role components."""

    def __init__(self) -> None:
        super().__init__()
        self._roles = OrderedSet([])

    @property
    def roles(self) -> Iterable[IRole]:
        return self._roles

    def add_role(self, role: IRole) -> None:
        self._roles.add(role)

    def remove_role(self, role: IRole) -> None:
        self._roles.remove(role)

    def to_dict(self) -> Dict[str, Any]:
        return {"roles": [type(role).__name__ for role in self.roles]}

    def get_roles_of_type(self, role_type: Type[_RT]) -> List[_RT]:
        """Get all roles that are an instance or derived instance of the given type."""
        return [role for role in self._roles if isinstance(role, role_type)]

    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__, [type(r).__name__ for r in self._roles]
        )
