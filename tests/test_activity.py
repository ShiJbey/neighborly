from neighborly.components.activity import Activities
from neighborly.content_management import ActivityLibrary
from neighborly.core.ecs import World
from neighborly.factories.activity import ActivitiesFactory


def test_get_activity_from_library() -> None:
    activity_library = ActivityLibrary()
    running = activity_library.get("Running")
    running_other = activity_library.get("running")
    eating = activity_library.get("Eating")

    assert running is running_other
    assert running.uid == 0
    assert eating.uid == 1
    assert eating.name == "eating"


def test_iterate_activity_library() -> None:
    activity_library = ActivityLibrary(
        ["Running", "Eating", "Drinking", "Socializing", "Shopping"]
    )

    all_activities = set([str(a) for a in activity_library])
    assert all_activities == {
        "running",
        "eating",
        "drinking",
        "socializing",
        "shopping",
    }


def test_activity_library_contains() -> None:
    activity_library = ActivityLibrary()
    activity_library.get("Running")
    activity_library.get("Eating")
    activity_library.get("Drinking")

    assert ("running" in activity_library) is True
    assert ("Eating" in activity_library) is True
    assert ("socializing" in activity_library) is False
    assert ("shopping" in activity_library) is False


def test_activities_contains() -> None:
    activity_library = ActivityLibrary()

    activity_manager = Activities(
        {
            activity_library.get("Running"),
            activity_library.get("Eating"),
            activity_library.get("Drinking"),
        }
    )

    assert activity_library.get("Drinking") in activity_manager
    assert activity_library.get("Shopping") not in activity_manager


def test_activities_to_dict() -> None:
    activity_library = ActivityLibrary()

    activity_manager = Activities(
        {
            activity_library.get("Running"),
            activity_library.get("Eating"),
            activity_library.get("Drinking"),
        }
    )

    assert activity_manager.to_dict() == {
        "activities": ["running", "eating", "drinking"]
    }


def test_activities_factory() -> None:
    world = World()

    activity_library = ActivityLibrary()

    world.add_resource(activity_library)

    factory = ActivitiesFactory()

    activity_manager: Activities = factory.create(
        world, activities=["Shopping", "Eating"]
    )

    assert activity_library.get("Drinking") not in activity_manager
    assert activity_library.get("Shopping") in activity_manager
    assert activity_library.get("Eating") in activity_manager
