"""Tests utility functions in neighborly.utils.common.

"""

from neighborly.components.shared import FrequentedBy, FrequentedLocations, Location
from neighborly.simulation import Neighborly
from neighborly.utils.common import clear_frequented_locations


def test_clear_frequented_locations() -> None:
    sim = Neighborly()

    jon = sim.world.gameobject_manager.spawn_gameobject(
        components={FrequentedLocations: {}},
        name="Jon",
    )

    gym = sim.world.gameobject_manager.spawn_gameobject(
        components={Location: {}, FrequentedBy: {}},
        name="Gym",
    )

    grocery_store = sim.world.gameobject_manager.spawn_gameobject(
        components={Location: {}, FrequentedBy: {}},
        name="Grocery Store",
    )

    office_building = sim.world.gameobject_manager.spawn_gameobject(
        components={Location: {}, FrequentedBy: {}},
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
