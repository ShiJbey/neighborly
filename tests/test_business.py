"""
Tests for the Neighborly's Business and Occupation logic
"""

import pytest

from neighborly.components.business import (
    BaseBusiness,
    Business,
    BusinessConfig,
    Occupation,
    Services,
    ServiceType,
)
from neighborly.simulation import Neighborly


class Cook(Occupation):
    pass


class Restaurateur(Occupation):
    pass


class Server(Occupation):
    pass


class Host(Occupation):
    pass


class Restaurant(BaseBusiness):
    config = BusinessConfig(
        owner_type=Restaurateur, employee_types={Cook: 1, Server: 2, Host: 1}
    )


@pytest.fixture
def test_sim():
    sim = Neighborly()

    sim.world.gameobject_manager.register_component(Restaurateur)
    sim.world.gameobject_manager.register_component(Cook)
    sim.world.gameobject_manager.register_component(Server)
    sim.world.gameobject_manager.register_component(Host)
    sim.world.gameobject_manager.register_component(Restaurant)

    return sim


def test_construct_business(test_sim: Neighborly):
    """Constructing business components using BusinessArchetypes"""
    restaurant = Restaurant._instantiate(test_sim.world, lot=(0, 0))
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == Restaurateur
    assert restaurant_business.owner is None


def test_services_contains() -> None:
    sim = Neighborly()

    gameobject = sim.world.gameobject_manager.spawn_gameobject()

    services_component = gameobject.add_component(Services, services=["Food", "Retail"])

    assert ServiceType.Food in services_component
    assert ServiceType.Retail in services_component
    assert ServiceType.ChildCare not in services_component
