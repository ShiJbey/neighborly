"""
samples/addition_removal_detection

This sample script shows how simulation authors can detect when components are added
or removed. This may be helpful when you need to change the state of other components
based on the change in presence of another component
"""
from dataclasses import dataclass
from typing import Any, Dict

from neighborly import Component, ISystem, Neighborly
from neighborly.core.status import StatusManager
from neighborly.decorators import component, system

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


@system(sim)
class OnAddAttackBuff(ISystem):
    sys_group = "late-character-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for guid in self.world.iter_added_component(AttackBuff):
            character = self.world.get_gameobject(guid)
            stats = character.get_component(AdventurerStats)
            stats.attack += character.get_component(AttackBuff).amount


@system(sim)
class OnRemoveAttackBuff(ISystem):
    sys_group = "late-character-update"

    def process(self, *args: Any, **kwargs: Any) -> None:
        for pair in self.world.iter_removed_component(AttackBuff):
            character = self.world.get_gameobject(pair.guid)
            stats = character.get_component(AdventurerStats)
            stats.attack -= pair.component.amount


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
