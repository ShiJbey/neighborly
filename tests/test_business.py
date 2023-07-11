"""
Tests for the Neighborly's Business and Occupation logic
"""

from typing import Any

from neighborly.components.business import Business, Services
from neighborly.components.character import GameCharacter, Gender, GenderType
from neighborly.components.shared import Age
from neighborly.core.ecs import Component, GameObject, GameObjectPrefab
from neighborly.factories.business import ServicesFactory
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
            },
        )
    )

    restaurant = sim.world.gameobject_manager.instantiate_prefab("Restaurant")
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == "Proprietor"
    assert restaurant_business.owner is None


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


def test_services_factory() -> None:
    """
    This test ensures that the ServicesFactory class successfully constructs new
    Services classes.

    We have to construct the instances after calling sim.step() because ServiceType
    GameObject instances are not constructed until the world's InitializationSystemGroup
    runs.
    """
    sim = Neighborly()

    # Get references to the constructed instances
    factory = ServicesFactory()

    services_component: Services = factory.create(
        sim.world, services=["Running", "Socializing"]
    )

    assert "Running" in services_component
    assert "Socializing" in services_component
    assert "Drinking" not in services_component


def test_services_contains() -> None:
    services_component = Services(
        [
            "drinking",
            "eating",
            "running",
        ]
    )

    assert "drinking" in services_component
    assert "eating" in services_component
    assert "shopping" not in services_component
    assert "socializing" not in services_component
