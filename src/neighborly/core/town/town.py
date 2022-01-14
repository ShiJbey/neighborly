from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from neighborly.core import ecs_manager


@dataclass(frozen=True)
class TownConfig:
    """Configuration parameters for Town instance"""

    name: Optional[str] = None
    name_generator: str = "default_town_names"
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

        if config.name:
            town_name = config.name
        else:
            town_name = ecs_manager.get_name_generator(config.name_generator)()

        return cls(name=town_name)
