import random
from typing import Any

from neighborly.core.ai import AIComponent
from neighborly.core.ecs import IComponentFactory, World


class AIComponentFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> AIComponent:
        return AIComponent(world.get_resource(random.Random))
