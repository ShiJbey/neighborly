"""
Tests for the Neighborly's Business and Occupation logic
"""

import pytest

from neighborly.components.business import (
    Business,
    Occupation,
    Services,
    register_occupation_type,
)
from neighborly.core.ecs import GameObjectPrefab
from neighborly.factories.business import ServicesFactory
from neighborly.simulation import Neighborly


class Cook(Occupation):
    pass


class Restaurateur(Occupation):
    pass


class Server(Occupation):
    pass


class Host(Occupation):
    pass


@pytest.fixture
def test_sim():
    sim = Neighborly()

    sim.world.gameobject_manager.add_prefab(
        GameObjectPrefab(
            name="Restaurant",
            components={
                "Name": {"value": "Restaurant"},
                "Business": {
                    "owner_type": "Restaurateur",
                    "employee_types": {
                        "Cook": 1,
                        "Server": 2,
                        "Host": 1,
                    },
                },
            },
        )
    )

    register_occupation_type(sim.world, Restaurateur)
    register_occupation_type(sim.world, Cook)
    register_occupation_type(sim.world, Server)
    register_occupation_type(sim.world, Host)

    return sim


def test_construct_business(test_sim: Neighborly):
    """Constructing business components using BusinessArchetypes"""
    restaurant = test_sim.world.gameobject_manager.instantiate_prefab("Restaurant")
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == Restaurateur
    assert restaurant_business.owner is None


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
