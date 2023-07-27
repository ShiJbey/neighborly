"""
samples/addition_removal_detection

This sample script shows how simulation authors can detect when components are added
or removed. This may be helpful when you need to change the state of other components
based on the change in presence of another component. In this example, we add and remove
a status buffer on the character.

Adding new components triggers a ComponentAddedEvent, and we can use the info inside
the event to make changes.
"""
from dataclasses import dataclass
from typing import Any, Dict

from neighborly import Component, Neighborly
from neighborly.core.ecs import GameObject
from neighborly.decorators import component
from neighborly.stat_system import StatComponent, StatModifier, StatModifierType
from neighborly.status_system import Statuses

sim = Neighborly()


@component(sim.world)
@dataclass
class Actor(Component):
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name}


@component(sim.world)
class Attack(StatComponent):
    pass


@component(sim.world)
@dataclass
class AttackBuff(Component):
    amount: int

    def to_dict(self) -> Dict[str, Any]:
        return {"amount": self.amount}

    def on_add(self, gameobject: GameObject) -> None:
        gameobject.get_component(Attack).add_modifier(
            StatModifier(
                modifier_type=StatModifierType.Flat, value=self.amount, source=self
            )
        )

    def on_remove(self, gameobject: GameObject) -> None:
        gameobject.get_component(Attack).remove_modifiers_from_source(self)


def main():
    alice = sim.world.gameobject_manager.spawn_gameobject(
        components={Actor: {"name": "Alice"}, Statuses: {}, Attack: {}}
    )

    print(alice.get_component(Attack))

    alice.add_component(AttackBuff, amount=10)

    print(alice.get_component(Attack))

    alice.remove_component(AttackBuff)

    print(alice.get_component(Attack))


if __name__ == "__main__":
    main()
