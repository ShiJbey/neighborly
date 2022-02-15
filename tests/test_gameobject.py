from dataclasses import dataclass

from neighborly.core.ecs import World, GameObject, Component


class TestGameCharacter(Component):

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def on_add(self) -> None:
        self.gameobject.set_name(self.name)

    def __repr__(self) -> str:
        return f"GameCharacter(name={self.name})"


class TestBuilding(Component):
    __slots__ = "size", "capacity"

    def __init__(self, size: str) -> None:
        super().__init__()
        self.size: str = size
        if size == 'large':
            self.capacity = 36
        elif size == 'medium':
            self.capacity = 18
        elif size == 'small':
            self.capacity = 8
        else:
            raise ValueError("Invalid building size")

    def on_start(self) -> None:
        location = self.gameobject.get_component(TestLocation)
        location.capacity = self.capacity

    def __repr__(self) -> str:
        return f"Building(size={self.size}, capacity={self.capacity})"


class TestLocation(Component):
    __slots__ = "capacity"

    def __init__(self, capacity: int = 999) -> None:
        super().__init__()
        self.capacity: int = capacity

    def __repr__(self) -> str:
        return f"Location(capacity={self.capacity})"


@dataclass
class TestRoutine(Component):
    free: bool


def test_gameobject() -> None:
    world = World()

    adrian = GameObject(
        components=[TestGameCharacter("Adrian"), TestRoutine(False)])

    jamie = GameObject(
        components=[TestGameCharacter("Jamie"), TestRoutine(False)])

    park = GameObject(name="Park", components=[TestLocation()])

    office_building = GameObject(name="Office Building", components=[
        TestLocation(), TestBuilding("medium")])

    world.add_gameobject(adrian)
    world.add_gameobject(jamie)
    world.add_gameobject(park)
    world.add_gameobject(office_building)

    assert jamie.name == "Jamie"
    assert jamie.get_component(TestGameCharacter).name == "Jamie"

    assert len(world.get_component(TestGameCharacter)) == 2
    assert len(world.get_component(TestLocation)) == 2

    assert park.get_component(TestLocation).capacity == 999
    assert office_building.get_component(TestLocation).capacity == 18

    assert len(world.get_components(TestGameCharacter, TestRoutine)) == 2
