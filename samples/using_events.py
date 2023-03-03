#!/usr/bin/env python3

"""
samples/using_events.py

Events are core to the reactivity of the simulation. They alert other systems that
something significant has occurred. Simulation authors can tap into these events
to make cascading effects.

In this example, we add one character to the simulation and track the amount of money
they have. When they accumulate enough money from their job, we emit an event
saying they became a millionaire. We then read that event in another system that
decrements money from the character (presumably because they need to pay taxes).

Events disappear at the end of the timestep. So, the event will not fire again until
the character has enough money.
"""
from dataclasses import dataclass
from typing import Any, Dict

from neighborly import (
    Component,
    GameObject,
    ISystem,
    Neighborly,
    NeighborlyConfig,
    SimDateTime,
)
from neighborly.core.event import Event, EventBuffer
from neighborly.decorators import component, system

sim = Neighborly(NeighborlyConfig(verbose=False))


@component(sim)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim)
@dataclass
class Money(Component):
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}


@component(sim)
@dataclass
class Job(Component):
    title: str
    salary: int

    def to_dict(self) -> Dict[str, Any]:
        return {"title": self.title, "salary": self.salary}


@system(sim)
class SalarySystem(ISystem):
    sys_group = "character-update"

    def process(self, *args: Any, **kwargs: Any):
        for _, (actor, job, money) in self.world.get_components((Actor, Job, Money)):
            money.amount += job.salary // 12
            print(f"{actor.name} has ${money.amount}.")


@system(sim)
class BecomeMillionaireEventSystem(ISystem):

    sys_group = "character-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for guid, money in self.world.get_component(Money):
            character = self.world.get_gameobject(guid)
            if money.amount > 1_000_000:
                self.world.get_resource(EventBuffer).append(
                    BecomeMillionaireEvent(
                        self.world.get_resource(SimDateTime), character
                    )
                )


class BecomeMillionaireEvent(Event):
    def __init__(self, date: SimDateTime, character: GameObject) -> None:
        super().__init__(date)
        self.character: GameObject = character


@system(sim)
class OnBecomeMillionaireSystem(ISystem):

    sys_group = "event-listeners"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for event in self.world.get_resource(EventBuffer).iter_events_of_type(
            BecomeMillionaireEvent
        ):
            actor = event.character.get_component(Actor)
            print(f"{actor.name} became a millionaire. Here comes the IRS")
            event.character.get_component(Money).amount -= 750_000


def main():
    sim.world.spawn_gameobject([Actor("Alice"), Money(0), Job("Intern", 1_000_000)])

    for _ in range(24):
        sim.step()


if __name__ == "__main__":
    main()
