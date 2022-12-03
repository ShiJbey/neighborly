import pandas as pd
import pytest

from neighborly.builtin.components import Age, Name, NonBinary, Retired
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import Component, World
from neighborly.core.query import (
    Query,
    Relation,
    eq_,
    filter_,
    has_components,
    ne_,
    where,
    where_any,
    where_not,
)


def test_relation_create_empty():
    r0 = Relation.create_empty()
    assert r0.empty is True
    assert r0.get_symbols() == ()

    r1 = Relation.create_empty("Apprentice", "Boss")
    assert r1.empty is True
    assert r1.get_symbols() == ("Apprentice", "Boss")


def test_relation_from_bindings():
    r0 = Relation.from_bindings(Initiator=0, LoveInterest=1)
    assert r0.empty is False
    assert r0.get_symbols() == ("Initiator", "LoveInterest")

    r0 = Relation.from_bindings(Rival=0, LoveInterest=1, Protagonist=4)
    assert r0.empty is False
    assert r0.get_symbols() == ("Rival", "LoveInterest", "Protagonist")


def test_relation_get_symbols():
    r0 = Relation.create_empty("Employee", "OldEmployer", "NewEmployer")
    assert r0.get_symbols() == ("Employee", "OldEmployer", "NewEmployer")

    r1 = Relation.create_empty("Antagonist")
    assert r1.get_symbols() == ("Antagonist",)


def test_relation_is_empty():
    r0 = Relation.create_empty()
    assert r0.empty is True

    r1 = Relation.create_empty("Hero", "DemonKing")
    assert r1.empty is True

    r2 = Relation(pd.DataFrame())
    assert r2.empty is True


def test_relation_get_tuples():
    r0 = Relation(pd.DataFrame({"Hero": [1, 1, 1], "DemonKing": [3, 4, 5]}))
    assert r0.get_tuples() == [(1, 3), (1, 4), (1, 5)]

    r1 = Relation.from_bindings(Hero=1, DemonKing=4)
    assert r1.get_tuples() == [(1, 4)]


def test_relation_get_data_frame():
    df = pd.DataFrame()
    r0 = Relation(df)
    assert id(r0.get_data_frame()) == id(df)


def test_relation_unify():

    r0 = Relation.create_empty()
    r1 = Relation(pd.DataFrame({"Hero": [1, 1, 1], "DemonKing": [3, 4, 5]}))
    r2 = Relation(pd.DataFrame({"Hero": [1, 2], "LoveInterest": [4, 6]}))
    r3 = Relation(pd.DataFrame({"Rival": [5, 3]}))

    # Test an empty Relation attempting to unify with a non-empty Relation
    assert r0.unify(r1).empty is True
    assert r0.unify(r1).get_symbols() == ()
    assert r0.unify(r1).get_tuples() == []

    # Test a non-empty Relation attempting to unify with an empty Relation
    assert r1.unify(r0).empty is True
    assert r1.unify(r0).get_symbols() == ()
    assert r1.unify(r0).get_tuples() == []

    # Test unify relations with shared symbols (DataFrame columns)
    assert r1.unify(r2).empty is False
    assert r1.unify(r2).get_symbols() == ("Hero", "DemonKing", "LoveInterest")
    assert r1.unify(r2).get_tuples() == [
        (1, 3, 4),
        (1, 4, 4),
        (1, 5, 4),
    ]

    # Test unify relations without shared symbols
    assert r2.unify(r3).empty is False
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
    world = World()

    world.spawn_gameobject([Hero(), GameCharacter("Shi", ""), Age(27)])
    world.spawn_gameobject([Hero(), GameCharacter("Astrid", ""), NonBinary()])
    world.spawn_gameobject([DemonKing(), GameCharacter("-Shi", ""), Retired()])
    world.spawn_gameobject([DemonKing(), GameCharacter("Palpatine", ""), NonBinary()])

    return world


