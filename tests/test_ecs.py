from dataclasses import dataclass

from neighborly.core.ecs import Component, GameObject, World


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


def test_gameobject() -> None:
    world = World()

    adrian = GameObject(
        components=[SimpleGameCharacter("Adrian"), SimpleRoutine(False)]
    )

    jamie = GameObject(components=[SimpleGameCharacter("Jamie"), SimpleRoutine(False)])

    park = GameObject(name="Park", components=[SimpleLocation()])

    office_building = GameObject(
        name="Office Building", components=[SimpleLocation(18)]
    )

    world.add_gameobject(adrian)
    world.add_gameobject(jamie)
    world.add_gameobject(park)
    world.add_gameobject(office_building)

    assert jamie.get_component(SimpleGameCharacter).name == "Jamie"

    assert len(world.get_component(SimpleGameCharacter)) == 2
    assert len(world.get_component(SimpleLocation)) == 2

    assert park.get_component(SimpleLocation).capacity == 999
    assert office_building.get_component(SimpleLocation).capacity == 18

    assert len(world.get_components(SimpleGameCharacter, SimpleRoutine)) == 2
