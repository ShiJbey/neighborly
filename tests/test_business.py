"""
Tests for the Neighborly's Business and Occupation logic
"""
from typing import Any, Dict

import pytest

from neighborly.builtin.archetypes import BaseBusinessArchetype
from neighborly.core.business import (
    Business,
    OccupationType,
    OccupationTypes,
    parse_operating_hour_str,
)
from neighborly.core.ecs import Component, GameObject, World
from neighborly.core.time import Weekday
from neighborly.plugins.talktown.business_components import Restaurant
from neighborly.simulation import SimulationBuilder


class CollegeGraduate(Component):
    pass


@pytest.fixture
def sample_occupation_types():
    def is_college_graduate(
        world: World, gameobject: GameObject, **kwargs: Any
    ) -> bool:
        return gameobject.has_component(CollegeGraduate)

    ceo_occupation_type = OccupationType("CEO", 5)

    return {"ceo": ceo_occupation_type}


def test_register_occupation_type(sample_occupation_types: Dict[str, OccupationType]):
    ceo_occupation_type = sample_occupation_types["ceo"]

    assert ceo_occupation_type.name == "CEO"
    assert ceo_occupation_type.level == 5

    OccupationTypes.add(ceo_occupation_type)

    assert ceo_occupation_type == OccupationTypes.get("CEO")


# def test_occupation(sample_occupation_types: Dict[str, OccupationType]):
#     OccupationTypeLibrary.add(sample_occupation_types["ceo"])
#
#     ceo = Occupation(OccupationTypeLibrary.get("CEO"), 1)
#
#     assert ceo.get_type().name == "CEO"
#     assert ceo.get_business() == 1
#     assert ceo.get_years_held() == 0
#
#     ceo.increment_years_held(0.5)
#
#     assert ceo.get_years_held() == 0
#
#     ceo.increment_years_held(0.5)
#
#     assert ceo.get_years_held() == 1
#


def test_construct_business():
    """Constructing business components using BusinessArchetypes"""
    restaurant_archetype = BaseBusinessArchetype(
        business_type=Restaurant,
        name_format="#restaurant_name#",
        hours="11AM - 10PM",
        owner_type="Proprietor",
        employee_types={
            "Cook": 1,
            "Server": 2,
            "Host": 1,
        },
    )

    sim = SimulationBuilder().build()

    restaurant = restaurant_archetype.create(world=sim.world)
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == "Proprietor"
    assert restaurant_business.owner is None
    assert restaurant_business.needs_owner() is True
    assert restaurant_business.operating_hours[Weekday.Monday] == (11, 22)


def test_parse_operating_hours_str():
    # Time Interval
    assert parse_operating_hour_str("00-11")[Weekday.Sunday] == (0, 11)
    assert parse_operating_hour_str("0-11")[Weekday.Monday] == (0, 11)
    assert parse_operating_hour_str("2-17")[Weekday.Tuesday] == (2, 17)
    assert parse_operating_hour_str("00-23")[Weekday.Wednesday] == (0, 23)
    assert parse_operating_hour_str("21-04")[Weekday.Thursday] == (21, 4)
    assert parse_operating_hour_str("23-06")[Weekday.Friday] == (23, 6)
    assert parse_operating_hour_str("23-5")[Weekday.Saturday] == (23, 5)

    # Time Interval Alias
    assert parse_operating_hour_str("day")[Weekday.Sunday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Monday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Tuesday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Wednesday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Thursday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Friday] == (8, 11)
    assert parse_operating_hour_str("day")[Weekday.Saturday] == (8, 11)

    # Days + Time Interval
    assert parse_operating_hour_str("MT: 08-11")[Weekday.Monday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("MT: 08-11")[Weekday.Wednesday] == (8, 11)

    assert parse_operating_hour_str("WMF: 8-11")[Weekday.Friday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("MWF: 8-11")[Weekday.Tuesday] == (8, 11)

    assert parse_operating_hour_str("SU: 08 - 11")[Weekday.Sunday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("SU: 8 - 11")[Weekday.Friday] == (8, 11)

    assert parse_operating_hour_str("US: 08 - 11")[Weekday.Sunday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("SU: 8-11")[Weekday.Friday] == (8, 11)

    # Days + Time Interval Alias
    assert parse_operating_hour_str("MT: day")[Weekday.Monday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("MT: day")[Weekday.Wednesday] == (8, 11)

    assert parse_operating_hour_str("WMF: day")[Weekday.Friday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("MWF: day")[Weekday.Tuesday] == (8, 11)

    assert parse_operating_hour_str("SU: day")[Weekday.Sunday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("SU: day")[Weekday.Friday] == (8, 11)

    assert parse_operating_hour_str("US: day")[Weekday.Sunday] == (8, 11)
    with pytest.raises(KeyError):
        assert parse_operating_hour_str("SU: day")[Weekday.Friday] == (8, 11)

    # Invalid values
    with pytest.raises(ValueError):
        parse_operating_hour_str("MONDAY")
        parse_operating_hour_str("MONDAY: day")
        parse_operating_hour_str("day - night")
        parse_operating_hour_str("M: 9 - 24")
