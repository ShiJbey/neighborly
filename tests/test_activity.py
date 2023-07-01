"""Test Activity-related components.

"""
import pytest

from neighborly.components.activity import (
    Activities,
    ActivityLibrary,
    register_activity_type,
)
from neighborly.core.ecs import GameObjectPrefab
from neighborly.factories.activity import ActivitiesFactory
from neighborly.simulation import Neighborly

# Create prefabs for activity types
RUNNING = GameObjectPrefab(
    name="Running", components={"ActivityType": {}, "Name": {"value": "Running"}}
)
EATING = GameObjectPrefab(
    name="Eating", components={"ActivityType": {}, "Name": {"value": "Eating"}}
)
DRINKING = GameObjectPrefab(
    name="Drinking", components={"ActivityType": {}, "Name": {"value": "Drinking"}}
)
SOCIALIZING = GameObjectPrefab(
    name="Socializing",
    components={"ActivityType": {}, "Name": {"value": "Socializing"}},
)
SHOPPING = GameObjectPrefab(
    name="Shopping",
    components={"ActivityType": {}, "Name": {"value": "Shopping"}},
)


def test_register_activity_type() -> None:
    """
    This test ensures that activity type prefabs are properly loaded into the
    world's GameObject manager.
    """
    sim = Neighborly()

    register_activity_type(sim.world, RUNNING)
    register_activity_type(sim.world, EATING)
    register_activity_type(sim.world, DRINKING)

    assert sim.world.gameobject_manager.get_prefab("Running") == RUNNING
    assert sim.world.gameobject_manager.get_prefab("Eating") == EATING
    assert sim.world.gameobject_manager.get_prefab("Drinking") == DRINKING


def test_instantiate_activities_system() -> None:
    """
    This test ensures that the activity types are properly constructed at
    the beginning of the first call to step() as part of its
    Initialization system group.
    """

    sim = Neighborly()
    activity_library = sim.world.resource_manager.get_resource(ActivityLibrary)

    register_activity_type(sim.world, RUNNING)
    register_activity_type(sim.world, EATING)
    register_activity_type(sim.world, DRINKING)

    # All activities are instantiated at the beginning of the first simulation step
    sim.step()

    assert activity_library.get("Running").name == "Running"
    assert activity_library.get("Eating").name == "Eating"
    assert activity_library.get("Drinking").name == "Drinking"

    with pytest.raises(KeyError):
        assert activity_library.get("Socializing")


def test_activity_factory() -> None:
    """
    This test ensures that the ActivityFactory class successfully constructs new
    Activity classes.

    We have to construct the instances after calling sim.step() because ActivityType
    GameObject instances are not constructed until the world's InitializationSystemGroup
    runs.
    """
    sim = Neighborly()
    activity_library = sim.world.resource_manager.get_resource(ActivityLibrary)

    register_activity_type(sim.world, RUNNING)
    register_activity_type(sim.world, EATING)
    register_activity_type(sim.world, DRINKING)
    register_activity_type(sim.world, SOCIALIZING)

    # All activities are instantiated at the beginning of the first simulation step
    sim.step()

    # Get references to the constructed instances
    running_type = activity_library.get("Running")
    socializing_type = activity_library.get("Socializing")
    drinking_type = activity_library.get("Drinking")

    factory = ActivitiesFactory()

    activities_component: Activities = factory.create(
        sim.world, activities=["Running", "Socializing"]
    )

    assert running_type in activities_component
    assert socializing_type in activities_component
    assert drinking_type not in activities_component


def test_activities_contains() -> None:
    sim = Neighborly()

    register_activity_type(sim.world, RUNNING)
    register_activity_type(sim.world, EATING)
    register_activity_type(sim.world, DRINKING)
    register_activity_type(sim.world, SOCIALIZING)
    register_activity_type(sim.world, SHOPPING)

    sim.step()

    activity_library = sim.world.resource_manager.get_resource(ActivityLibrary)

    drinking = activity_library.get("Drinking")
    eating = activity_library.get("Eating")
    running = activity_library.get("Running")
    shopping = activity_library.get("Shopping")
    socializing = activity_library.get("Socializing")

    activities_component = Activities(
        {
            drinking,
            eating,
            running,
        }
    )

    assert drinking in activities_component
    assert eating in activities_component
    assert shopping not in activities_component
    assert socializing not in activities_component
