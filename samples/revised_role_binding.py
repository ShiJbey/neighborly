from __future__ import annotations

from typing import Generator, Optional, Tuple

from neighborly.core.ecs import Component, GameObject
from neighborly.core.life_event import (
    EventRoleBindingContext,
    RandomLifeEvent,
    event_role,
)
from neighborly.simulation import Neighborly


def sample_consideration(
    gameobject: GameObject, event: StartHeroStory
) -> Optional[float]:
    return 0.1


class StartHeroStory(RandomLifeEvent):
    """Begins a story of a hero versus a villain."""

    def execute(self) -> None:
        pass

    @staticmethod
    @event_role("hero", considerations=[lambda gameobject, event: 0.8])
    def hero(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a hero."""
        for guid, _ in ctx.world.get_component(Hero):
            yield (ctx.world.gameobject_manager.get_gameobject(guid),)

    @staticmethod
    @event_role("villain", considerations=[sample_consideration])
    def villain(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a villain."""
        for guid, _ in ctx.world.get_component(Villain):
            yield (ctx.world.gameobject_manager.get_gameobject(guid),)


class Hero(Component):
    pass


class Villain(Component):
    pass


def main() -> None:
    sim = Neighborly()

    sim.world.gameobject_manager.spawn_gameobject([Hero()], name="Miles")
    sim.world.gameobject_manager.spawn_gameobject([Hero()], name="Peter")
    sim.world.gameobject_manager.spawn_gameobject([Hero()], name="Gwen")

    sim.world.gameobject_manager.spawn_gameobject([Villain()], name="KingPin")
    sim.world.gameobject_manager.spawn_gameobject([Villain()], name="Green Goblin")
    sim.world.gameobject_manager.spawn_gameobject([Villain()], name="The Prowler")
    sim.world.gameobject_manager.spawn_gameobject([Villain()], name="Doc. Oc")

    for result in StartHeroStory.generate(sim.world):
        print(result.__repr__())
        print(f"Probability: {result.get_probability()}")
        print("===")


if __name__ == "__main__":
    main()
