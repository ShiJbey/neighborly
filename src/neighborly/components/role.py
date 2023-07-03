"""Components for defining role GameObjects.

"""
from __future__ import annotations

from typing import Any, Dict, Type, List

from ordered_set import OrderedSet

from neighborly import Component, GameObject
from neighborly.core.ecs import ISerializable, TagComponent


class RoleTracker(Component, ISerializable):
    """Tracks the roles currently held by this character."""

    __slots__ = "_roles"

    _roles: OrderedSet[GameObject]
    """References to the role GameObjects."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._roles = OrderedSet([])

    @property
    def roles(self) -> OrderedSet[GameObject]:
        return self._roles

    def to_dict(self) -> Dict[str, Any]:
        return {"roles": [role.uid for role in self.roles]}


class IsRole(TagComponent):
    """Tags a GameObject as tracking information about a role."""

    pass


def get_roles_with_components(
    gameobject: GameObject, *component_types: Type[Component]
) -> List[GameObject]:
    """Get all role associated with a GameObject that have specific components.

    Parameters
    ----------
    gameobject
        The GameObject to search on
    *component_types
        The component classes to check for

    Returns
    -------
    List[GameObject]
        Matching role GameObjects
    """
    matches: List[GameObject] = []

    for role in gameobject.get_component(RoleTracker).roles:
        if role.has_components(*component_types):
            matches.append(role)

    return matches


def add_role(gameobject: GameObject, role: GameObject) -> None:
    """Add a role to a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the role to.
    role
        The role to add.
    """
    gameobject.get_component(RoleTracker).roles.add(role)
    gameobject.add_child(role)


def remove_role(gameobject: GameObject, role: GameObject) -> None:
    """Remove a role from a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to remove the role from.
    role
        The role to add.
    """
    gameobject.get_component(RoleTracker).roles.remove(role)
    gameobject.remove_child(role)
