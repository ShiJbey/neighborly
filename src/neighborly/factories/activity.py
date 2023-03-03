from __future__ import annotations

from typing import Any, List, Optional

from neighborly.components.activity import Activities
from neighborly.content_management import ActivityLibrary
from neighborly.core.ecs import IComponentFactory, World


class ActivitiesFactory(IComponentFactory):
    """Creates Activities component instances"""

    def create(
        self, world: World, activities: Optional[List[str]] = None, **kwargs: Any
    ) -> Activities:

        activity_library = world.get_resource(ActivityLibrary)

        activity_names: List[str] = activities if activities else []

        return Activities(set([activity_library.get(name) for name in activity_names]))
