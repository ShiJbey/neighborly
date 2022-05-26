from dataclasses import dataclass
from typing import Any, Dict

from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentDefinition


@dataclass
class Position2D(Component):
    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "x": self.x, "y": self.y}


class Position2DFactory(AbstractFactory):
    def __init__(self):
        super().__init__("Position2D")

    def create(self, spec: ComponentDefinition, **kwargs) -> Position2D:
        return Position2D()
