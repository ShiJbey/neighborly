from typing import Any, Dict, Tuple

import pytest

from neighborly.ecs import GameObject, World
from neighborly.life_event import EventHistory, EventLog, LifeEvent
from neighborly.simulation import Neighborly
from neighborly.time import SimDateTime


class PriceDisputeEvent(LifeEvent):
    __slots__ = "merchant", "customer"

    merchant: GameObject
    customer: GameObject

    def __init__(
        self,
        world: World,
        date: SimDateTime,
        merchant: GameObject,
        customer: GameObject,
    ) -> None:
        super().__init__(world, date)
        self.merchant = merchant
        self.customer = customer

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        self.merchant.get_component(EventHistory).append(self)
        self.customer.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "merchant": self.merchant.uid,
            "customer": self.customer.uid,
        }


class DeclareRivalryEvent(LifeEvent):
    __slots__ = "characters"

    characters: Tuple[GameObject, ...]

    def __init__(
        self, world: World, date: SimDateTime, *characters: GameObject
    ) -> None:
        super().__init__(world, date)
        self.characters = characters

    def on_dispatch(self) -> None:
        self.world.resource_manager.get_resource(EventLog).append(self)
        for character in self.characters:
            character.get_component(EventHistory).append(self)

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "characters": [c.uid for c in self.characters]}


@pytest.fixture
def sample_event():
    sim = Neighborly()
    merchant = sim.world.gameobject_manager.spawn_gameobject(name="Merchant")
    customer = sim.world.gameobject_manager.spawn_gameobject(name="customer")

    return PriceDisputeEvent(sim.world, SimDateTime(1, 1, 1), merchant, customer)


@pytest.fixture
def shared_role_event():
    sim = Neighborly()
    character_a = sim.world.gameobject_manager.spawn_gameobject(name="A")
    character_b = sim.world.gameobject_manager.spawn_gameobject(name="B")

    return DeclareRivalryEvent(
        sim.world, SimDateTime(1, 1, 1), character_a, character_b
    )


def test_life_event_to_dict(sample_event: LifeEvent):
    serialized_event = sample_event.to_dict()
    assert serialized_event["type"] == "PriceDisputeEvent"
    assert serialized_event["timestamp"] == "0001-01-01T00:00:00"
    assert serialized_event["merchant"] == 1
    assert serialized_event["customer"] == 2
