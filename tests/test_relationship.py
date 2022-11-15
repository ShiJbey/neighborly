from neighborly import GameObject, World
from neighborly.core.character import GameCharacter
from neighborly.core.relationship import Relationships


def create_character(world: World) -> GameObject:
    return world.spawn_gameobject([GameCharacter(), Relationships()])


def test_relationships():
    # Create characters as ints
    world = World()

    homer = create_character(world)
    lisa = create_character(world)
    bart = create_character(world)
    maggie = create_character(world)

    lisa.get_component(Relationships).get(bart.id).add_tags("Sibling")
    assert lisa.get_component(Relationships).get(bart.id).has_tag("Sibling")

    lisa.get_component(Relationships).get(maggie.id).add_tags("Sibling")
    assert lisa.get_component(Relationships).get(maggie.id).has_tag("Sibling")

    homer.get_component(Relationships).get(lisa.id).add_tags("Child")
    assert homer.get_component(Relationships).get(lisa.id).has_tag("Child")

    assert len(lisa.get_component(Relationships).get_all_with_tags("Sibling")) == 2
