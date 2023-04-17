from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Optional

from neighborly.core.ecs import GameObject


class Role:
    """A role that a GameObject plays in a life event or action"""

    __slots__ = "_name", "_gameobject"

    def __init__(self, name: str, gameobject: GameObject) -> None:
        """
        Parameters
        ----------
        name : str
            The name of the role
        gameobject : GameObject
            The GameObject bound to this role
        """
        self._name: str = name
        self._gameobject: GameObject = gameobject

    @property
    def name(self) -> str:
        """Get the name of the role"""
        return self._name

    @property
    def gameobject(self) -> GameObject:
        """Get the GameObject bound to the role"""
        return self._gameobject

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "gameobject": self.gameobject.uid}

    def __str__(self) -> str:
        return f"({self.name}: {self.gameobject})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, gid={self.gameobject})"


class RoleList:
    """A collection of Roles"""

    __slots__ = "_roles", "_sorted_roles"

    def __init__(self, roles: Optional[Iterable[Role]] = None) -> None:
        """
        Parameters
        ----------
        roles
            Roles to instantiate the list with, by default None
        """
        self._roles: List[Role] = []
        self._sorted_roles: Dict[str, List[Role]] = {}

        if roles:
            for role in roles:
                self.add_role(role)

    def add_role(self, role: Role) -> None:
        """Add role to the list"""
        self._roles.append(role)
        if role.name not in self._sorted_roles:
            self._sorted_roles[role.name] = []
        self._sorted_roles[role.name].append(role)

    def get_all(self, role_name: str) -> List[GameObject]:
        """Return all GameObjects bound to the given role name"""
        return [role.gameobject for role in self._sorted_roles[role_name]]

    def get(self, role_name: str) -> Optional[GameObject]:
        """
        Get the GameObject bound to the role name

        Parameters
        ----------
        role_name : str
            The name of the role to get from the list

        Returns
        -------
        GameObject or None
            The bound GameObject or None if no role exists
        """
        if role_name in self._sorted_roles:
            return self._sorted_roles[role_name][0].gameobject
        return None

    def __len__(self) -> int:
        return len(self._roles)

    def __bool__(self) -> int:
        return bool(self._roles)

    def __getitem__(self, role_name: str) -> GameObject:
        return self._sorted_roles[role_name][0].gameobject

    def __iter__(self) -> Iterator[Role]:
        return self._roles.__iter__()

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return "[{}]".format(", ".join([str(role) for role in self._roles]))
