"""Relationship System Helper Functions.

"""

from neighborly.components.relationship import (
    Relationship,
    Relationships,
    SocialRule,
    SocialRules,
)
from neighborly.components.stats import Stat, Stats
from neighborly.components.traits import Traits
from neighborly.ecs import GameObject
from neighborly.helpers.stats import add_stat
from neighborly.helpers.traits import has_trait


def add_relationship(owner: GameObject, target: GameObject) -> GameObject:
    """
    Creates a new relationship from the subject to the target

    Parameters
    ----------
    owner
        The GameObject that owns the relationship
    target
        The GameObject that the Relationship is directed toward

    Returns
    -------
    GameObject
        The new relationship instance
    """
    if has_relationship(owner, target):
        return get_relationship(owner, target)

    relationship = owner.world.gameobject_manager.spawn_gameobject(
        components=[
            Relationship(owner=owner, target=target),
            Stats(),
            SocialRules(),
            Traits(),
        ],
    )

    add_stat(relationship, "reputation", Stat(base_value=0, bounds=(-100, 100)))
    add_stat(relationship, "romance", Stat(base_value=0, bounds=(-100, 100)))
    add_stat(relationship, "compatibility", Stat(base_value=0))
    add_stat(relationship, "romantic_compatibility", Stat(base_value=0))
    add_stat(relationship, "interaction_score", Stat(base_value=0, bounds=(0, 10)))

    relationship.name = f"{owner.name} -> {target.name}"

    owner.get_component(Relationships).add_outgoing_relationship(target, relationship)
    target.get_component(Relationships).add_incoming_relationship(owner, relationship)

    # Apply the social rules
    social_rules = owner.get_component(SocialRules).rules
    for rule in social_rules:
        if rule.check_preconditions(relationship):
            rule.apply(relationship)
            relationship.get_component(SocialRules).add_rule(rule)

    return relationship


def get_relationship(
    owner: GameObject,
    target: GameObject,
) -> GameObject:
    """Get a relationship from one GameObject to another.

    This function will create a new instance of a relationship if one does not exist.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    GameObject
        A relationship instance.
    """
    if has_relationship(owner, target):
        return owner.get_component(Relationships).get_outgoing_relationship(target)

    return add_relationship(owner, target)


def has_relationship(owner: GameObject, target: GameObject) -> bool:
    """Check if there is an existing relationship from the owner to the target.

    Parameters
    ----------
    owner
        The owner of the relationship.
    target
        The target of the relationship.

    Returns
    -------
    bool
        True if there is an existing Relationship between the GameObjects,
        False otherwise.
    """
    return owner.get_component(Relationships).has_outgoing_relationship(target)


def destroy_relationship(owner: GameObject, target: GameObject) -> bool:
    """Destroy the relationship GameObject to the target.

    Parameters
    ----------
    owner
        The owner of the relationship
    target
        The target of the relationship

    Returns
    -------
    bool
        Returns True if a relationship was removed. False otherwise.
    """
    if has_relationship(owner, target):
        relationship = get_relationship(owner, target)
        owner.get_component(Relationships).remove_outgoing_relationship(target)
        target.get_component(Relationships).remove_incoming_relationship(owner)
        relationship.destroy()
        return True

    return False


def get_relationships_with_traits(
    gameobject: GameObject, *traits: str
) -> list[GameObject]:
    """Get all the relationships with the given tags.

    Parameters
    ----------
    gameobject
        The character to check.
    *traits
        The trait IDs to check for on relationships.

    Returns
    -------
    list[GameObject]
        Relationships with the given traits.
    """
    matches: list[GameObject] = []

    for _, relationship in gameobject.get_component(Relationships).outgoing.items():
        if all(has_trait(relationship, trait) for trait in traits):
            matches.append(relationship)

    return matches


def add_social_rule(gameobject: GameObject, rule: SocialRule) -> None:
    """Add a social rule to a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the social rule to.
    rule
        The rule to add.
    """
    gameobject.get_component(SocialRules).add_rule(rule)
    relationships = gameobject.get_component(Relationships).outgoing

    # Apply this rule to all relationships
    for _, relationship in relationships.items():
        if rule.check_preconditions(relationship):
            relationship.get_component(SocialRules).add_rule(rule)
            rule.apply(relationship)


def remove_social_rule(gameobject: GameObject, rule: SocialRule) -> None:
    """Remove a social rule from a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to remove the social rule from.
    rule
        The rule to remove.
    """
    gameobject.get_component(SocialRules).add_rule(rule)
    relationships = gameobject.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        relationship_rules = relationship.get_component(SocialRules)
        if relationship_rules.has_rule(rule):
            rule.remove(relationship)
            relationship_rules.remove_rule(rule)

    gameobject.get_component(SocialRules).remove_rule(rule)


def remove_all_social_rules_from_source(gameobject: GameObject, source: object) -> None:
    """Remove all social rules with a given source.

    Parameters
    ----------
    gameobject
        The GameObject modify.
    source
        The source object to check for.
    """
    # Remove the effects of this social rule from all current relationships.
    rules = list(gameobject.get_component(SocialRules).rules)

    for rule in rules:
        if rule.source == source:
            remove_social_rule(gameobject, rule)


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(Relationships)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()
