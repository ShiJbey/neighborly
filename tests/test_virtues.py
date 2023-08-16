import random

from neighborly.components.character import Virtue, Virtues
from neighborly.ecs import World


def test_construct_virtue_vect() -> None:
    # Test that virtue vector defaults to all zeros
    vect_0 = Virtues()
    assert vect_0[Virtue.HEALTH] == 0
    assert vect_0[Virtue.POWER] == 0
    assert vect_0[Virtue.TRADITION] == 0
    assert vect_0[Virtue.AMBITION] == 0

    # Test that one can override virtue vector values
    vect_1 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -120})
    assert vect_1[Virtue.HEALTH] == 10
    assert vect_1[Virtue.POWER] == 20
    assert vect_1[Virtue.TRADITION] == -50  # Should be clamped
    assert vect_1[Virtue.AMBITION] == 0


def test_virtue_vect_compatibility() -> None:
    vect_0 = Virtues({"HEALTH": 10, "POWER": 20})
    vect_1 = Virtues({"HEALTH": 10, "POWER": 20})
    vect_2 = Virtues({"HEALTH": -10, "POWER": -20})
    vect_3 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": 10})
    vect_4 = Virtues({"HEALTH": 30, "POWER": 60})

    assert vect_0.compatibility(vect_1) == 100
    assert vect_0.compatibility(vect_2) == -9
    assert vect_0.compatibility(vect_3) == 94
    assert vect_0.compatibility(vect_4) == 93


def test_virtue_vect_get_low_values() -> None:
    vect_0 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -10, "LUST": -35})

    assert set(vect_0.get_low_values(2)) == {Virtue.TRADITION, Virtue.LUST}


def test_virtue_vect_get_high_values() -> None:
    vect_0 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -10, "LUST": -35})

    assert set(vect_0.get_high_values(2)) == {Virtue.HEALTH, Virtue.POWER}


def test_virtue_vect_get_item() -> None:
    vect_1 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -120})
    assert vect_1[Virtue.HEALTH] == 10
    assert vect_1[Virtue.POWER] == 20
    assert vect_1[Virtue.TRADITION] == -50  # Should be clamped
    assert vect_1[Virtue.AMBITION] == 0


def test_virtue_vect_set_item() -> None:
    vect_1 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -120})
    assert vect_1[Virtue.HEALTH] == 10
    vect_1[Virtue.HEALTH] = 56
    assert vect_1[Virtue.HEALTH] == 50


def test_virtue_vect_to_dict() -> None:
    vect_1 = Virtues({"HEALTH": 10, "POWER": 20, "TRADITION": -120})
    virtue_dict = vect_1.to_dict()

    assert virtue_dict["HEALTH"] == 10
    assert virtue_dict["POWER"] == 20
    assert virtue_dict["TRADITION"] == -50


def test_virtue_vect_factory() -> None:
    world = World()
    world.resource_manager.add_resource(random.Random(1234))
    vector: Virtues = Virtues.factory(world, overrides={"ADVENTURE": 10, "POWER": 20})
    assert vector[Virtue.ADVENTURE] == 10
    assert vector[Virtue.POWER] == 20
