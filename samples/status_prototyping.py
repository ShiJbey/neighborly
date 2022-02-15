from typing import Dict, Type

from neighborly.core.character.character import GameCharacter
from neighborly.core.character.status import Status, StatusManager
from neighborly.core.ecs import World, Component
from neighborly.plugins import default_plugin
from neighborly.simulation import SimulationConfig, Simulation

STATUSES = """
-
    name: Adult
    preconditions:
        - age > config.a
"""


class Occupation(Component):
    __slots__ = "title"

    def __init__(self, title: str) -> None:
        super().__init__()
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

    @classmethod
    def check_preconditions(cls, world: World, character: GameCharacter) -> bool:
        """Return true if the given character passes the preconditions"""
        return character.age >= character.config.lifecycle.adult_age

    def update(self, world: World, character: GameCharacter) -> bool:
        """Update status and return True is still active"""
        return True


@register_status("unemployed")
class UnemployedStatus(Status):
    @classmethod
    def check_preconditions(cls, world: World, character: GameCharacter) -> bool:
        """Return true if the given character passes the preconditions"""
        return character.gameobject.get_component(StatusManager).has_status("adult") \
               and not character.gameobject.has_component(Occupation)

    def update(self, world: World, character_id: int) -> bool:
        """Update status and return True is still active"""
        return True


def main():
    config = SimulationConfig(hours_per_timestep=4, seed=1010)
    sim = Simulation.create(config=config)
    default_plugin.initialize_plugin(sim.get_engine())

    character = sim.get_engine().create_character("default")
    character.add_component(StatusManager())

    for _, status_cls in _status_registry.items():
        if status_cls.check_preconditions(
                sim.world, character.get_component(GameCharacter)
        ) and not character.get_component(StatusManager).has_status(status_cls.get_tag()):
            character.get_component(StatusManager).add_status(status_cls({}, []))

    print(character.get_component(StatusManager))


if __name__ == "__main__":
    main()
