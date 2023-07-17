"""Tests utility functions in neighborly.utils.common.

"""
from neighborly.components.character import GameCharacter
from neighborly.components.shared import (
    CurrentSettlement,
    FrequentedBy,
    FrequentedLocations,
    Location,
)
from neighborly.core.settlement import Settlement
from neighborly.simulation import Neighborly
from neighborly.utils.common import (
    add_location_to_settlement,
    clear_frequented_locations,
    remove_location_from_settlement,
)
from neighborly.utils.location import add_sub_location, remove_sub_location


def test_add_sub_location() -> None:
    sim = Neighborly()

    city = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="City",
    )

    city_hall = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="City Hall",
    )

    add_sub_location(parent_location=city, sub_location=city_hall)

    assert city_hall in city.children
    assert city_hall in city.get_component(Location).children
    assert city_hall.parent == city
    assert city_hall.get_component(Location).parent == city


def test_remove_sub_location() -> None:
    sim = Neighborly()

    city = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="City",
    )

    city_hall = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="City Hall",
    )

    add_sub_location(parent_location=city, sub_location=city_hall)

    assert city_hall in city.get_component(Location).children
    assert city_hall.get_component(Location).parent == city

    remove_sub_location(city, city_hall)

    assert city_hall not in city.get_component(Location).children
    assert city_hall.get_component(Location).parent is None


def test_add_location_to_settlement() -> None:
    sim = Neighborly()

    jasmine_dragon = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="The Jasmine Dragon Tea Shop",
    )

    ba_sing_se = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
            sim.world.gameobject_manager.create_component(
                Settlement, width=10, length=10
            ),
        ],
        name="Ba Sing Se",
    )

    add_location_to_settlement(jasmine_dragon, ba_sing_se)

    assert jasmine_dragon.get_component(CurrentSettlement).settlement == ba_sing_se
    assert jasmine_dragon in ba_sing_se.children
    assert jasmine_dragon.parent == ba_sing_se
    assert jasmine_dragon.get_component(Location).parent == ba_sing_se
    assert jasmine_dragon in ba_sing_se.get_component(Location).children


def test_remove_location_from_settlement() -> None:
    sim = Neighborly()

    jasmine_dragon = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
        ],
        name="The Jasmine Dragon Tea Shop",
    )

    ba_sing_se = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
            sim.world.gameobject_manager.create_component(
                Settlement, width=10, length=10
            ),
        ],
        name="Ba Sing Se",
    )

    add_location_to_settlement(location=jasmine_dragon, settlement=ba_sing_se)

    assert jasmine_dragon.get_component(CurrentSettlement).settlement == ba_sing_se
    assert jasmine_dragon.get_component(Location).parent == ba_sing_se
    assert jasmine_dragon in ba_sing_se.get_component(Location).children

    remove_location_from_settlement(location=jasmine_dragon, settlement=ba_sing_se)

    assert jasmine_dragon.has_component(CurrentSettlement) is False
    assert jasmine_dragon.get_component(Location).parent is None
    assert jasmine_dragon not in ba_sing_se.get_component(Location).children


def test_clear_frequented_locations() -> None:
    sim = Neighborly()

    jon = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(
                GameCharacter, first_name="Jon", last_name="Black"
            ),
            sim.world.gameobject_manager.create_component(FrequentedLocations),
        ],
        name="Jon",
    )

    gym = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
            sim.world.gameobject_manager.create_component(FrequentedBy),
        ],
        name="Gym",
    )

    grocery_store = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
            sim.world.gameobject_manager.create_component(FrequentedBy),
        ],
        name="Grocery Store",
    )

    office_building = sim.world.gameobject_manager.spawn_gameobject(
        components=[
            sim.world.gameobject_manager.create_component(Location),
            sim.world.gameobject_manager.create_component(FrequentedBy),
        ],
        name="Office Building",
    )

    jon.get_component(FrequentedLocations).add(gym)
    gym.get_component(FrequentedBy).add(jon)
    jon.get_component(FrequentedLocations).add(office_building)
    office_building.get_component(FrequentedBy).add(jon)
    jon.get_component(FrequentedLocations).add(grocery_store)
    grocery_store.get_component(FrequentedBy).add(jon)

    assert len(jon.get_component(FrequentedLocations)) == 3
    assert grocery_store in jon.get_component(FrequentedLocations)
    assert jon in gym.get_component(FrequentedBy)
    assert jon in grocery_store.get_component(FrequentedBy)
    assert jon in office_building.get_component(FrequentedBy)

    clear_frequented_locations(jon)

    assert len(jon.get_component(FrequentedLocations)) == 0
    assert jon not in gym.get_component(FrequentedBy)
    assert jon not in grocery_store.get_component(FrequentedBy)
    assert jon not in office_building.get_component(FrequentedBy)
