#!/usr/bin/python3

"""
Updated Event Role Authoring
============================

This sample shows how to author life events using the new @event_role decorator for
role binding functions. This new authoring workflow is intended to remove the need for
boilerplate code. And it allows us to repeatedly generate new valid castings for
life event types.

"""


from __future__ import annotations

from typing import Any, Dict, Generator, Tuple

from neighborly.ecs import Component, GameObject
from neighborly.life_event import (
    EventBindingContext,
    RandomLifeEvent,
    event_consideration,
    event_role,
)
from neighborly.simulation import Neighborly
from neighborly.stats import StatModifier, StatModifierType


class SpiderManBossFight(RandomLifeEvent):
    """Begins a story of a hero versus a villain."""

    base_probability = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return {
            **super().to_dict(),
            "hero": self.roles.get_first("hero").uid,
            "villain": self.roles.get_first("villain").uid,
        }

    def execute(self) -> None:
        pass

    @staticmethod
    @event_role("hero")
    def hero(
        ctx: EventBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a hero."""
        for guid, _ in ctx.world.get_component(Hero):
            yield (ctx.world.gameobject_manager.get_gameobject(guid),)

    @staticmethod
    @event_role("villain")
    def villain(
        ctx: EventBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a villain."""
        for guid, _ in ctx.world.get_component(Villain):
            yield (ctx.world.gameobject_manager.get_gameobject(guid),)

    @staticmethod
    @event_consideration()
    def universe_match_consideration(event: SpiderManBossFight) -> StatModifier:
        """Modify the probability based on the match-up."""

        if event["hero"].name == "Miles" and event["villain"].name == "The Prowler":
            return StatModifier(0.1, StatModifierType.Flat)

        elif event["hero"].name == "Peter" and event["villain"].name == "Green Goblin":
            return StatModifier(0.1, StatModifierType.Flat)

        elif event["hero"].name == "Gwen" and event["villain"].name == "Daredevil":
            return StatModifier(0.1, StatModifierType.Flat)

        else:
            return StatModifier(-0.5, StatModifierType.PercentAdd)


class Hero(Component):
    pass


class Villain(Component):
    pass


def main() -> None:
    sim = Neighborly()

    sim.world.gameobject_manager.register_component(Hero)
    sim.world.gameobject_manager.register_component(Villain)

    sim.world.gameobject_manager.spawn_gameobject(components={Hero: {}}, name="Miles")
    sim.world.gameobject_manager.spawn_gameobject(components={Hero: {}}, name="Peter")
    sim.world.gameobject_manager.spawn_gameobject(components={Hero: {}}, name="Gwen")

    sim.world.gameobject_manager.spawn_gameobject(
        components={Villain: {}}, name="Green Goblin"
    )
    sim.world.gameobject_manager.spawn_gameobject(
        components={Villain: {}}, name="The Prowler"
    )
    sim.world.gameobject_manager.spawn_gameobject(
        components={Villain: {}}, name="Daredevil"
    )

    for result in SpiderManBossFight.generate(sim.world):
        print(result.__repr__())
        print(f"Probability: {result.get_probability()}")
        print("===")


if __name__ == "__main__":
    main()
