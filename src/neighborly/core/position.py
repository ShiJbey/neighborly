from dataclasses import dataclass

from neighborly.core.ecs import Component
from neighborly.core.engine import AbstractFactory, ComponentSpec


@dataclass
class Position2D(Component):
    x: float = 0.0
    y: float = 0.0


class Position2DFactory(AbstractFactory):

    def __init__(self):
        super().__init__("Position2D")

    def create(self, spec: ComponentSpec, **kwargs) -> Position2D:
        return Position2D()
