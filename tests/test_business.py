"""
Tests for the Neighborly's Business and Occupation logic
"""

import pytest

from neighborly.components.business import Business
from neighborly.core.ecs import EntityPrefab, GameObjectFactory
from neighborly.core.time import Weekday
from neighborly.factories import OperatingHoursFactory
from neighborly.simulation import Neighborly


def test_construct_business():
    """Constructing business components using BusinessArchetypes"""
    GameObjectFactory.add(
        EntityPrefab(
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

    sim = Neighborly()

    restaurant = GameObjectFactory.instantiate(sim.world, "Restaurant")
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.owner_type == "Proprietor"
    assert restaurant_business.owner is None
    assert restaurant_business.needs_owner() is True


def test_parse_operating_hours_str():
    parse_operating_hour_str = OperatingHoursFactory.parse_operating_hour_str

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
