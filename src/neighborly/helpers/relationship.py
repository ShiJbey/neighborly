"""Relationship System Helper Functions.

"""

from sqlalchemy import exists, select

from neighborly.components.relationship import Relationship
from neighborly.components.shared import Agent
from neighborly.components.stats import Stat
from neighborly.ecs import GameObject
from neighborly.helpers.stats import add_stat, remove_stat_modifiers_from_source
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

    relationship = GameObject.create_new(
        owner.world,
        components={
            Relationship: {
                "owner": owner.get_component(Agent),
                "target": target.get_component(Agent),
            }
        },
    )

    add_stat(
        relationship,
        Stat(name="reputation", base_value=0, min_value=-100, max_value=100),
    )
    add_stat(
        relationship,
        Stat(name="romance", base_value=0, min_value=-100, max_value=100),
    )
    add_stat(
        relationship,
        Stat(name="compatibility", base_value=0, min_value=-100, max_value=100),
    )
    add_stat(
        relationship,
        Stat(
            name="romantic_compatibility", base_value=0, min_value=-100, max_value=100
        ),
    )
    add_stat(
        relationship,
        Stat(name="interaction_score", base_value=0, min_value=0, max_value=10),
    )

    relationship.name = f"{owner.name} -> {target.name}"

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
    return owner.world.session.execute(
        select(Relationship)
        .where(Relationship.owner_id == owner.uid)
        .where(Relationship.target_id == target.uid)
    ).one()[0]


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
    return bool(
        owner.world.session.query(
            exists(Relationship)
            .where(Relationship.owner_id == owner.uid)
            .where(Relationship.target_id == target.uid)
        ).scalar()
    )


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

    search_traits: set[str] = set(*traits)

    outgoing_relationships = gameobject.world.session.execute(
        select(Relationship).where(Relationship.owner_id == gameobject.uid)
    ).tuples()

    for (relationship,) in outgoing_relationships:
        relationship_traits: set[str] = set(
            t.trait_id for t in relationship.gameobject.get_component(Traits).instances
        )

        if len(search_traits - relationship_traits) == 0:
            matches.append(relationship.gameobject)

    return matches


def reevaluate_social_rules(relationship_obj: GameObject) -> None:
    """Reevaluate the social rules against the given relationship."""

    relationship = relationship_obj.get_component(Relationship)
    rule_library = relationship_obj.world.resources.get_resource(SocialRuleLibrary)

    for entry in relationship.active_rules:
        social_rule = rule_library.rules[entry.rule_id]
        for modifier in social_rule.modifiers:
            remove_stat_modifiers_from_source(
                relationship_obj, modifier.name, entry.rule_id
            )

    relationship.active_rules.clear()

    rule_library = relationship_obj.world.resources.get_resource(SocialRuleLibrary)

    # for rule in rule_library.rules:
    #     if rule.check_preconditions(relationship_obj):
    #         for modifier in rule.modifiers:
    #             add_stat_modifier(
    #                 relationship_obj,
    #                 modifier.name,
    #                 StatModifier(
    #                     value=modifier.value,
    #                     modifier_type=StatModifierType.FLAT,
    #                     source=rule,
    #                 ),
    #             )

    #         relationship.active_rules.append(
    #             ActiveSocialRule(
    #                 rule=rule,
    #                 description=rule.description.replace(
    #                     "[owner]", relationship.owner.gameobject.name
    #                 ).replace("[target]", relationship.target.gameobject.name),
    #             )
    #         )


def deactivate_relationships(gameobject: GameObject) -> None:
    """Deactivates all an objects incoming and outgoing relationships."""

    outgoing_relationships = gameobject.world.session.execute(
        select(Relationship).where(Relationship.owner_id == gameobject.uid)
    ).tuples()

    for (relationship,) in outgoing_relationships:
        relationship.gameobject.deactivate()

    incoming_relationships = gameobject.world.session.execute(
        select(Relationship).where(Relationship.target_id == gameobject.uid)
    ).tuples()

    for (relationship,) in incoming_relationships:
        relationship.gameobject.deactivate()
