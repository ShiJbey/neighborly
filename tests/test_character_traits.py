import pytest

from neighborly.core.personal_values import PersonalValues


def test_constructor():
    base_values = PersonalValues(default=50)

    overridden_values = PersonalValues({"family": 42, "power": 90, "social": 36})

    assert base_values["family"] == 50
    assert base_values["social"] == 50

    assert overridden_values["social"] == 36
    assert overridden_values["power"] == 50  # clamps value


def test_setter():
    base_values = PersonalValues()

    # Set to a value within bounds
    base_values["confidence"] = 75
    assert base_values["confidence"] == 50

    # Set to a value less than the bounds
    base_values["confidence"] = -50
    assert base_values["confidence"] == -50

    # Set to a value greater than the bounds
    base_values["confidence"] = 9000
    assert base_values["confidence"] == 50

    with pytest.raises(KeyError):
        base_values["officiousness"] = 100


def test_getter():
    base_propensities = PersonalValues(default=0)

    assert base_propensities["confidence"] == 0
    assert base_propensities["friendship"] == 0

    with pytest.raises(KeyError):
        assert base_propensities["officiousness"] == 0


def test_compatibility():
    ...
