from __future__ import annotations

import random
from typing import Any

from neighborly import Neighborly, World
from neighborly.stat_system import ClampedStatComponent, StatComponent
from neighborly.utils.common import debug_print_gameobject

sim = Neighborly()


class Health(StatComponent):
    """Tracks how healthy a character is."""

    @staticmethod
    def instantiate(world: World, **kwargs: Any) -> Health:
        rng = world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.normalvariate(85, 10)))
        return Health(base_value=base_value)


class HealthDecayRate(StatComponent):
    """Tracks how fast a character's health decreases each year."""

    pass


class Attractiveness(StatComponent):
    """Tracks how visually attractive a character is."""

    @staticmethod
    def instantiate(world: World, **kwargs: Any) -> Attractiveness:
        rng = world.resource_manager.get_resource(random.Random)
        base_value = float(kwargs.get("base_value", rng.normalvariate(25, 10)))
        return Attractiveness(base_value=base_value)


class Influence(StatComponent):
    """Tracks how much social influence a character has."""

    pass


class Fertility(ClampedStatComponent):
    def __init__(self, base_value: float) -> None:
        super().__init__(base_value, 0.0, 1.0)


if __name__ == "__main__":
    sim.world.gameobject_manager.register_component(Health, factory=Health.instantiate)
    sim.world.gameobject_manager.register_component(HealthDecayRate)
    sim.world.gameobject_manager.register_component(
        Attractiveness, factory=Attractiveness.instantiate
    )
    sim.world.gameobject_manager.register_component(Influence)
    sim.world.gameobject_manager.register_component(Fertility)

    character = sim.world.gameobject_manager.spawn_gameobject(
        name="Character",
        components={
            Health: {"base_value": 0},
            HealthDecayRate: {"base_value": 0},
            Attractiveness: {"base_value": 0},
            Influence: {"base_value": 0},
            Fertility: {"base_value": 0},
        },
    )

    debug_print_gameobject(character)
