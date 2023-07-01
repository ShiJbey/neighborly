from typing import Any

from neighborly.components.activity import Activities, ActivityLibrary
from neighborly.core.ecs import IComponentFactory, World


class ActivitiesFactory(IComponentFactory):
    def create(self, world: World, **kwargs: Any) -> Activities:
        activity_library = world.resource_manager.get_resource(ActivityLibrary)
        activities = [
            activity_library.get(activity_name)
            for activity_name in kwargs["activities"]
        ]
        return Activities(activities)
