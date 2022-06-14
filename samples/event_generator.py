from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine


class LifeEventEmitter:
    """
    Generates a specific type of life event for characters to engage in
    """

    def __init__(self, probability: float, max_iters: int = -1) -> None:
        self.probability: float = probability
        self.max_iters: float = probability

    def run(self, world: World) -> None:
        engine = world.get_resource(NeighborlyEngine)
        if engine.get_rng().random() < self.probability:
            ...
