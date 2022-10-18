from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from neighborly.core.ecs import Component, World, remove_on_archive


@remove_on_archive
@dataclass
class Position2D(Component):

    x: float = 0.0
    y: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "x": self.x, "y": self.y}

    @classmethod
    def create(cls, world: World, **kwargs) -> Position2D:
        return Position2D(x=kwargs.get("x", 0.0), y=kwargs.get("y", 0.0))