def test_where(sample_world):
    query = Query(("Hero",), [where(has_components(Hero), "Hero")])
    result = set(query.execute(sample_world))
    expected = {(1,), (2,)}
    assert result == expected

    query = Query(("NB",), [where(has_components(GameCharacter, NonBinary), "NB")])
    result = set(query.execute(sample_world))
    expected = {(2,), (4,)}
    assert result == expected

    query = Query(
        ("HERO", "VILLAIN"),
        [
            where(has_components(GameCharacter, Hero), "HERO"),
            where(has_components(DemonKing), "VILLAIN"),
            where(has_components(Retired), "VILLAIN"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 3), (2, 3)}
    assert result == expected


def test_where_not(sample_world):
    query = Query(
        ("Hero",),
        [
            where(has_components(Hero), "Hero"),
            where_not(has_components(NonBinary), "Hero"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1,)}
    assert result == expected

    query = Query(
        ("C",),
        [
            where(has_components(GameCharacter, NonBinary), "C"),
            where_not(has_components(Hero), "C"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(4,)}
    assert result == expected

    query = Query(
        ("HERO", "VILLAIN"),
        [
            where(has_components(GameCharacter, Hero), "HERO"),
            where(has_components(DemonKing), "VILLAIN"),
            where_not(has_components(Retired), "VILLAIN"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 4), (2, 4)}
    assert result == expected


def test_where_either(sample_world):
    query = Query(
        ("X",),
        [
            where(has_components(GameCharacter, Hero), "X"),
            where_any(where(has_components(NonBinary), "X")),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(2,)}
    assert result == expected

    query = Query(
        ("X",),
        [
            where(has_components(GameCharacter), "X"),
            where_any(
                where(has_components(NonBinary), "X"),
                where(has_components(Retired), "X"),
            ),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(2,), (3,), (4,)}
    assert result == expected

    query = Query(
        ("X", "Y"),
        [
            where(has_components(GameCharacter), "X"),
            where(has_components(GameCharacter), "Y"),
            where_any(
                where(has_components(NonBinary), "X"),
                where(has_components(Retired), "Y"),
            ),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {
        (1, 3),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (3, 3),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
    }
    assert result == expected


def test_equal(sample_world):
    query = Query(
        ("X", "Y"),
        [
            where(has_components(GameCharacter, Hero), "X"),
            where(has_components(GameCharacter, Hero), "Y"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 1), (1, 2), (2, 1), (2, 2)}
    assert result == expected

    query = Query(
        ("X", "Y"),
        [
            where(has_components(GameCharacter, Hero), "X"),
            where(has_components(GameCharacter, Hero), "Y"),
            eq_(("X", "Y")),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 1), (2, 2)}
    assert result == expected


def test_not_equal(sample_world):
    query = Query(
        ("X", "Y"),
        [
            where(has_components(GameCharacter, Hero), "X"),
            where(has_components(GameCharacter, Hero), "Y"),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 1), (1, 2), (2, 1), (2, 2)}
    assert result == expected

    query = Query(
        ("X", "Y"),
        [
            where(has_components(GameCharacter, Hero), "X"),
            where(has_components(GameCharacter, Hero), "Y"),
            ne_(("X", "Y")),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1, 2), (2, 1)}
    assert result == expected


def test_query_bindings(sample_world):
    query = Query(("Hero",), [where(has_components(Hero), "Hero")])
    result = set(query.execute(sample_world, Hero=2))
    expected = {(2,)}
    assert result == expected

    query = Query(("NB",), [where(has_components(GameCharacter, NonBinary), "NB")])
    result = set(query.execute(sample_world, NB=4))
    expected = {(4,)}
    assert result == expected

    query = Query(
        ("HERO", "VILLAIN"),
        [
            where(has_components(GameCharacter, Hero), "HERO"),
            where(has_components(DemonKing), "VILLAIN"),
            where(has_components(Retired), "VILLAIN"),
        ],
    )
    result = set(query.execute(sample_world, HERO=2))
    expected = {(2, 3)}
    assert result == expected


def test_filter(sample_world):
    query = Query(
        ("X",),
        [
            where(has_components(GameCharacter), "X"),
            filter_(
                lambda w, *g: g[0].has_component(Age)
                and g[0].get_component(Age).value > 25,
                "X",
            ),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(1,)}
    assert result == expected

    query = Query(
        ("X",),
        [
            where(has_components(GameCharacter), "X"),
            filter_(
                lambda w, *g: g[0].has_component(NonBinary),
            ),
        ],
    )
    result = set(query.execute(sample_world))
    expected = {(2,), (4,)}
    assert result == expected
