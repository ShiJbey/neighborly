from dataclasses import dataclass
from typing import Any

import pytest

from neighborly.core.ecs import (
    Component,
    ComponentNotFoundError,
    GameObjectNotFoundError,
    ISystem,
    ResourceNotFoundError,
    World,
)


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


@dataclass
class AnotherFakeResource:
    config_value: int = 43


class FakeSystemBaseA(ISystem):
    def process(self, *args: Any, **kwargs: Any):
        for _, a in self.world.get_component(A):
            a.value += 1


#########################################
# TEST WORLD GAMEOBJECT-RELATED METHODS
#########################################


def test_spawn_gameobject():
    world = World()

    adrian = world.spawn_gameobject(
        [SimpleRoutine(False), SimpleGameCharacter("Adrian")]
    )

    assert world.ecs.entity_exists(adrian.id)

    jamie = world.spawn_gameobject([SimpleRoutine(False), SimpleGameCharacter("Jamie")])

    assert world.ecs.entity_exists(jamie.id)

    park = world.spawn_gameobject([SimpleLocation()], name="Park")

    assert world.ecs.entity_exists(park.id)

    office_building = world.spawn_gameobject(
        [SimpleLocation(18)], name="Office Building"
    )

    assert world.ecs.entity_exists(office_building.id)

    assert jamie.get_component(SimpleGameCharacter).name == "Jamie"

    assert len(world.get_component(SimpleGameCharacter)) == 2
    assert len(world.get_component(SimpleLocation)) == 2

    assert park.get_component(SimpleLocation).capacity == 999
    assert office_building.get_component(SimpleLocation).capacity == 18

    assert len(world.get_components(SimpleGameCharacter, SimpleRoutine)) == 2


def test_get_gameobject():
    world = World()
    gameobject = world.spawn_gameobject()
    assert world.get_gameobject(gameobject.id) == gameobject


def test_get_gameobject_raises_exception():
    with pytest.raises(GameObjectNotFoundError):
        world = World()
        world.get_gameobject(7)


def test_has_gameobject():
    world = World()
    assert world.has_gameobject(1) is False
    gameobject = world.spawn_gameobject()
    assert world.has_gameobject(gameobject.id) is True


def test_get_gameobjects():
    world = World()
    g1 = world.spawn_gameobject()
    g2 = world.spawn_gameobject()
    g3 = world.spawn_gameobject()
    assert world.get_gameobjects() == [g1, g2, g3]


def test_try_gameobject():
    world = World()
    assert world.try_gameobject(1) is None
    world.spawn_gameobject()
    assert world.try_gameobject(1) is not None


def test_delete_gameobject():

    world = World()

    g1 = world.spawn_gameobject([A()])

    # Make sure that the game objects exists
    assert world.has_gameobject(g1.id) is True

    world.delete_gameobject(g1.id)

    # the GameObject should still exist and be removed
    # at the start of the next step
    assert world.has_gameobject(g1.id) is True

    world.step()

    # Now the gameobject should be deleted
    assert world.has_gameobject(g1.id) is False

    # Ensure that GameObjects that were always empty
    # are properly removed
    g2 = world.spawn_gameobject()
    assert world.has_gameobject(g2.id) is True
    world.delete_gameobject(g2.id)
    world.step()
    assert world.has_gameobject(g2.id) is False

    # Ensure that GameObjects that are empty, but
    # once held components are properly removed
    g3 = world.spawn_gameobject([A()])
    assert g3.has_component(A) is True
    g3.remove_component(A)
    assert g3.has_component(A) is True
    assert world.has_gameobject(g3.id) is True
    world.step()
    assert g3.has_component(A) is False
    # When you remove the last component from an entity,
    # it technically does not exist within esper anymore
    assert world.ecs.entity_exists(g3.id) is False
    world.delete_gameobject(g3.id)
    world.step()
    assert world.has_gameobject(g3.id) is False


#########################################
# TEST WORLD COMPONENT-RELATED METHODS
#########################################


def test_world_get_component():
    world = World()
    world.spawn_gameobject([A()])
    world.spawn_gameobject([B()])
    world.spawn_gameobject([A(), B()])

    with_a = world.get_component(A)

    assert list(zip(*with_a))[0] == (1, 3)

    with_b = world.get_component(B)

    assert list(zip(*with_b))[0] == (2, 3)


def test_world_get_components():
    world = World()
    world.spawn_gameobject([A()])
    world.spawn_gameobject([B()])
    world.spawn_gameobject([A(), B()])

    with_a = world.get_components(A)

    assert list(zip(*with_a))[0] == (1, 3)

    with_b = world.get_components(B)

    assert list(zip(*with_b))[0] == (2, 3)


#########################################
# TEST WORLD SYSTEM-RELATED METHODS
#########################################


def test_world_add_get_system():
    world = World()

    assert world.get_system(FakeSystemBaseA) is None
    world.add_system(FakeSystemBaseA())
    assert world.get_system(FakeSystemBaseA) is not None


def test_world_remove_system():
    world = World()

    assert world.get_system(FakeSystemBaseA) is None
    world.add_system(FakeSystemBaseA())
    assert world.get_system(FakeSystemBaseA) is not None
    world.remove_system(FakeSystemBaseA)
    assert world.get_system(FakeSystemBaseA) is None


