"""Relationship System Helper Functions.

"""

from repraxis.query import DBQuery

from neighborly.components.relationship import (
    Compatibility,
    InteractionScore,
    Relationship,
    Relationships,
    Reputation,
    Romance,
    RomanticCompatibility,
    SocialRule,
    SocialRuleDirection,
    SocialRules,
)
from neighborly.components.stats import StatModifier, StatModifierType, Stats
from neighborly.components.traits import Traits
from neighborly.ecs import GameObject
from neighborly.helpers.db_helpers import preprocess_query_string
from neighborly.helpers.stats import get_stat
from neighborly.libraries import SocialRuleLibrary


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

    relationship = owner.world.gameobject_manager.spawn_gameobject()

    relationship.add_component(Relationship(relationship, owner=owner, target=target))
    relationship.add_component(Stats(relationship))
    relationship.add_component(Traits(relationship))
    relationship.add_component(Reputation(relationship))
    relationship.add_component(Romance(relationship))
    relationship.add_component(Compatibility(relationship))
    relationship.add_component(RomanticCompatibility(relationship))
    relationship.add_component(InteractionScore(relationship))

    relationship.name = f"{owner.name} -> {target.name}"

    owner.get_component(Relationships).add_outgoing_relationship(target, relationship)
    target.get_component(Relationships).add_incoming_relationship(owner, relationship)

    reevaluate_relationship(relationship.get_component(Relationship))

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
        owner.world.rp_db.delete(f"{relationship.uid}")
        relationship.destroy()
        return True

    return False


def add_social_rule(gameobject: GameObject, rule_id: str) -> None:
    """Add a social rule to a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to add the social rule to.
    rule
        The rule to add.
    """
    gameobject.get_component(SocialRules).add_rule(rule_id)

    relationships = gameobject.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        reevaluate_relationship(relationship.get_component(Relationship))

    relationships = gameobject.get_component(Relationships).incoming

    for _, relationship in relationships.items():
        reevaluate_relationship(relationship.get_component(Relationship))


def remove_social_rule(gameobject: GameObject, rule_id: str) -> None:
    """Remove a social rule from a GameObject.

    Parameters
    ----------
    gameobject
        The GameObject to remove the social rule from.
    rule
        The rule to remove.
    """
    gameobject.get_component(SocialRules).remove_rule(rule_id)

    relationships = gameobject.get_component(Relationships).outgoing

    for _, relationship in relationships.items():
        reevaluate_relationship(relationship.get_component(Relationship))

    relationships = gameobject.get_component(Relationships).incoming

    for _, relationship in relationships.items():
        reevaluate_relationship(relationship.get_component(Relationship))


def reevaluate_relationship(relationship: Relationship) -> None:
    """Reevaluate social rules for a given relationship."""

    library = relationship.gameobject.world.resource_manager.get_resource(
        SocialRuleLibrary
    )

    for rule_id in relationship.active_rules:
        remove_social_rule_modifiers(library.rules[rule_id], relationship)

    relationship.active_rules.clear()

    owner_rules = relationship.owner.get_component(SocialRules)

    for rule_id in owner_rules.rules:
        rule = library.rules[rule_id]

        if rule.direction != SocialRuleDirection.OUTGOING:
            continue

        if rule_id in relationship.active_rules:
            continue

        if check_social_rule_preconditions(rule, relationship):
            relationship.active_rules.append(rule_id)
            apply_social_rule_modifiers(rule, relationship)

    target_rules = relationship.owner.get_component(SocialRules)

    for rule_id in target_rules.rules:
        rule = library.rules[rule_id]

        if rule.direction != SocialRuleDirection.INCOMING:
            continue

        if rule_id in relationship.active_rules:
            continue

        if check_social_rule_preconditions(rule, relationship):
            relationship.active_rules.append(rule_id)
            apply_social_rule_modifiers(rule, relationship)


def apply_social_rule_modifiers(rule: SocialRule, relationship: Relationship) -> None:
    """Add stat modifiers to the relationship."""
    for entry in rule.stat_modifiers:
        get_stat(relationship.gameobject, entry.name).add_modifier(
            StatModifier(
                value=entry.value,
                modifier_type=StatModifierType[entry.modifier_type],
                source=rule,
            )
        )


def remove_social_rule_modifiers(rule: SocialRule, relationship: Relationship) -> None:
    """Remove stat modifiers from the relationship."""
    for entry in rule.stat_modifiers:
        get_stat(relationship.gameobject, entry.name).remove_modifiers_from_source(rule)


def check_social_rule_preconditions(
    rule: SocialRule, relationship: Relationship
) -> bool:
    """Check that a relationship passes all the preconditions."""
    owner = relationship.owner
    target = relationship.target

    query_lines = preprocess_query_string(rule.preconditions)

    result = DBQuery(query_lines).run(
        relationship.gameobject.world.rp_db,
        [{"?owner": owner.uid, "?target": target.uid}],
    )

    return result.success


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(Relationships)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()
