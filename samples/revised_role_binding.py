from __future__ import annotations

from typing import Generator, Optional, Tuple

from neighborly import World
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


# noinspection PyNestedDecorators
class StartHeroStory(RandomLifeEvent):
    """Begins a story of a hero versus a villain."""

    def execute(self, world: World) -> None:
        pass

    @event_role(considerations=[lambda gameobject, event: 0.8])
    @staticmethod
    def hero(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a hero."""
        for guid, _ in ctx.world.get_component(Hero):
            yield (ctx.world.get_gameobject(guid),)

    @event_role(considerations=[sample_consideration])
    @staticmethod
    def villain(
        ctx: EventRoleBindingContext,
    ) -> Generator[Tuple[GameObject, ...], None, None]:
        """Bind a villain."""
        for guid, _ in ctx.world.get_component(Villain):
            yield (ctx.world.get_gameobject(guid),)


class Hero(Component):
    pass


class Villain(Component):
    pass


def main() -> None:
    sim = Neighborly()

    sim.world.spawn_gameobject([Hero()], name="Miles")
    sim.world.spawn_gameobject([Hero()], name="Peter")
    sim.world.spawn_gameobject([Hero()], name="Gwen")

    sim.world.spawn_gameobject([Villain()], name="KingPin")
    sim.world.spawn_gameobject([Villain()], name="Green Goblin")
    sim.world.spawn_gameobject([Villain()], name="The Prowler")
    sim.world.spawn_gameobject([Villain()], name="Doc. Oc")

    for result in StartHeroStory.generate(sim.world):
        print(result.__repr__())
        print(f"Probability: {result.get_probability()}")
        print("===")


if __name__ == "__main__":
    main()
