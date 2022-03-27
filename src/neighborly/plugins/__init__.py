from abc import ABC, abstractmethod
from dataclasses import dataclass

from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine


@dataclass(frozen=True)
class PluginContext:
    engine: NeighborlyEngine
    world: World


class NeighborlyPlugin(ABC):

    @abstractmethod
    def apply(self, ctx: PluginContext, **kwargs) -> None:
        raise NotImplementedError()
