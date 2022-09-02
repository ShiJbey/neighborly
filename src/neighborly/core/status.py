from abc import ABC

from neighborly.core.ecs import Component


class Status(Component, ABC):
    """
    A temporary or permanent status applied to a GameObject

    Attributes
    ----------
    name: str
        Name of the status
    description: str
        Brief description of what the status does
    """

    __slots__ = "_name", "_description"

    def __init__(self, name: str, description: str) -> None:
        super().__init__()
        self._name: str = name
        self._description: str = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def __repr__(self) -> str:
        return f"{self.name}({self.gameobject.id})"
