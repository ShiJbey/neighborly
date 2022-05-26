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


class ChildStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "child",
            "Character is seen as a child in the eyes of society",
        )


class AdolescentStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Teen",
            "Character is seen as an teen in the eyes of society",
        )


class YoungAdultStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Young Adult",
            "Character is seen as a young adult in the eyes of society",
        )


class AdultStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Adult",
            "Character is seen as an adult in the eyes of society",
        )


class ElderStatus(Status):
    def __init__(self) -> None:
        super().__init__(
            "Senior",
            "Character is seen as a senior in the eyes of society",
        )
