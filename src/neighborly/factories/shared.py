from __future__ import annotations

from typing import Any

from neighborly.components.shared import Name
from neighborly.core.ecs import IComponentFactory, World
from neighborly.core.tracery import Tracery


class NameFactory(IComponentFactory):
    """Creates instances of Name Components using Tracery"""

    def create(self, world: World, value: str = "", **kwargs: Any) -> Name:
        return Name(Tracery.generate(value))
