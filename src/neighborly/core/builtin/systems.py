import logging

from neighborly.core.builtin.events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeElderEvent,
    BecomeYoungAdultEvent,
    DeathEvent,
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
from neighborly.core.ecs import World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.time import HOURS_PER_YEAR, SimDateTime

logger = logging.getLogger(__name__)


def character_aging_system(world: World, **kwargs) -> None:
    """Handles updating the ages of characters"""

    date_time = world.get_resource(SimDateTime)
    engine = world.get_resource(NeighborlyEngine)

    for _, character in world.get_component(GameCharacter):
        if character.gameobject.has_component(Deceased):
            continue

        character.age += float(date_time.delta_time) / HOURS_PER_YEAR

        if (
            character.gameobject.has_component(Child)
            and character.age >= character.character_def.aging.life_stages["teen"]
        ):
            character.gameobject.remove_component(Child)
            character.gameobject.add_component(Teen())

            event = BecomeAdolescentEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)

        elif (
            character.gameobject.has_component(Teen)
            and character.age
            >= character.character_def.aging.life_stages["young_adult"]
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

        elif (
            character.gameobject.has_component(YoungAdult)
            and character.age >= character.character_def.aging.life_stages["adult"]
        ):
            character.gameobject.remove_component(YoungAdult)

            event = BecomeAdultEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)

        elif (
            character.gameobject.has_component(Adult)
            and character.age >= character.character_def.aging.life_stages["elder"]
        ):
            character.gameobject.add_component(Elder())

            event = BecomeElderEvent(
                timestamp=date_time.to_iso_str(),
                character_id=character.gameobject.id,
                character_name=str(character.name),
            )
            character.gameobject.handle_event(event)

        if (
            character.age >= character.character_def.aging.lifespan
            and engine.rng.random() < 0.8
        ):
            print(f"{str(character.name)} has died")
            character.gameobject.handle_event(
                DeathEvent(
                    timestamp=date_time.to_iso_str(),
                    character_name=str(character.name),
                    character_id=character.gameobject.id,
                )
            )
            world.delete_gameobject(character.gameobject.id)
