from dataclasses import dataclass, field
from typing import Any, Dict

from neighborly.core.name_generation import get_name


@dataclass(frozen=True)
class TownConfig:
    """Configuration parameters for Town instance"""

    name: str = "#town_names#"
    town_layout: str = "default"
    town_layout_options: Dict[str, Any] = field(default_factory=dict)


class Town:
    """Simulated town where characters live"""

    __slots__ = "name"

    def __init__(self, name: str) -> None:
        self.name = name

    @classmethod
    def create(cls, config: TownConfig) -> "Town":
        """Create a town instance"""
        town_name = get_name(config.name)
        return cls(name=town_name)
