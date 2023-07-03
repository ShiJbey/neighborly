import pytest

from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import EventRole, LifeEvent
from neighborly.core.time import SimDateTime


class PriceDisputeEvent(LifeEvent):
    def __init__(
        self,
        world: World,
        date: SimDateTime,
        merchant: GameObject,
        customer: GameObject,
    ) -> None:
        super().__init__(
            world,
            date,
            [EventRole("Merchant", merchant), EventRole("Customer", customer)],
        )

    @property
    def merchant(self):
        return self["Merchant"]

    @property
    def customer(self):
        return self["Customer"]


class DeclareRivalryEvent(LifeEvent):
    def __init__(
        self, world: World, date: SimDateTime, *characters: GameObject
    ) -> None:
        super().__init__(world, date, [EventRole("Character", c) for c in characters])

    @property
    def characters(self):
        return self._roles.get_all("Character")


@pytest.fixture
def sample_event():
    world = World()
    merchant = world.gameobject_manager.spawn_gameobject(name="Merchant")
    customer = world.gameobject_manager.spawn_gameobject(name="customer")

    return PriceDisputeEvent(world, SimDateTime(1, 1, 1), merchant, customer)


@pytest.fixture
def shared_role_event():
    world = World()
    character_a = world.gameobject_manager.spawn_gameobject(name="A")
    character_b = world.gameobject_manager.spawn_gameobject(name="B")

    return DeclareRivalryEvent(world, SimDateTime(1, 1, 1), character_a, character_b)


def test_life_event_to_dict(sample_event: LifeEvent):
    serialized_event = sample_event.to_dict()
    assert serialized_event["type"] == "PriceDisputeEvent"
    assert serialized_event["timestamp"] == "0001-01-01T00:00:00"
    assert serialized_event["roles"]["Merchant"] == 1
    assert serialized_event["roles"]["Customer"] == 2
