import pandas as pd
import pytest

from neighborly.components.character import GameCharacter, Gender, GenderValue, Retired
from neighborly.components.shared import Age
from neighborly.core.ecs import Component, World
from neighborly.core.query import QueryBuilder, Relation, eq_
from neighborly.utils.role_filters import is_gender


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
    world.spawn_gameobject(
        [Hero(), GameCharacter("Astrid", ""), Gender(GenderValue.Female), Retired()]
    )
    world.spawn_gameobject([DemonKing(), GameCharacter("-Shi", ""), Retired()])
    world.spawn_gameobject(
        [DemonKing(), GameCharacter("Palpatine", ""), Gender(GenderValue.NonBinary)]
    )

    return world


def test_with(sample_world: World):
    query = QueryBuilder().with_((Hero,)).build()
    result = set(query.execute(sample_world))
    expected = {(1,), (2,)}
    assert result == expected

    query = QueryBuilder().with_((Hero, Retired)).build()
    result = set(query.execute(sample_world))
    expected = {(2,)}
    assert result == expected

    query = (
        QueryBuilder("HERO", "VILLAIN")
        .with_((GameCharacter, Hero), "HERO")
        .with_((DemonKing, Retired), "VILLAIN")
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(1, 3), (2, 3)}
    assert result == expected


def test_without(sample_world: World):
    query = QueryBuilder().with_((Hero,)).without_((Retired,)).build()
    result = set(query.execute(sample_world))
    expected = {(1,)}
    assert result == expected

    query = QueryBuilder().with_((GameCharacter, Gender)).without_((Hero,)).build()
    result = set(query.execute(sample_world))
    expected = {(4,)}
    assert result == expected

    query = (
        QueryBuilder("Hero", "Villain")
        .with_((GameCharacter, Hero), "Hero")
        .with_((DemonKing,), "Villain")
        .without_((Retired,), "Villain")
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(1, 4), (2, 4)}
    assert result == expected

    with pytest.raises(RuntimeError):
        (QueryBuilder().without_((Retired,)).build().execute(sample_world))


def test_equal(sample_world: World):
    query = (
        QueryBuilder("X", "Y")
        .with_((GameCharacter, Hero), "X")
        .with_((GameCharacter, Hero), "Y")
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(1, 1), (1, 2), (2, 1), (2, 2)}
    assert result == expected

    query = (
        QueryBuilder("X", "Y")
        .with_((GameCharacter, Hero), "X")
        .with_((GameCharacter, Hero), "Y")
        .filter_(eq_, "X", "Y")
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(1, 1), (2, 2)}
    assert result == expected


def test_query_bindings(sample_world: World):

    query = QueryBuilder().with_((Hero,)).build()
    result = set(query.execute(sample_world, 2))
    expected = {(2,)}
    assert result == expected

    query = (
        QueryBuilder()
        .with_((GameCharacter, Gender))
        .filter_(is_gender(GenderValue.NonBinary))
        .build()
    )
    result = set(query.execute(sample_world, 4))
    expected = {(4,)}
    assert result == expected

    query = (
        QueryBuilder("HERO", "VILLAIN")
        .with_((GameCharacter, Hero), "HERO")
        .with_((DemonKing, Retired), "VILLAIN")
        .build()
    )
    result = set(query.execute(sample_world, HERO=2))
    expected = {(2, 3)}
    assert result == expected


def test_filter(sample_world: World):
    query = (
        QueryBuilder()
        .with_((GameCharacter,))
        .filter_(
            lambda world, *gameobjects: gameobjects[0].has_component(Age)
            and gameobjects[0].get_component(Age).value > 25
        )
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(1,)}
    assert result == expected

    query = (
        QueryBuilder()
        .with_((GameCharacter,))
        .filter_(is_gender(GenderValue.NonBinary))
        .build()
    )
    result = set(query.execute(sample_world))
    expected = {(4,)}
    assert result == expected

    with pytest.raises(RuntimeError):
        QueryBuilder("X", "Y").filter_(eq_, "X", "Y").build().execute(sample_world)
