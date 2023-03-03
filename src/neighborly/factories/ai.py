from typing import Any

from neighborly.content_management import AIBrainLibrary
from neighborly.core.ai.brain import AIComponent
from neighborly.core.ecs import IComponentFactory, World


class AIComponentFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> AIComponent:
        brain_library = world.get_resource(AIBrainLibrary)
        brain_factory = brain_library[kwargs["brain"]]
        brain_options = kwargs.get("brain_options", {})
        return AIComponent(brain_factory(**brain_options))
