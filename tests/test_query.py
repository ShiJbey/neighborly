import pytest

from neighborly.components.character import Female, Gender, Male, NonBinary, Retired
from neighborly.components.shared import Age, Name
from neighborly.ecs import Active, Component, World
from neighborly.query import QB, Relation
from neighborly.simulation import Neighborly
from neighborly.statuses import Statuses


def test_relation_create_empty():
    r0 = Relation.create_empty()
    assert r0.is_empty() is True
    assert r0.get_symbols() == ()
    assert r0.is_uninitialized() is False

    r1 = Relation.create_empty("Apprentice", "Boss")
    assert r1.is_empty() is True
    assert r1.get_symbols() == ("Apprentice", "Boss")
    assert r1.is_uninitialized() is False

    r2 = Relation((), [], False)
    assert r2.is_empty() is True
    assert r2.get_symbols() == ()
    assert r2.is_uninitialized() is True


def test_relation_from_bindings():
    r0 = Relation.from_bindings({"Initiator": 0, "LoveInterest": 1})
    assert r0.is_empty() is False
    assert r0.get_symbols() == ("Initiator", "LoveInterest")

    r0 = Relation.from_bindings({"Rival": 0, "LoveInterest": 1, "Protagonist": 4})
    assert r0.is_empty() is False
    assert r0.get_symbols() == ("Rival", "LoveInterest", "Protagonist")


def test_relation_get_symbols():
    r0 = Relation.create_empty("Employee", "OldEmployer", "NewEmployer")
    assert r0.get_symbols() == ("Employee", "OldEmployer", "NewEmployer")

    r1 = Relation.create_empty("Antagonist")
    assert r1.get_symbols() == ("Antagonist",)


def test_relation_is_empty():
    r0 = Relation.create_empty()
    assert r0.is_empty() is True

    r1 = Relation.create_empty("Hero", "DemonKing")
    assert r1.is_empty() is True


def test_relation_get_tuples():
    r0 = Relation(("Hero", "DemonKing"), [(1, 3), (1, 4), (1, 5)])
    assert r0.get_tuples() == [(1, 3), (1, 4), (1, 5)]

    r1 = Relation.from_bindings({"Hero": 1, "DemonKing": 4})
    assert r1.get_tuples() == [(1, 4)]


def test_relation_unify():
    r0 = Relation.create_empty()
    r1 = Relation(("Hero", "DemonKing"), [(1, 3), (1, 4), (1, 5)])
    r2 = Relation(("Hero", "LoveInterest"), [(1, 4), (2, 6)])
    r3 = Relation(("Rival",), [(5,), (3,)])

    # Test an empty Relation attempting to unify with a non-empty Relation
    assert r0.unify(r1).is_empty() is True
    assert r0.unify(r1).get_symbols() == ()
    assert r0.unify(r1).get_bindings() == []

    # Test a non-empty Relation attempting to unify with an empty Relation
    assert r1.unify(r0).is_empty() is True
    assert r1.unify(r0).get_symbols() == ()
    assert r1.unify(r0).get_bindings() == []

    # Test unify relations with shared symbols (DataFrame columns)
    assert r1.unify(r2).is_empty() is False
    assert r1.unify(r2).get_symbols() == ("Hero", "DemonKing", "LoveInterest")
    assert r1.unify(r2).get_tuples() == [
        (1, 3, 4),
        (1, 4, 4),
        (1, 5, 4),
    ]

    # Test unify relations without shared symbols
    assert r2.unify(r3).is_empty() is False
    assert r2.unify(r3).get_symbols() == ("Hero", "LoveInterest", "Rival")
    assert r2.unify(r3).get_tuples() == [(1, 4, 5), (1, 4, 3), (2, 6, 5), (2, 6, 3)]


def test_relation_copy():
    r0 = Relation.create_empty()
    r1 = r0.copy()
    assert id(r0) != id(r1)


class Hero(Component):
    pass


class DemonKing(Component):
    pass


