from neighborly.core.relationship import Connection, get_modifier, Relationship


def test_get_modifier():
    acquaintance_mod = get_modifier('acquaintance')

    assert acquaintance_mod.name == 'acquaintance'
    assert acquaintance_mod.salience == 0


def test_add_remove_modifiers():
    relationship = Relationship(1, 2)

    acquaintance_mod = get_modifier('acquaintance')

    relationship.add_modifier(acquaintance_mod)

    assert relationship.modifiers[0] == acquaintance_mod
    assert relationship.has_flags(
        Connection.ACQUAINTANCE) == True

    relationship.remove_modifier(acquaintance_mod)

    assert len(relationship.modifiers) == 0
    assert relationship.has_flags(
        Connection.ACQUAINTANCE) == False

    best_friend_mod = get_modifier('best friend')

    relationship.add_modifier(best_friend_mod)

    assert relationship.modifiers[0] == best_friend_mod
    assert relationship.has_flags(
        Connection.BEST_FRIEND) == True
    assert relationship.salience == 30
