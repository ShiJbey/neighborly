"""
In this file, I am messing around with using generator functions
to handle things like pattern matching in LifeEventRules and
timestep sizes when handling level-of-detail changes
"""
from __future__ import annotations

from abc import abstractmethod
from typing import Generator, Optional, Protocol
from dataclasses import dataclass
from neighborly.core.time import SimDateTime
from neighborly.core.ecs import GameObject, Component
from neighborly.core.life_event import (
    ILifeEventListener,
    LifeEvent,
    check_gameobject_preconditions,
    handle_gameobject_effects,
)


def custom_range(max: int) -> Generator[int, None, None]:
    i = 0
    while i < max:
        yield i
        i += 1


def print_custom_range(max: int) -> None:
    for x in custom_range(max):
        print(x)


def variable_lod(
    date_time: SimDateTime,
    low_lod_step: int,
    high_lod_step: int,
    days_per_year: int,
    end_date: Optional[str] = None,
) -> Generator[int, None, None]:
    """
    Yields time step increments based on the current date,
    switching between low and high levels-of-detail.
    """
    ...


class IPatternFn(Protocol):
    @abstractmethod
    def __call__(
        self, world: list[GameObject]
    ) -> Generator[tuple[LifeEvent, tuple[GameObject, ...]], None, None]:
        raise NotImplementedError()


def strength_greater_than(value: int) -> IPatternFn:
    def pattern(
        world: list[GameObject],
    ):
        for g in world:
            if g.has_component(A) and g.get_component(A).strength > value:
                yield LifeEvent("test_event", ""), (g,)

    return pattern


strength_greater_than_10 = strength_greater_than(10)


@dataclass
class A(Component, ILifeEventListener):
    strength: int = 0

    def handle_event(self, event: LifeEvent) -> bool:
        if event.event_type == "test_event":
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
