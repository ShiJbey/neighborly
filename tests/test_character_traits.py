import pytest

from neighborly.core.character.traits import CharacterTraits


def test_constructor():
    base_propensities = CharacterTraits()

    rls_propensities = CharacterTraits({
        "rash": 90,
        "lust": 90,
        "social": 90
    })

    assert base_propensities["love"] == 50
    assert base_propensities["social"] == 50

    assert rls_propensities["social"] == 90
    assert rls_propensities["lust"] == 90


def test_setter():
    base_propensities = CharacterTraits()

    # Set to a value within bounds
    base_propensities["confidence"] = 75
    assert base_propensities["confidence"] == 75

    # Set to a value less than the bounds
    base_propensities["confidence"] = -50
    assert base_propensities["confidence"] == 0

    # Set to a value greater than the bounds
    base_propensities["confidence"] = 9000
    assert base_propensities["confidence"] == 100

    with pytest.raises(KeyError):
        base_propensities["officiousness"] = 100


def test_getter():
    base_propensities = CharacterTraits()

    assert base_propensities["confidence"] == 50
    assert base_propensities["friendlyness"] == 50

    with pytest.raises(KeyError):
        assert base_propensities["officiousness"] == 50
