from typing import Callable, Dict


class Town:
    """Simulated town where characters live"""

    __slots__ = "name"

    _name_factories: Dict[str, Callable[..., str]] = {}

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def register_name_factory(cls, name: str, factory: Callable[..., str]) -> None:
        """Register a name factory that creates instances of Town names"""
        cls._name_factories[name] = factory
