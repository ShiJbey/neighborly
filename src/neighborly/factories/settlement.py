from typing import Any

from neighborly.core.ecs import IComponentFactory, World
from neighborly.core.settlement import GridSettlementMap, Settlement


class SettlementFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Settlement:
        return Settlement(GridSettlementMap((kwargs["width"], kwargs["length"])))
