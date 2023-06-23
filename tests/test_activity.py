from neighborly.components.activity import (
    Activities,
    ActivityLibrary,
    register_activity_type,
)
from neighborly.core.ecs import EntityPrefab
from neighborly.simulation import Neighborly


def test_activities_contains() -> None:
    sim = Neighborly()

    register_activity_type(
        sim.world, EntityPrefab(name="Running", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, EntityPrefab(name="Eating", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, EntityPrefab(name="Drinking", components={"ActivityType": {}})
    )
    register_activity_type(
        sim.world, EntityPrefab(name="Shopping", components={"ActivityType": {}})
    )

    activity_library = sim.world.get_resource(ActivityLibrary)

    drinking = activity_library.get("Drinking")
    eating = activity_library.get("Eating")
    running = activity_library.get("Running")
    shopping = activity_library.get("Shopping")

    activity_manager = Activities(
        {
            drinking,
            eating,
            running,
        }
    )

    assert drinking in activity_manager
    assert shopping not in activity_manager
