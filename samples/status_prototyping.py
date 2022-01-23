from typing import Dict, Type

import esper

from neighborly.core.character.character import CharacterConfig, GameCharacter
from neighborly.core.character.status import Status
from neighborly.core.ecs_manager import register_character_config, create_character
from neighborly.plugins import default_plugin
from neighborly.simulation import SimulationConfig, Simulation

STATUSES = """
-
    name: Adult
    preconditions:
        - age > config.a
"""


class Occupation:
    __slots__ = "title"

    def __init__(self, title: str) -> None:
        self.title = title


_status_registry: Dict[str, Type[Status]] = {}


def register_status(tag: str):
    """Decorator for organizing status types"""

    def wrapper(status_cls: Type[Status]):
        _status_registry[tag] = status_cls
        status_cls.tag = tag
        return status_cls

    return wrapper


@register_status("adult")
class AdultStatus(Status):
    def check_preconditions(self, world: esper.World, character_id: int) -> bool:
        """Return true if the given character passes the preconditions"""
        character = world.component_for_entity(character_id, GameCharacter)
        return character.age >= character.config.lifecycle.adult_age

    def update(self, world: esper.World, character_id: int) -> bool:
        """Update status and return True is still active"""
        return True


@register_status("unemployed")
class UnemployedStatus(Status):
    def check_preconditions(self, world: esper.World, character_id: int) -> bool:
        """Return true if the given character passes the preconditions"""
        character = world.component_for_entity(character_id, GameCharacter)
        return character.statuses.has_status("adult") and not world.has_component(
            character_id, Occupation
        )

    def update(self, world: esper.World, character_id: int) -> bool:
        """Update status and return True is still active"""
        return True


def main():
    default_plugin.initialize_plugin()
    config = SimulationConfig(hours_per_timestep=4, seed=1010)
    sim = Simulation(config)

    register_character_config("default", CharacterConfig())

    character_1_id, character_1 = create_character(sim.world)

    for _, status_cls in _status_registry.items():
        if status_cls.check_preconditions(
                sim.world, character_1_id
        ) and not character_1.statuses.has_status(status_cls.get_tag()):
            character_1.statuses.add_status(status_cls())

    for _, status_cls in _status_registry.items():
        if status_cls.check_preconditions(
                sim.world, character_1_id
        ) and not character_1.statuses.has_status(status_cls.get_tag()):
            character_1.statuses.add_status(status_cls())

    print(character_1.statuses)


if __name__ == "__main__":
    main()
