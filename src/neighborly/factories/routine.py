from typing import Any

from neighborly.components.routine import Routine, RoutineEntry
from neighborly.core.ecs import IComponentFactory, World
from neighborly.core.time import Weekday


class RoutineFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Routine:
        routine = Routine()

        presets = kwargs.get("presets")

        if presets == "default":
            at_home = RoutineEntry(20, 8, "home")
            routine.add_entries(
                "at_home_default", [d.value for d in list(Weekday)], at_home
            )

        return routine
