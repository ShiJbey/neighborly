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

    __slots__ = "name", "description"

    def __init__(self, name: str, description: str) -> None:
        super().__init__()
        self.name: str = name
        self.description: str = description
