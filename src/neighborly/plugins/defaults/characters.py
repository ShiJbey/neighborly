from typing import Any

from neighborly.components.character import (
    BaseCharacter,
    CanAge,
    CharacterConfig,
    Health,
    LifeStageConfig,
)
from neighborly.core.ecs import GameObject, World
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default characters plugin",
    plugin_id="default.characters",
    version="0.1.0",
)


class Human(BaseCharacter):
    config = CharacterConfig(
        spawn_frequency=1,
        aging=LifeStageConfig(
            adolescent_age=13, young_adult_age=18, adult_age=30, senior_age=65
        ),
        avg_lifespan=80,
    )

    @classmethod
    def instantiate(cls, world: World, **kwargs: Any) -> GameObject:
        character = super().instantiate(world, **kwargs)

        character.add_component(CanAge)

        return character


def setup(sim: Neighborly):
    sim.world.gameobject_manager.register_component(Health)
    sim.world.gameobject_manager.register_component(Human)
