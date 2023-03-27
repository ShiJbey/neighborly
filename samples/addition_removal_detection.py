"""
samples/addition_removal_detection

This sample script shows how simulation authors can detect when components are added
or removed. This may be helpful when you need to change the state of other components
based on the change in presence of another component
"""
from dataclasses import dataclass
from typing import Any, Dict

from neighborly import Component, Neighborly
from neighborly.core.ecs import (
    ComponentAddedEvent,
    ComponentRemovedEvent,
    Event,
    GameObject,
)
from neighborly.core.status import StatusManager
from neighborly.decorators import component

sim = Neighborly()


@component(sim)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim)
@dataclass
class AdventurerStats(Component):
    attack: int
    defense: int

    def to_dict(self) -> Dict[str, Any]:
        return {"attack": self.attack, "defense": self.defense}


@component(sim)
@dataclass()
class AttackBuff(Component):
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}


def handle_event(gameobject: GameObject, event: Event) -> None:
    print(f"{gameobject.name}: {str(type(event))}")


def on_attack_buff_added(gameobject: GameObject, event: ComponentAddedEvent) -> None:
    c = event.component
    if isinstance(c, AttackBuff):
        stats = gameobject.get_component(AdventurerStats)
        stats.attack += c.amount


def on_attack_buffer_removed(
    gameobject: GameObject, event: ComponentAddedEvent
) -> None:
    c = event.component
    if isinstance(c, AttackBuff):
        stats = gameobject.get_component(AdventurerStats)
        stats.attack -= c.amount


GameObject.on_any(handle_event)
GameObject.on(ComponentAddedEvent, on_attack_buff_added)
GameObject.on(ComponentRemovedEvent, on_attack_buffer_removed)


def main():
    alice = sim.world.spawn_gameobject(
        [Actor("Alice"), StatusManager(), AdventurerStats(5, 7)]
    )

    print(alice.get_component(AdventurerStats))

    alice.add_component(AttackBuff(10))

    sim.step()

    print(alice.get_component(AdventurerStats))

    alice.remove_component(AttackBuff)

    sim.step()

    print(alice.get_component(AdventurerStats))


if __name__ == "__main__":
    main()
