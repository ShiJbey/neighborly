"""
Tests for the Neighborly's Business and Occupation logic
"""

from typing import Any

import pytest

from neighborly.components.business import (
    Business,
    JobRequirementLibrary,
    JobRequirementParser,
    register_service_type,
    ServiceLibrary,
    Services,
)
from neighborly.components.character import GameCharacter, Gender, GenderType
from neighborly.components.shared import Age
from neighborly.core.ecs import Component, GameObject, GameObjectPrefab
from neighborly.factories.business import ServicesFactory
from neighborly.plugins.talktown.school import CollegeGraduate
from neighborly.simulation import Neighborly


def test_construct_business():
    """Constructing business components using BusinessArchetypes"""

    sim = Neighborly()

    sim.world.gameobject_manager.add_prefab(
        GameObjectPrefab(
            name="Restaurant",
            components={
                "Name": {"value": "Restaurant"},
                "Business": {
                    "owner_type": "Proprietor",
                    "employee_types": {
                        "Cook": 1,
                        "Server": 2,
                        "Host": 1,
                    },
                },
                "OperatingHours": {"hours": "11AM - 10PM"},
            },
        )
    )

    restaurant = sim.world.gameobject_manager.instantiate_prefab("Restaurant")
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == "Proprietor"
    assert restaurant_business.owner is None
    assert restaurant_business.needs_owner() is True


def has_last_name(gameobject: GameObject, *args: Any):
    last_name: str
    (last_name,) = args

    if game_character := gameobject.try_component(GameCharacter):
        return game_character.last_name == last_name
    return False


def has_component(gameobject: GameObject, *args: Any) -> bool:
    component_name: str
    (component_name,) = args
    return gameobject.has_component(
        gameobject.world.gameobject_manager.get_component_info(
            component_name
        ).component_type
    )


def has_gender(gameobject: GameObject, *args: Any) -> bool:
    gender_name: str
    (gender_name,) = args
    if gender := gameobject.try_component(Gender):
        return gender.gender == GenderType[gender_name]
    return False


def over_age(gameobject: GameObject, *args: Any) -> bool:
    years: float
    (years,) = args
    if age := gameobject.try_component(Age):
        return age.value > years
    return False


class Cyborg(Component):
    pass


def test_parse_job_requirements():
    sim = Neighborly()
    library = JobRequirementLibrary()
    parser = JobRequirementParser(sim.world)

    sim.world.resource_manager.add_resource(library)

    sim.world.gameobject_manager.register_component(CollegeGraduate)
    sim.world.gameobject_manager.register_component(Cyborg)

    library.add("has_gender", has_gender)
    library.add("over_age", over_age)
    library.add("has_last_name", has_last_name)
    library.add("has_component", has_component)

    kieth = sim.world.gameobject_manager.spawn_gameobject(
        [GameCharacter("Kieth", "Smith"), Gender("Male"), Age(32)]
    )

    percy = sim.world.gameobject_manager.spawn_gameobject(
        [GameCharacter("Percy", "Jenkins"), Age(51), CollegeGraduate()]
    )

    dolph = sim.world.gameobject_manager.spawn_gameobject(
        [GameCharacter("Dolph", "McKnight"), Age(23), CollegeGraduate(), Cyborg()]
    )

    rule = parser.parse_string(
        "(OR (has_gender 'Male') (has_gender 'Female') (over_age 45))"
    )

    assert rule(kieth) is True
    assert rule(percy) is True
    assert rule(dolph) is False

    rule = parser.parse_string('(has_last_name "Smith")')

    assert rule(kieth) is True
    assert rule(percy) is False
    assert rule(dolph) is False

    rule = parser.parse_string(
        "(AND (has_component 'Cyborg') (has_component 'CollegeGraduate'))"
    )

    assert rule(kieth) is False
    assert rule(percy) is False
    assert rule(dolph) is True

    rule = parser.parse_string(
        "(OR (has_component 'Cyborg') (has_component 'CollegeGraduate'))"
    )

    assert rule(kieth) is False
    assert rule(percy) is True
    assert rule(dolph) is True

    parser.parse_string(
        """
    (OR
        (over_age 45)
        (AND
            (has_component 'Cyborg')
            (has_component 'CollegeGraduate')
        )
    )
    """
    )

    assert rule(kieth) is False
    assert rule(percy) is True
    assert rule(dolph) is True


