"""
John Wick Neighborly Sample
Author: Shi Johnson-Bey

John Wick is a movie franchise staring Keanu Reeves, in which
his entity, John Wick, is part of an underground society of
assassins and hit-people. The member of the criminal underworld
follow specific social norms that regular civilians don't. All
favors come at the cost of coins, and no work-for-hire killing
is allowed to take place in specific locations. For example,
hotels that represent safe-zones.

This example shows how someone could use neighborly to model
the narrative world of John Wick.

"""
import random
import time
from dataclasses import dataclass
from typing import Any

from neighborly.archetypes import BaseBusinessArchetype
from neighborly.components.business import IBusinessType
from neighborly.components.character import Deceased, GameCharacter, LifeStageValue
from neighborly.components.shared import Active
from neighborly.core.query import QueryBuilder
from neighborly.core.ecs import Component, World
from neighborly.core.event import Event, EventRole
from neighborly.core.life_event import ILifeEvent, LifeEvent
from neighborly.core.time import SimDateTime
from neighborly.engine import LifeEvents
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.plugins import defaults, talktown, weather
from neighborly.simulation import Neighborly, Plugin, Simulation
from neighborly.utils.role_filters import (
    get_friendships_lte,
    has_component,
    life_stage_ge,
)
from neighborly.utils.common import from_pattern


@dataclass
class Assassin(Component):
    """Assassin component to be attached to an entity

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0


class Hotel(IBusinessType):
    pass


def continental_hotel() -> BaseBusinessArchetype:
    return BaseBusinessArchetype(
        name_format="The Continental Hotel",
        max_instances=1,
        min_population=40,
        employee_types={
            "Manager": 1,
            "Concierge": 1,
            "Bartender": 2,
        },
        business_type=Hotel,
    )


def become_an_assassin(probability: float = 0.3) -> ILifeEvent:
    """Turns ordinary people into assassins"""

    def execute(world: World, event: Event):
        new_assassin = world.get_gameobject(event["Character"])
        new_assassin.add_component(Assassin())

    return LifeEvent(
        name="BecomeAssassin",
        probability=probability,
        effect=execute,
        bind_fn=from_pattern(
            QueryBuilder("Character")
            .with_((GameCharacter, Active))
            .without_((Assassin,))
            .filter_(life_stage_ge(LifeStageValue.YoungAdult))
            .build()
        ),
    )


def hire_assassin_event(
    dislike_threshold: float = 0.3, probability: float = 0.2
) -> ILifeEvent:
    def execute_fn(world: World, event: Event):
        date_time = world.get_resource(SimDateTime)
        assassin = world.get_gameobject(event["Assassin"])
        assassin.get_component(Assassin).kills += 1

        Event(
            name="Death",
            timestamp=date_time.to_iso_str(),
            roles=[
                EventRole("Character", event["Target"]),
            ],
        )

        world.get_gameobject(event["Target"]).add_component(Deceased())

    return LifeEvent(
        name="HireAssassin",
        probability=probability,
        effect=execute_fn,
        bind_fn=from_pattern(
            QueryBuilder("Client", "Target", "Assassin")
            .with_((GameCharacter, Active), "Client")
            .get_(get_friendships_lte(dislike_threshold), "Client", "Target")
            .filter_(has_component(Active), "Target")
            .with_((Assassin, Active), "Assassin")
            .build()
        ),
    )


class JohnWickPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        LifeEvents.add(hire_assassin_event(-30))
        LifeEvents.add(become_an_assassin())
        sim.engine.business_archetypes.add("The Continental Hotel", continental_hotel())


EXPORT_WORLD = False


def main():
    sim = (
        Neighborly(
            seed=random.randint(0, 999999),
            starting_date=SimDateTime(year=1990, month=0, day=0),
            print_events=True,
        )
        .add_plugin(defaults.get_plugin())
        .add_plugin(weather.get_plugin())
        .add_plugin(talktown.get_plugin())
        .add_plugin(JohnWickPlugin())
        .build()
    )

    st = time.time()
    sim.run_for(40)
    elapsed_time = time.time() - st

    print(f"World Date: {sim.date.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")

    if EXPORT_WORLD:
        output_path = f"{sim.seed}_{sim.town.name.replace(' ', '_')}.json"

        with open(output_path, "w") as f:
            data = NeighborlyJsonExporter().export(sim)
            f.write(data)
            print(f"Simulation data written to: '{output_path}'")


if __name__ == "__main__":
    main()
