"""
This sample shows how to manually execute life events
"""
import random
from random import Random
from typing import Any, Dict, List, Optional

from neighborly import (
    Component,
    GameObject,
    ISystem,
    Neighborly,
    NeighborlyConfig,
    SimDateTime,
    World,
)
from neighborly.components import InTheWorkforce, Unemployed
from neighborly.core.ecs.ecs import Active
from neighborly.core.event import EventBuffer, EventHistory
from neighborly.core.life_event import ActionableLifeEvent
from neighborly.core.relationship import Romance, add_relationship, get_relationship
from neighborly.core.roles import Role, RoleList
from neighborly.decorators import component, system
from neighborly.plugins.defaults.life_events import StartDatingLifeEvent
from neighborly.utils.common import (
    add_character_to_settlement,
    spawn_character,
    spawn_settlement,
)

sim = Neighborly(
    NeighborlyConfig().parse_obj(
        {
            "seed": 3,
            "relationship_schema": {
                "stats": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                        "changes_with_time": True,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                        "changes_with_time": True,
                    },
                },
            },
            "plugins": [
                "neighborly.plugins.defaults.names",
                "neighborly.plugins.defaults.characters",
                "neighborly.plugins.defaults.life_events",
            ],
        }
    )
)


@component(sim)
class SimpleBrain(Component):
    def __init__(self) -> None:
        super().__init__()
        self.optional_events: List[ActionableLifeEvent] = []

    def append_life_event(self, event: ActionableLifeEvent) -> None:
        self.optional_events.append(event)

    def select_life_event(self, world: World) -> Optional[ActionableLifeEvent]:
        rng = world.get_resource(Random)
        if self.optional_events:
            chosen = rng.choice(self.optional_events)
            if chosen.is_valid(world):
                return chosen

        return None

    def to_dict(self) -> Dict[str, Any]:
        return {}


@system(sim)
class SimpleBrainSystem(ISystem):
    sys_group = "character-update"
    priority = -20

    def process(self, *args: Any, **kwargs: Any) -> None:
        brains = self.world.get_component(SimpleBrain)
        random.shuffle(brains)
        for _, brain in brains:
            event = brain.select_life_event(self.world)
            if event:
                self.world.get_resource(EventBuffer).append(event)
                event.execute()


class FindJob(ActionableLifeEvent):
    def __init__(
        self,
        date: SimDateTime,
        character: GameObject,
        business: GameObject,
        occupation: str,
    ):
        super().__init__(
            date, [Role("Character", character), Role("Business", business)]
        )
        self.occupation: str = occupation

    def execute(self) -> None:
        # print("Decided to find a job")
        pass

    @classmethod
    def instantiate(
        cls,
        world: World,
        bindings: RoleList,
    ) -> Optional[ActionableLifeEvent]:
        character = bindings["Character"]
        business = world.get_gameobject(world.get_component(MockBiz)[0][0])
        return cls(world.get_resource(SimDateTime), character, business, "worker")


@component(sim)
class MockBiz(Component):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name: str = name

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@system(sim)
class FindAJobSystem(ISystem):
    sys_group = "character-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        business = self.world.get_gameobject(self.world.get_component(MockBiz)[0][0])
        for guid, _ in self.world.get_components((Active, InTheWorkforce, Unemployed)):
            gameobject = self.world.get_gameobject(guid)
            gameobject.get_component(SimpleBrain).append_life_event(
                FindJob(
                    self.world.get_resource(SimDateTime), gameobject, business, "worker"
                )
            )


def main():
    republic_city = spawn_settlement(sim.world, "Republic City")

    sim.world.spawn_gameobject(
        [MockBiz("Cabbage Corp."), EventHistory(), SimpleBrain()], "Cabbage Corp."
    )

    korra = spawn_character(
        sim.world,
        "character::default::female",
        first_name="Avatar",
        last_name="Korra",
        age=21,
    )
    korra.add_component(SimpleBrain())
    korra.add_component(EventHistory())

    add_character_to_settlement(korra, republic_city)

    asami = spawn_character(
        sim.world,
        "character::default::female",
        first_name="Asami",
        last_name="Sato",
        age=22,
    )
    asami.add_component(SimpleBrain())
    asami.add_component(EventHistory())

    add_character_to_settlement(asami, republic_city)

    add_relationship(korra, asami)
    add_relationship(asami, korra)

    get_relationship(korra, asami).get_component(Romance).increment(5)
    get_relationship(asami, korra).get_component(Romance).increment(5)

    event = StartDatingLifeEvent.instantiate(
        sim.world, RoleList([Role("Initiator", korra), Role("Other", asami)])
    )

    print(event)

    sim.step()

    get_relationship(korra, asami).get_component(Romance).increment(25)
    get_relationship(asami, korra).get_component(Romance).increment(25)

    event = StartDatingLifeEvent.instantiate(
        sim.world, RoleList([Role("Initiator", korra), Role("Other", asami)])
    )

    assert event

    event.get_initiator().get_component(SimpleBrain).append_life_event(event)

    sim.step()

    print(event.is_valid(sim.world))


if __name__ == "__main__":
    main()
