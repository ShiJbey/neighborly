"""
Tests for the Neighborly's Business and Occupation logic
"""
from typing import Any, Dict

import pytest

from neighborly.core.business import (
    Occupation,
    OccupationDefinition,
)
from neighborly.core.ecs import GameObject
from neighborly.core.engine import BusinessArchetype
from neighborly.core.status import Status


class CollegeGraduate(Status):
    def __init__(self) -> None:
        super().__init__("College Graduate", "This character graduated from college.")


@pytest.fixture
def sample_occupation_types():
    def is_college_graduate(gameobject: GameObject, **kwargs: Any) -> bool:
        return gameobject.has_component(CollegeGraduate)

    ceo_occupation_type = OccupationDefinition(
        "CEO",
        5,
        [is_college_graduate],
    )

    return {"ceo": ceo_occupation_type}


@pytest.fixture
def sample_business_types():
    restaurant_type = BusinessArchetype(name="Restaurant", hours="MTWRFSU 10:00-21:00")

    return {"restaurant": restaurant_type}


def test_register_occupation_type(
    sample_occupation_types: Dict[str, OccupationDefinition]
):
    ceo_occupation_type = sample_occupation_types["ceo"]

    assert ceo_occupation_type.name == "CEO"
    assert ceo_occupation_type.level == 5

    OccupationDefinition.register_type(ceo_occupation_type)

    assert ceo_occupation_type == OccupationDefinition.get_registered_type("CEO")


def test_occupation(sample_occupation_types: Dict[str, OccupationDefinition]):
    OccupationDefinition.register_type(sample_occupation_types["ceo"])

    ceo = Occupation(OccupationDefinition.get_registered_type("CEO"), 1)

    assert ceo.get_type().name == "CEO"
    assert ceo.get_business() == 1
    assert ceo.get_years_held() == 0

    ceo.increment_years_held(0.5)

    assert ceo.get_years_held() == 0

    ceo.increment_years_held(0.5)

    assert ceo.get_years_held() == 1


def test_register_business_type(sample_business_types: Dict[str, BusinessArchetype]):
    restaurant_type = sample_business_types["restaurant"]

    BusinessArchetype.register(restaurant_type)

    BusinessArchetype.get("Restaurant").name = "Restaurant"
