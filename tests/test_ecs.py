from dataclasses import dataclass

import pytest

from neighborly.core.ecs import Component, World


class SimpleGameCharacter(Component):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def __repr__(self) -> str:
        return f"GameCharacter(name={self.name})"


class SimpleLocation(Component):
    __slots__ = "capacity"

    def __init__(self, capacity: int = 999) -> None:
        super().__init__()
        self.capacity: int = capacity

    def __repr__(self) -> str:
        return f"Location(capacity={self.capacity})"


@dataclass
class SimpleRoutine(Component):
    free: bool


@dataclass
class A(Component):
    value: int = 0


@dataclass
class B(Component):
    value: int = 0


@dataclass
class FakeResource:
    config_value: int = 5


def test_has_resource():
    world = World()
    assert world.has_resource(FakeResource) is False
    world.add_resource(FakeResource())
    assert world.has_resource(FakeResource) is True


def test_get_resource():
    world = World()
    fake_resource = FakeResource()
    assert world.has_resource(FakeResource) is False
    # This should throw a key error when not present
    with pytest.raises(KeyError):
        assert world.get_resource(FakeResource)
    world.add_resource(fake_resource)
    assert world.get_resource(FakeResource) == fake_resource


def test_remove_resource():
    world = World()
    world.add_resource(FakeResource())
    assert world.has_resource(FakeResource) is True
    world.remove_resource(FakeResource)
    assert world.has_resource(FakeResource) is False
    # This should throw a key error when not present
    with pytest.raises(KeyError):
        world.remove_resource(FakeResource)


def test_add_resource():
    world = World()
    fake_resource = FakeResource()
    assert world.has_resource(FakeResource) is False
    world.add_resource(fake_resource)
    assert world.has_resource(FakeResource) is True


def test_gameobject() -> None:
    world = World()
    adrian = world.spawn_gameobject(SimpleRoutine(False), SimpleGameCharacter("Adrian"), name="Adrian")
    jamie = world.spawn_gameobject(SimpleRoutine(False), SimpleGameCharacter("Jamie"), name="Jamie")
    park = world.spawn_gameobject(SimpleLocation(), name="Park")
    office_building = world.spawn_gameobject(SimpleLocation(18), name="Office Building")

    assert jamie.get_component(SimpleGameCharacter).name == "Jamie"

    assert len(world.get_component(SimpleGameCharacter)) == 2
    assert len(world.get_component(SimpleLocation)) == 2

    assert park.get_component(SimpleLocation).capacity == 999
    assert office_building.get_component(SimpleLocation).capacity == 18

    assert len(world.get_components(SimpleGameCharacter, SimpleRoutine)) == 2
