"""Components for defining role GameObjects.

"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Type, TypeVar

from ordered_set import OrderedSet

from neighborly import Component, GameObject
from neighborly.core.ecs import ISerializable

_RT = TypeVar("_RT", bound=Component)


class Roles(Component, ISerializable):
    """Tracks the roles currently held by this character."""

    __slots__ = "_roles"

    _roles: OrderedSet[Component]
    """References to the role components."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._roles = OrderedSet([])

    @property
    def roles(self) -> Iterable[Component]:
        return self._roles

    def add_role(self, role: Component) -> None:
        self._roles.add(role)

    def remove_role(self, role: Component) -> None:
        self._roles.remove(role)

    def to_dict(self) -> Dict[str, Any]:
        return {"roles": [type(role).__name__ for role in self.roles]}

    def get_roles_of_type(self, role_type: Type[_RT]) -> List[_RT]:
        """Get all roles that are an instance or derived instance of the given type."""
        return [role for role in self._roles if isinstance(role, role_type)]

    def __repr__(self) -> str:
        return "{}({})".format(
            type(self).__name__,
            [type(r).__name__ for r in self._roles]
        )


def add_role(gameobject: GameObject, role: Component) -> None:
    """Add a role to a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the role to.
    role
        The role to add.
    """
    gameobject.get_component(Roles).add_role(role)
    gameobject.add_component(role)


def remove_role(gameobject: GameObject, role_type: Type[Component]) -> None:
    """Remove a role from a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to remove the role from.
    role_type
        The role to remove.
    """
    if role := gameobject.try_component(role_type):
        gameobject.get_component(Roles).remove_role(role)
        gameobject.remove_component(role_type)
