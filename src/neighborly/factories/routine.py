from typing import Any

from neighborly.components.routine import Routine
from neighborly.core.ecs import IComponentFactory, World


class RoutineFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Routine:
        routine = Routine()
        return routine