def test_world_step():
    world = World()
    world.add_system(FakeSystemBaseA())

    g1 = world.spawn_gameobject([A(1)])
    g2 = world.spawn_gameobject([A(2)])
    g3 = world.spawn_gameobject([A(3), B()])

    world.step()

    assert g1.get_component(A).value == 2
    assert g2.get_component(A).value == 3
    assert g3.get_component(A).value == 4


#########################################
# TEST WORLD RESOURCE-RELATED METHODS
#########################################


def test_get_all_resources():
    world = World()

    fake_resource = FakeResource()
    another_fake_resource = AnotherFakeResource

    world.add_resource(fake_resource)
    world.add_resource(another_fake_resource)

    assert world.get_all_resources() == [fake_resource, another_fake_resource]


def test_has_resource():
    world = World()
    assert world.has_resource(FakeResource) is False
    world.add_resource(FakeResource())
    assert world.has_resource(FakeResource) is True


def test_get_resource():
    world = World()
    fake_resource = FakeResource()
    assert world.has_resource(FakeResource) is False
    world.add_resource(fake_resource)
    assert world.get_resource(FakeResource) == fake_resource


def test_get_resource_raises_exception():
    """
    Test that the .get_resource(...) method throws
    a ResourceNotFoundError when attempting to get
    a resource that does not exist in the world instance.
    """
    world = World()
    with pytest.raises(ResourceNotFoundError):
        assert world.get_resource(FakeResource)


def test_remove_resource():
    world = World()
    world.add_resource(FakeResource())
    assert world.has_resource(FakeResource) is True
    world.remove_resource(FakeResource)
    assert world.has_resource(FakeResource) is False


def test_remove_resource_raises_exception():
    """
    Test that .remove_resource(...) method throws a
    ResourceNotFoundError when attempting to remove a
    resource that does not exist in the World instance.
    """
    world = World()
    with pytest.raises(ResourceNotFoundError):
        world.remove_resource(FakeResource)


def test_try_resource():
    world = World()

    assert world.try_resource(FakeResource) is None

    world.add_resource(FakeResource())

    assert world.try_resource(FakeResource) is not None


def test_add_resource():
    world = World()
    fake_resource = FakeResource()
    assert world.has_resource(FakeResource) is False
    world.add_resource(fake_resource)
    assert world.has_resource(FakeResource) is True


#########################################
# TEST GAMEOBJECT METHODS
#########################################


def test_add_component():
    world = World()
    g1 = world.spawn_gameobject()
    assert g1.has_component(A) is False
    g1.add_component(A())
    assert g1.has_component(A) is True


def test_get_component():
    world = World()
    a_component = A()
    g1 = world.spawn_gameobject([a_component])
    assert g1.get_component(A) == a_component


def test_get_component_raises_exception():
    with pytest.raises(ComponentNotFoundError):
        world = World()
        g1 = world.spawn_gameobject()
        g1.get_component(A)
        g1.get_component(B)


def test_remove_component():
    world = World()
    g1 = world.spawn_gameobject([A(), B()])
    assert g1.has_component(A) is True
    g1.remove_component(A)
    world.step()
    assert g1.has_component(A) is False


def test_try_component():
    world = World()
    g1 = world.spawn_gameobject()
    assert g1.try_component(A) is None
    g1.add_component(A())
    assert g1.try_component(A) is not None


def test_add_child():
    world = World()
    g1 = world.spawn_gameobject([A()])
    g2 = world.spawn_gameobject([B()])
    g1.add_child(g2)

    assert (g2 in g1.children) is True
    assert (g2.parent == g1) is True

    g3 = world.spawn_gameobject([A()])

    g3.add_child(g2)

    assert (g2 not in g1.children) is True
    assert (g2.parent != g1) is True
    assert (g2.parent == g3) is True
    assert (g2 in g3.children) is True


def test_remove_child():
    world = World()
    g1 = world.spawn_gameobject([A()])
    g2 = world.spawn_gameobject([B()])
    g3 = world.spawn_gameobject([B()])

    g1.add_child(g2)
    g1.add_child(g3)

    assert (g2 in g1.children) is True
    assert (g3 in g1.children) is True
    assert (g1 == g3.parent) is True

    g1.remove_child(g3)

    assert (g3 in g1.children) is False
    assert g3.parent is None


def test_remove_gameobject_with_children():
    world = World()

    g1 = world.spawn_gameobject([A()])
    g2 = world.spawn_gameobject([B()])
    g3 = world.spawn_gameobject([B()])
    g4 = world.spawn_gameobject([B()])
    g5 = world.spawn_gameobject([B()])

    g1.add_child(g2)
    g2.add_child(g3)
    g3.add_child(g4)
    g3.add_child(g5)

    # Removing g3 should remove g4 and g5
    assert world.has_gameobject(g3.id) is True
    assert world.has_gameobject(g4.id) is True
    assert world.has_gameobject(g5.id) is True

    world.delete_gameobject(g3.id)
    world.step()

    # Removing g3 should remove g4 and g5
    assert world.has_gameobject(g3.id) is False
    assert world.has_gameobject(g4.id) is False
    assert world.has_gameobject(g5.id) is False

    world.delete_gameobject(g2.id)
    world.step()

    assert world.has_gameobject(g2.id) is False
