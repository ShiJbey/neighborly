import pytest

from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.roles import Role
from neighborly.core.time import SimDateTime


class PriceDisputeEvent(LifeEvent):
    def __init__(
        self, date: SimDateTime, merchant: GameObject, customer: GameObject
    ) -> None:
        super().__init__(date, [Role("Merchant", merchant), Role("Customer", customer)])

    @property
    def merchant(self):
        return self["Merchant"]

    @property
    def customer(self):
        return self["Customer"]


class DeclareRivalryEvent(LifeEvent):
    def __init__(self, date: SimDateTime, *characters: GameObject) -> None:
        super().__init__(date, [Role("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


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


def test_life_event_get_type(sample_event: LifeEvent):
    assert sample_event.get_type() == "PriceDisputeEvent"


def test_life_event_to_dict(sample_event: LifeEvent):
    serialized_event = sample_event.to_dict()
    assert serialized_event["type"] == "PriceDisputeEvent"
    assert serialized_event["timestamp"] == "0001-01-01T00:00:00"
    assert serialized_event["roles"]["Merchant"] == 1
    assert serialized_event["roles"]["Customer"] == 2
