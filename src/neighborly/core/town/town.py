class Town:
    """Simulated town where characters live"""

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name = name
