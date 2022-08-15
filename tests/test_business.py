"""
Tests for the Neighborly's Business and Occupation logic
"""
from typing import Any, Dict

import pytest

from neighborly.core.archetypes import BusinessArchetype
from neighborly.core.business import (
    Business,
    BusinessStatus,
    Occupation,
    OccupationType,
    OccupationTypeLibrary,
)
from neighborly.core.ecs import GameObject, World
from neighborly.core.status import Status


class CollegeGraduate(Status):
    def __init__(self) -> None:
        super().__init__("College Graduate", "This character graduated from college.")


@pytest.fixture
def sample_occupation_types():
    def is_college_graduate(
        world: World, gameobject: GameObject, **kwargs: Any
    ) -> bool:
        return gameobject.has_component(CollegeGraduate)

    ceo_occupation_type = OccupationType(
        "CEO",
        5,
        is_college_graduate,
    )

    return {"ceo": ceo_occupation_type}


@pytest.fixture
def sample_business_types():
    restaurant_type = BusinessArchetype(name="Restaurant", hours=["day"])

    return {"restaurant": restaurant_type}


def test_register_occupation_type(sample_occupation_types: Dict[str, OccupationType]):
    ceo_occupation_type = sample_occupation_types["ceo"]

    assert ceo_occupation_type.name == "CEO"
    assert ceo_occupation_type.level == 5

    OccupationTypeLibrary.add(ceo_occupation_type)

    assert ceo_occupation_type == OccupationTypeLibrary.get("CEO")


def test_occupation(sample_occupation_types: Dict[str, OccupationType]):
    OccupationTypeLibrary.add(sample_occupation_types["ceo"])

    ceo = Occupation(OccupationTypeLibrary.get("CEO"), 1)

    assert ceo.get_type().name == "CEO"
    assert ceo.get_business() == 1
    assert ceo.get_years_held() == 0

    ceo.increment_years_held(0.5)

    assert ceo.get_years_held() == 0

    ceo.increment_years_held(0.5)

    assert ceo.get_years_held() == 1


def test_construct_occupation():
    """Constructing Occupations from OccupationTypes"""
    pass


def test_construct_business():
    """Constructing business components using BusinessArchetypes"""
    restaurant_Archetype = BusinessArchetype(
        "Restaurant",
        name_format="#restaurant_name#",
        hours=["day", "evening"],
        owner_type="Proprietor",
        employee_types={
            "Cook": 1,
            "Server": 2,
            "Host": 1,
        },
    )

    world = World()

    restaurant = world.spawn_archetype(restaurant_Archetype)
    restaurant_business = restaurant.get_component(Business)

    assert restaurant_business.business_type == "Restaurant"
    assert restaurant_business.owner_type == "Proprietor"
    assert restaurant_business.status == BusinessStatus.PendingOpening
    assert restaurant_business.owner is None
    assert restaurant_business.needs_owner() is True
