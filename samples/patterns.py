"""
In this file, I am messing around with using generator functions
to handle things like pattern matching in LifeEventRules and
timestep sizes when handling level-of-detail changes
"""
from abc import abstractmethod
from typing import Generator, List, Protocol, Tuple
from dataclasses import dataclass
from neighborly.core.ecs import GameObject, Component
from neighborly.core.life_event import (
    ILifeEventListener,
    LifeEvent,
    check_gameobject_preconditions,
    handle_gameobject_effects,
)


class IPatternFn(Protocol):
    @abstractmethod
    def __call__(
        self, world: List[GameObject]
    ) -> Generator[Tuple[LifeEvent, Tuple[GameObject, ...]], None, None]:
        raise NotImplementedError()


class TestEvent(LifeEvent):

    event_type: str = "test-event"

    def __init__(self, timestamp: str) -> None:
        super().__init__(timestamp)

    @classmethod
    def get_type(cls) -> str:
        return cls.event_type


def strength_greater_than(value: int) -> IPatternFn:
    def pattern(
        world: List[GameObject],
    ):
        for g in world:
            if g.has_component(A) and g.get_component(A).strength > value:
                yield TestEvent("now"), (g,)

    return pattern


strength_greater_than_10 = strength_greater_than(10)


@dataclass
class A(Component, ILifeEventListener):
    strength: int = 0

    def handle_event(self, event: LifeEvent) -> bool:
        if event.get_type() == "test-event":
            print("Handling works")
        return True

    def check_preconditions(self, event: LifeEvent) -> bool:
        print("Pizza")
        return True


@dataclass
class B(Component):
    health: int = 0


def main():
    world = [
        GameObject(components=[A()]),
        GameObject(components=[A(11), B(10)]),
        GameObject(components=[A(25)]),
    ]

    for event, participants in strength_greater_than_10(world):
        preconditions_pass = all(
            [check_gameobject_preconditions(g, event) for g in participants]
        )
        if preconditions_pass:
            for g in participants:
                handle_gameobject_effects(g, event)


if __name__ == "__main__":
    main()