@pytest.fixture()
def sample_world() -> World:
    sim = Neighborly()

    sim.world.gameobject_manager.register_component(Hero)
    sim.world.gameobject_manager.register_component(DemonKing)

    sim.world.gameobject_manager.spawn_gameobject(
        {
            Hero: {},
            Name: {"value": "Shi"},
            Age: {"value": 28},
            Male: {},
            Statuses: {},
        }
    )
    sim.world.gameobject_manager.spawn_gameobject(
        {
            Hero: {},
            Name: {"value": "Astrid"},
            Female: {},
            Statuses: {},
            Retired: {"timestamp": 0},
            Age: {"value": 24},
        }
    )
    sim.world.gameobject_manager.spawn_gameobject(
        {
            Statuses: {},
            DemonKing: {},
            Name: {"value": "Calvin"},
            Retired: {"timestamp": 10},
            Age: {"value": 22},
        }
    )
    sim.world.gameobject_manager.spawn_gameobject(
        {
            DemonKing: {},
            Name: {"value": "Palpatine"},
            NonBinary: {},
            Statuses: {},
            Age: {"value": 128},
        }
    )

    return sim.world


def test_with(sample_world: World):
    query = QB.query("_", QB.with_(Hero, "_"))
    result = set(query.execute(sample_world))
    expected = {(1,), (2,)}
    assert result == expected

    query = QB.query(("_",), QB.with_((Hero, Retired), "_"))
    result = set(query.execute(sample_world))
    expected = {(2,)}
    assert result == expected

    query = QB.query(
        ("HERO", "VILLAIN"),
        QB.with_((Hero,), "HERO"),
        QB.with_((DemonKing, Retired), "VILLAIN"),
    )
    result = set(query.execute(sample_world))
    expected = {(1, 3), (2, 3)}
    assert result == expected


def test_query_not(sample_world: World):
    query = QB.query(
        ("HERO", "VILLAIN"),
        QB.with_((Hero,), "HERO"),
        QB.not_(QB.with_((Retired,), "HERO")),
        QB.with_((DemonKing, Retired), "VILLAIN"),
    )
    result = set(query.execute(sample_world))
    expected = {(1, 3)}
    assert result == expected


def test_query_bindings(sample_world: World):
    query = QB.query("_", QB.with_(Hero, "_"))
    result = set(query.execute(sample_world, {"_": 2}))
    expected = {(2,)}
    assert result == expected

    query = QB.query(
        ("_",),
        QB.with_(Active, "_"),
        QB.filter_(
            lambda gameobject: (gameobject.has_component(NonBinary)),
            "_",
        ),
    )
    result = set(query.execute(sample_world, {"_": 4}))
    expected = {(4,)}
    assert result == expected

    query = QB.query(
        ("HERO", "VILLAIN"),
        QB.with_((Active, Hero), "HERO"),
        QB.with_((DemonKing, Retired), "VILLAIN"),
    )
    result = set(query.execute(sample_world, {"HERO": 2}))
    expected = {(2, 3)}
    assert result == expected

    query = QB.query(
        "_",
        QB.with_(Active, "_"),
        QB.filter_(
            lambda gameobject: (gameobject.has_component(NonBinary)),
            "_",
        ),
    )
    result = set(query.execute(sample_world, {"_": 4}))
    expected = {(4,)}
    assert result == expected


def test_filter(sample_world: World):
    query = QB.query(
        "_",
        QB.with_(Active, "_"),
        QB.filter_(
            lambda gameobject: gameobject.get_component(Age).value > 25,
            "_",
        ),
    )
    result = set(query.execute(sample_world))
    expected = {(1,), (4,)}
    assert result == expected

    query = QB.query(
        "_",
        QB.with_((Active, Gender), "_"),
        QB.filter_(
            lambda gameobject: (gameobject.has_component(NonBinary)),
            "_",
        ),
    )
    result = set(query.execute(sample_world))
    expected = {(4,)}
    assert result == expected

    with pytest.raises(RuntimeError):
        QB.query(("X", "Y"), QB.filter_(lambda x, y: x == y, ("X", "Y"))).execute(
            sample_world
        )
