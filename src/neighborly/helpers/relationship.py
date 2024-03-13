"""Relationship System Helper Functions.

"""

from neighborly.components.relationship import (
    ActiveSocialRule,
    Relationship,
    Relationships,
)
from neighborly.components.stats import Stat, StatModifier, StatModifierType, Stats
from neighborly.components.traits import Traits
from neighborly.ecs import GameObject
from neighborly.helpers.stats import add_stat
from neighborly.helpers.traits import has_trait
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

    relationship = owner.world.gameobjects.spawn_gameobject(
        components=[
            Relationship(owner=owner, target=target),
            Stats(),
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

    reevaluate_social_rules(relationship)

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


def reevaluate_social_rules(relationship_obj: GameObject) -> None:
    """Reevaluate the social rules against the given relationship."""

    relationship = relationship_obj.get_component(Relationship)
    stats = relationship_obj.get_component(Stats)
    for entry in relationship.active_social_rules:
        for modifier in entry.rule.modifiers:
            stats.get_stat(modifier.name).remove_modifiers_from_source(entry.rule)

    relationship.active_social_rules.clear()

    rule_library = relationship_obj.world.resources.get_resource(SocialRuleLibrary)

    for rule in rule_library.rules:
        if rule.check_preconditions(relationship_obj):
            for modifier in rule.modifiers:
                stats.get_stat(modifier.name).add_modifier(
                    StatModifier(
                        value=modifier.value,
                        modifier_type=StatModifierType.FLAT,
                        source=rule,
                    )
                )

            relationship.active_social_rules.append(
                ActiveSocialRule(
                    rule=rule,
                    description=rule.description.replace(
                        "[owner]", relationship.owner.name
                    ).replace("[target]", relationship.target.name),
                )
            )


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    relationships = gameobject.get_component(Relationships)

    for _, relationship in relationships.outgoing.items():
        relationship.deactivate()

    for _, relationship in relationships.incoming.items():
        relationship.deactivate()
