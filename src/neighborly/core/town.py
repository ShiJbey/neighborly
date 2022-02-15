from dataclasses import dataclass, field
from typing import Any, Dict

from neighborly.core.authoring import AbstractFactory
from neighborly.core.ecs import Component
from neighborly.core.name_generation import get_name


@dataclass(frozen=True)
class TownConfig:
    """Configuration parameters for Town instance"""

    name: str = "#town_name#"
    town_layout: str = "default"
    town_layout_options: Dict[str, Any] = field(default_factory=dict)


class Town(Component):
    """Simulated town where characters live"""

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    @classmethod
    def create(cls, config: TownConfig) -> "Town":
        """Create a town instance"""
        town_name = get_name(config.name)
        return cls(name=town_name)


class TownFactory(AbstractFactory):
    """Creates instances of Towns"""

    def __init__(self) -> None:
        super().__init__("Town")

    def create(self, params: Dict[str, Any]) -> Town:
        config = TownConfig(**params)
        town_name = get_name(config.name)
        return Town(name=town_name)
