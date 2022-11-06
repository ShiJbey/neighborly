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
from typing import List, Optional

from neighborly import (
    Component,
    GameObject,
    Plugin,
    SimDateTime,
    Simulation,
    SimulationBuilder,
    World,
)
from neighborly.builtin.components import Adult, Deceased
from neighborly.core.archetypes import BaseBusinessArchetype, BusinessArchetypes
from neighborly.core.business import IBusinessType
from neighborly.core.character import GameCharacter
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    LifeEvent,
    LifeEvents,
    LifeEventType,
    Role,
    RoleType,
    constant_probability,
)
from neighborly.core.relationship import RelationshipGraph
from neighborly.core.residence import Resident
from neighborly.exporter import NeighborlyJsonExporter
from neighborly.plugins import defaults, talktown, weather


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


def become_an_assassin(probability: float = 0.3) -> LifeEventType:
    """Turns ordinary people into assassins"""

    def bind_character(world: World, event: LifeEvent) -> Optional[GameObject]:
        candidates: List[GameObject] = []
        for gid, (character, _) in world.get_components(GameCharacter, Adult):
            if not character.gameobject.has_component(Assassin):
                candidates.append(character.gameobject)

        if candidates:
            return world.get_resource(NeighborlyEngine).rng.choice(candidates)

    def execute(world: World, event: LifeEvent):
        new_assassin = world.get_gameobject(event["Character"])
        new_assassin.add_component(Assassin())

    return LifeEventType(
        name="BecomeAssassin",
        probability=constant_probability(probability),
        effects=execute,
        roles=[RoleType(name="Character", binder_fn=bind_character)],
    )


def hire_assassin_event(
    dislike_threshold: int, probability: float = 0.2
) -> LifeEventType:
    def bind_client(world: World, event: LifeEvent) -> Optional[GameObject]:
        """Find someone who hates another entity"""
        rel_graph = world.get_resource(RelationshipGraph)
        candidates: List[int] = []
        for gid, _ in world.get_components(Component, Resident):
            for relationship in rel_graph.get_relationships(gid):
                if relationship.friendship < dislike_threshold:
                    candidates.append(gid)

        if candidates:
            return world.get_gameobject(
                world.get_resource(NeighborlyEngine).rng.choice(candidates)
            )

    def bind_target(world: World, event: LifeEvent) -> Optional[GameObject]:
        """Find someone that the client would want dead"""
        rel_graph = world.get_resource(RelationshipGraph)
        candidates: List[int] = []
        for relationship in rel_graph.get_relationships(event["Client"]):
            if relationship.friendship < dislike_threshold:
                candidate = world.get_gameobject(relationship.target)
                if candidate.has_component(Resident):
                    candidates.append(relationship.target)

        if candidates:
            return world.get_gameobject(
                world.get_resource(NeighborlyEngine).rng.choice(candidates)
            )

    def execute_fn(world: World, event: LifeEvent):
        date_time = world.get_resource(SimDateTime)
        assassin = world.get_gameobject(event["Assassin"])
        assassin.get_component(Assassin).kills += 1

        LifeEvent(
            name="Death",
            timestamp=date_time.to_iso_str(),
            roles=[
                Role("Character", event["Target"]),
            ],
        )

        world.get_gameobject(event["Target"]).add_component(Deceased())

    return LifeEventType(
        name="HireAssassin",
        probability=constant_probability(probability),
        roles=[
            RoleType(
                name="Client", components=[GameCharacter, Adult], binder_fn=bind_client
            ),
            RoleType(name="Target", binder_fn=bind_target),
            RoleType(name="Assassin", components=[Assassin, Adult]),
        ],
        effects=execute_fn,
    )


class JohnWickPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        LifeEvents.add(hire_assassin_event(-30))
        LifeEvents.add(become_an_assassin())
        BusinessArchetypes.add("The Continental Hotel", continental_hotel())


EXPORT_WORLD = False


def main():
    sim = (
        SimulationBuilder(
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
