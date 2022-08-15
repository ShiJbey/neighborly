"""
John Wick Neighborly Sample
Author: Shi Johnson-Bey

John Wick is a movie franchise staring Keanu Reeves, in which
his character, John Wick, is part of an underground society of
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

from neighborly.builtin.statuses import Adult
from neighborly.core.archetypes import (
    BusinessArchetype,
    BusinessArchetypeLibrary,
    CharacterArchetype,
)
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.engine import NeighborlyEngine
from neighborly.core.life_event import (
    EventResult,
    EventRole,
    EventRoleType,
    LifeEvent,
    LifeEventLibrary,
    LifeEventLog,
    LifeEventType,
)
from neighborly.core.relationship import RelationshipGraph
from neighborly.core.residence import Resident
from neighborly.core.time import SimDateTime
from neighborly.plugins.default_plugin import DefaultPlugin
from neighborly.plugins.talktown import TalkOfTheTownPlugin
from neighborly.plugins.weather_plugin import WeatherPlugin
from neighborly.simulation import Plugin, Simulation, SimulationBuilder


@dataclass
class Assassin(Component):
    """Assassin component to be attached to a character

    Assassins mark people who are part of the criminal
    underworld and who may exchange coins for assassinations
    of characters that they don't like
    """

    coins: int = 0
    kills: int = 0


def assassin_character_archetype() -> CharacterArchetype:
    return CharacterArchetype(
        name="Assassin",
        lifespan=85,
        life_stages={
            "child": 0,
            "teen": 13,
            "young_adult": 18,
            "adult": 30,
            "elder": 65,
        },
        extra_components={Assassin: {}},
    )


def continental_hotel() -> BusinessArchetype:
    return BusinessArchetype(
        name="The Continental Hotel",
        max_instances=1,
        min_population=40,
        employee_types={
            "Manager": 1,
            "Concierge": 1,
            "Bartender": 2,
        },
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
        return EventResult(generated_events=[event])

    return LifeEventType(
        name="BecomeAssassin",
        probability=probability,
        execute_fn=execute,
        roles=[EventRoleType(name="Character", binder_fn=bind_character)],
    )


def hire_assassin_event(
    dislike_threshold: int, probability: float = 0.2
) -> LifeEventType:
    def bind_client(world: World, event: LifeEvent) -> Optional[GameObject]:
        """Find someone who hates another character"""
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
        event_log = world.get_resource(LifeEventLog)
        date_time = world.get_resource(SimDateTime)
        assassin = world.get_gameobject(event["Assassin"])
        assassin.get_component(Assassin).kills += 1

        death_event = LifeEvent(
            name="Death",
            timestamp=date_time.to_iso_str(),
            roles=[
                EventRole("Character", event["Target"]),
            ],
        )

        world.get_gameobject(event["Target"]).archive()

        return EventResult(generated_events=[event, death_event])

    return LifeEventType(
        name="HireAssassin",
        probability=probability,
        roles=[
            EventRoleType(name="Client", components=[GameCharacter, Adult]),
            EventRoleType(name="Target", binder_fn=bind_target),
            EventRoleType(name="Assassin", components=[Assassin, Adult]),
        ],
        execute_fn=execute_fn,
    )


class JohnWickPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs) -> None:
        LifeEventLibrary.add(hire_assassin_event(-30))
        LifeEventLibrary.add(become_an_assassin())
        BusinessArchetypeLibrary.add(continental_hotel())


def main():
    sim = (
        SimulationBuilder(
            seed=random.randint(0, 999999),
            world_gen_start=SimDateTime(year=1839, month=8, day=19),
            world_gen_end=SimDateTime(year=1979, month=8, day=19),
        )
        .add_plugin(DefaultPlugin())
        .add_plugin(WeatherPlugin())
        .add_plugin(TalkOfTheTownPlugin())
        .add_plugin(JohnWickPlugin())
        .build()
    )

    sim.world.get_resource(LifeEventLog).subscribe(lambda e: print(str(e)))

    st = time.time()
    sim.establish_setting()
    elapsed_time = time.time() - st

    print(f"World Date: {sim.time.to_iso_str()}")
    print("Execution time: ", elapsed_time, "seconds")


if __name__ == "__main__":
    main()
