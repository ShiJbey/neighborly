class GameObject:

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name: str = name
