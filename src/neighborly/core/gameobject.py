class GameObject:

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name: str = name

    def __repr__(self) -> str:
        return "{}(name={})".format(
            self.__class__.__name__,
            self.name
        )
