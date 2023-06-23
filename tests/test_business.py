"""
Tests for the Neighborly's Business and Occupation logic
"""

from typing import Any

import pytest

from neighborly.components.business import (
    Business,
    JobRequirementLibrary,
    JobRequirementParser,
)
from neighborly.components.character import GameCharacter, Gender, GenderType
from neighborly.components.shared import Age
from neighborly.core.ecs import Component, EntityPrefab, GameObject, GameObjectFactory
from neighborly.core.time import Weekday
from neighborly.factories import OperatingHoursFactory
from neighborly.plugins.talktown.school import CollegeGraduate
from neighborly.simulation import Neighborly


def test_construct_business():
    """Constructing business components using BusinessArchetypes"""

    sim = Neighborly()

    sim.world.get_resource(GameObjectFactory).add(
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

    restaurant = sim.world.get_resource(GameObjectFactory).instantiate(
        sim.world, "Restaurant"
    )
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
        gameobject.world.get_component_info(component_name).component_type
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

    sim.world.add_resource(library)

    sim.world.register_component(CollegeGraduate)
    sim.world.register_component(Cyborg)

    library.add("has_gender", has_gender)
    library.add("over_age", over_age)
    library.add("has_last_name", has_last_name)
    library.add("has_component", has_component)

    kieth = sim.world.spawn_gameobject(
        [GameCharacter("Kieth", "Smith"), Gender("Male"), Age(32)]
    )

    percy = sim.world.spawn_gameobject(
        [GameCharacter("Percy", "Jenkins"), Age(51), CollegeGraduate()]
    )

    dolph = sim.world.spawn_gameobject(
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