# Create prefabs for service  types
RUNNING = GameObjectPrefab(
    name="Running", components={"ServiceType": {}, "Name": {"value": "Running"}}
)
EATING = GameObjectPrefab(
    name="Eating", components={"ServiceType": {}, "Name": {"value": "Eating"}}
)
DRINKING = GameObjectPrefab(
    name="Drinking", components={"ServiceType": {}, "Name": {"value": "Drinking"}}
)
SOCIALIZING = GameObjectPrefab(
    name="Socializing",
    components={"ServiceType": {}, "Name": {"value": "Socializing"}},
)
SHOPPING = GameObjectPrefab(
    name="Shopping",
    components={"ServiceType": {}, "Name": {"value": "Shopping"}},
)


def test_register_service_type() -> None:
    """
    This test ensures that service type prefabs are properly loaded into the
    world's GameObject manager.
    """
    sim = Neighborly()

    register_service_type(sim.world, RUNNING)
    register_service_type(sim.world, EATING)
    register_service_type(sim.world, DRINKING)

    assert sim.world.gameobject_manager.get_prefab("Running") == RUNNING
    assert sim.world.gameobject_manager.get_prefab("Eating") == EATING
    assert sim.world.gameobject_manager.get_prefab("Drinking") == DRINKING


def test_instantiate_services_system() -> None:
    """
    This test ensures that the service types are properly constructed at
    the beginning of the first call to step() as part of its
    Initialization system group.
    """

    sim = Neighborly()
    service_library = sim.world.resource_manager.get_resource(ServiceLibrary)

    register_service_type(sim.world, RUNNING)
    register_service_type(sim.world, EATING)
    register_service_type(sim.world, DRINKING)

    # All services are instantiated at the beginning of the first simulation step
    sim.step()

    assert service_library.get("Running").name == "Running"
    assert service_library.get("Eating").name == "Eating"
    assert service_library.get("Drinking").name == "Drinking"

    with pytest.raises(KeyError):
        assert service_library.get("Socializing")


def test_services_factory() -> None:
    """
    This test ensures that the ServicesFactory class successfully constructs new
    Services classes.

    We have to construct the instances after calling sim.step() because ServiceType
    GameObject instances are not constructed until the world's InitializationSystemGroup
    runs.
    """
    sim = Neighborly()

    service_library = sim.world.resource_manager.get_resource(ServiceLibrary)

    register_service_type(sim.world, RUNNING)
    register_service_type(sim.world, EATING)
    register_service_type(sim.world, DRINKING)
    register_service_type(sim.world, SOCIALIZING)

    # All service types are instantiated at the beginning of the first simulation step
    sim.step()

    # Get references to the constructed instances
    running_type = service_library.get("Running")
    socializing_type = service_library.get("Socializing")
    drinking_type = service_library.get("Drinking")

    factory = ServicesFactory()

    services_component: Services = factory.create(
        sim.world, services=["Running", "Socializing"]
    )

    assert running_type in services_component
    assert socializing_type in services_component
    assert drinking_type not in services_component


def test_services_contains() -> None:
    sim = Neighborly()

    register_service_type(sim.world, RUNNING)
    register_service_type(sim.world, EATING)
    register_service_type(sim.world, DRINKING)
    register_service_type(sim.world, SOCIALIZING)
    register_service_type(sim.world, SHOPPING)

    sim.step()

    service_library = sim.world.resource_manager.get_resource(ServiceLibrary)

    drinking = service_library.get("Drinking")
    eating = service_library.get("Eating")
    running = service_library.get("Running")
    shopping = service_library.get("Shopping")
    socializing = service_library.get("Socializing")

    services_component = Services(
        {
            drinking,
            eating,
            running,
        }
    )

    assert drinking in services_component
    assert eating in services_component
    assert shopping not in services_component
    assert socializing not in services_component
