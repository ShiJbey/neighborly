from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.rng import DefaultRNG


class LifeEventEmitter:
    """
    Generates a specific type of life event for characters to engage in
    """

    def __init__(self, probability: float, max_iters: int = -1) -> None:
        self.probability: float = probability
        self.max_iters: float = probability

    def run(self, world: World) -> None:
        engine = world.get_resource(NeighborlyEngine)
        if world.get_resource(DefaultRNG).random() < self.probability:
            ...
