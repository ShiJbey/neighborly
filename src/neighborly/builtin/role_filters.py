from neighborly.builtin.statuses import Male
from neighborly.core.character import GameCharacter
from neighborly.core.ecs import GameObject, World
from neighborly.core.life_event import LifeEvent
from neighborly.core.time import SimDateTime


def before_year(year: int):
    """
    Returns precondition function that checks if the
    current year is less than the given year
    """

    def precondition_fn(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        return world.get_resource(SimDateTime).year < year

    return precondition_fn


def is_man(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
    """Return true if GameObject is a man"""
    return gameobject.has_component(Male)


def older_than(age: int):
    def precondition_fn(world: World, event: LifeEvent, gameobject: GameObject) -> bool:
        return gameobject.get_component(GameCharacter).age > age

    return precondition_fn


def friendship_greater_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is greater than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).friendship
                > value
            )
        return False

    return fn


def friendship_less_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is less than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).friendship
                < value
            )
        return False

    return fn


def friendship_equal_to(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    friendship value for a character to another is equal to
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).friendship
                == value
            )
        return False

    return fn


def romance_greater_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is greater than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).romance > value
            )
        return False

    return fn


def romance_less_than(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is less than
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).romance < value
            )
        return False

    return fn


def romance_equal_to(value: int) -> ILifeEventCallback:
    """
    Returns a precondition function that checks if the
    romance value for a character to another is equal to
    a given value
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return (
                rel_graph.get_connection(gameobject.id, other.id).romance
                == value
            )
        return False

    return fn


def relationship_has_tag(tag: str) -> ILifeEventCallback:
    """
    Return true if the relationship between this character and
    another has the given tag
    """

    def fn(gameobject: GameObject, event: LifeEvent) -> bool:
        other: GameObject = event.data["other"]
        rel_graph = gameobject.world.get_resource(RelationshipNetwork)
        if rel_graph.has_connection(gameobject.id, other.id):
            return rel_graph.get_connection(gameobject.id, other.id).has_tags(
                RelationshipTag[tag]
            )
        return False

    return fn


def is_single(gameobject: GameObject, event: LifeEvent) -> bool:
    """Return True if this character has no relationships tagged as significant others"""
    rel_graph = gameobject.world.get_resource(RelationshipNetwork)
    significant_other_relationships = rel_graph.get_all_relationships_with_tags(
        gameobject.id, RelationshipTag.SignificantOther
    )
    return bool(significant_other_relationships)


def is_unemployed(gameobject: GameObject, event: LifeEvent) -> bool:
    """Returns True if this character does not have a job"""
    return not gameobject.has_component(Occupation)


def is_employed(gameobject: GameObject, event: LifeEvent) -> bool:
    """Returns True if this character has a job"""
    return gameobject.has_component(Occupation)
