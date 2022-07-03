import logging

from neighborly.core.builtin.events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeElderEvent,
    BecomeYoungAdultEvent,
)
from neighborly.core.builtin.statuses import (
    Adult,
    Child,
    Deceased,
    Elder,
    Teen,
    YoungAdult,
)
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import ISystem, World
from neighborly.core.life_event import LifeEventLogger
from neighborly.core.name_generation import TraceryNameFactory
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime
from neighborly.core.town import Town, TownConfig

logger = logging.getLogger(__name__)


def character_aging_system(world: World, **kwargs) -> None:
    """Handles updating the ages of characters"""

    date_time = world.get_resource(SimDateTime)
    event_logger = world.get_resource(LifeEventLogger)

    for _, character in world.get_component(GameCharacter):
        if character.gameobject.has_component(Deceased):
            continue

        character.age += float(date_time.delta_time) / HOURS_PER_YEAR

        if character.age >= character.character_def.lifecycle.life_stages["teen"]:
            character.gameobject.remove_component(Child)
            character.gameobject.add_component(Teen())

            event = BecomeAdolescentEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)
            event_logger.log_event(event, [character.gameobject.id])

        elif (
            character.age
            >= character.character_def.lifecycle.life_stages["young_adult"]
        ):
            character.gameobject.remove_component(Teen)
            character.gameobject.add_component(YoungAdult())
            character.gameobject.add_component(Adult())

            event = BecomeYoungAdultEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)
            event_logger.log_event(event, [character.gameobject.id])

        elif character.age >= character.character_def.lifecycle.life_stages["adult"]:
            character.gameobject.remove_component(YoungAdult)

            event = BecomeAdultEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)
            event_logger.log_event(event, [character.gameobject.id])

        elif character.age >= character.character_def.lifecycle.life_stages["elder"]:
            character.gameobject.add_component(Elder())

            event = BecomeElderEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)
            event_logger.log_event(event, [character.gameobject.id])


def default_town_setup_system(name: str, size: str) -> ISystem:
    """
    Create a new town and add it to the world

    Notes
    -----
    This system runs once during setup
    """

    def fn(world: World, **kwargs) -> None:
        town_name_generator = world.get_resource(TraceryNameFactory)

        town_name = town_name_generator.get_name(name)

        TOWN_SIZES = {"small": (3, 3), "medium": (5, 5), "large": (10, 10)}

        town_dimensions = TOWN_SIZES[size]

        town = Town.create(
            TownConfig(
                name=town_name, width=town_dimensions[0], length=town_dimensions[1]
            )
        )

        logger.debug(f"Created town of {town.name}")

    return fn
