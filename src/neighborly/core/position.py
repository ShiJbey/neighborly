from dataclasses import dataclass

from neighborly.core.ecs import Component


@dataclass
class Position2D(Component):
    x: float = 0.0
    y: float = 0.0
