from typing import Any, Dict, Tuple

import pytest

from neighborly.core.ecs import GameObject, World
from neighborly.core.event import Event
from neighborly.core.time import SimDateTime


class PriceDisputeEvent(Event):
    def __init__(
        self, date: SimDateTime, merchant: GameObject, customer: GameObject
    ) -> None:
        super().__init__(date)
        self.merchant: GameObject = merchant
        self.customer: GameObject = customer

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "merchant": self.merchant.uid,
            "customer": self.customer.uid,
        }


class DeclareRivalryEvent(Event):
    def __init__(self, date: SimDateTime, *characters: GameObject) -> None:
        super().__init__(date)
        self.characters: Tuple[GameObject, ...] = characters


@pytest.fixture
def sample_event():
    world = World()
    merchant = world.spawn_gameobject(name="Merchant")
    customer = world.spawn_gameobject(name="customer")

    return PriceDisputeEvent(SimDateTime(1, 1, 1), merchant, customer)


@pytest.fixture
def shared_role_event():
    world = World()
    character_a = world.spawn_gameobject(name="A")
    character_b = world.spawn_gameobject(name="B")

    return DeclareRivalryEvent(SimDateTime(1, 1, 1), character_a, character_b)


def test_life_event_get_type(sample_event: Event):
    assert sample_event.get_type() == "PriceDisputeEvent"


def test_life_event_to_dict(sample_event: Event):
    serialized_event = sample_event.to_dict()
    assert serialized_event["type"] == "PriceDisputeEvent"
    assert serialized_event["timestamp"] == "0001-01-01T00:00:00"
    assert serialized_event["merchant"] == 1
    assert serialized_event["customer"] == 2
