from neighborly.core.relationship import Connection, get_modifier, Relationship


def test_get_modifier():
    acquaintance_mod = get_modifier('acquaintance')

    assert acquaintance_mod.name == 'acquaintance'
    assert acquaintance_mod.salience == 0


def test_add_remove_modifiers():
    relationship = Relationship(1, 2, 0, True)

    rival_mod = get_modifier('rival')

    relationship.add_modifier(rival_mod)

    assert relationship.has_flags(
        Connection.RIVAL) == True

    relationship.remove_modifier(rival_mod)

    assert relationship.has_flags(
        Connection.RIVAL) == False

    best_friend_mod = get_modifier('best friend')

    relationship.add_modifier(best_friend_mod)

    assert relationship.has_flags(
        Connection.BEST_FRIEND) == True
    assert relationship.salience == 30
