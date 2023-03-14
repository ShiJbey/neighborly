from typing import Any, Dict, Type

from neighborly.components import Virtues
from neighborly.components.character import GameCharacter, Virtue
from neighborly.components.shared import Age
from neighborly.core.ecs import GameObject
from neighborly.core.relationship import Friendship, RelationshipFacet, Romance, lerp
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.query import are_related, is_single

plugin_info = PluginInfo(
    name="default location bias rules plugin",
    plugin_id="default.location_bias_rules",
    version="0.1.0",
)


def romance_boost_from_shared_virtues(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:
    """Characters with shared high/low virtues gain romance points"""

    if not subject.has_component(Virtues) or not target.has_component(Virtues):
        return {}

    subject_virtues = subject.get_component(Virtues)
    target_virtues = target.get_component(Virtues)

    shared_likes = set(subject_virtues.get_high_values()).intersection(
        set(target_virtues.get_high_values())
    )
    shared_dislikes = set(subject_virtues.get_low_values()).intersection(
        set(target_virtues.get_low_values())
    )

    return {Romance: len(shared_likes) + len(shared_dislikes)}


def romance_loss_from_virtue_conflicts(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:
    """Characters with shared high/low virtues gain romance points"""

    if not subject.has_component(Virtues) or not target.has_component(Virtues):
        return {}

    subject_virtues = subject.get_component(Virtues)
    target_virtues = target.get_component(Virtues)

    subject_conflicts = set(subject_virtues.get_high_values()).intersection(
        set(target_virtues.get_low_values())
    )
    target_conflicts = set(target_virtues.get_high_values()).intersection(
        set(subject_virtues.get_low_values())
    )

    return {Romance: -1 * (len(subject_conflicts) + len(target_conflicts))}


def friendship_virtue_compatibility(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:
    """Characters with more similar virtues will be better friends"""

    if not subject.has_component(Virtues) or not target.has_component(Virtues):
        return {}

    character_virtues = subject.get_component(Virtues)
    acquaintance_virtues = target.get_component(Virtues)

    compatibility = float(character_virtues.compatibility(acquaintance_virtues)) / 100.0

    return {Friendship: round(4 * compatibility)}


def virtue_rule(
    subject_virtue: Virtue,
    target_virtue: Virtue,
    modifier: Dict[Type[RelationshipFacet], int],
):
    def rule(
        subject: GameObject, target: GameObject
    ) -> Dict[Type[RelationshipFacet], int]:

        if not subject.has_component(Virtues) or not target.has_component(Virtues):
            return {}

        subject_virtues = subject.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        if subject_virtues[subject_virtue] >= Virtues.STRONG_AGREE:
            if target_virtues[target_virtue] >= Virtues.STRONG_AGREE:
                return modifier

        return {}

    return rule


def not_attracted_to_family(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:
    """Characters with more similar virtues will be better friends"""

    if are_related(subject, target):
        return {Romance: -15}

    return {}


def romance_from_age_difference(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:
    """Characters with more similar virtues will be better friends"""

    if not subject.has_component(GameCharacter) or not target.has_component(
        GameCharacter
    ):
        return {}

    subject_age = subject.get_component(Age).value
    target_age = subject.get_component(Age).value
    modifier = -1 * round(lerp(-3, 3, min(1.0, abs(subject_age - target_age) / 10)))

    return {Romance: modifier}


def romance_decrease_for_relationship(
    subject: GameObject, target: GameObject
) -> Dict[Type[RelationshipFacet], int]:

    if subject.has_component(GameCharacter) and target.has_component(GameCharacter):
        if not is_single(subject):
            return {Romance: -2}

    return {}


def setup(sim: Neighborly, **kwargs: Any):
    sim.add_social_rule(
        romance_boost_from_shared_virtues, "romance boost from shared values"
    )
    sim.add_social_rule(
        romance_loss_from_virtue_conflicts, "romance loss from conflicting values"
    )
    sim.add_social_rule(
        friendship_virtue_compatibility, "friendship boost from virtue alignment"
    )

    sim.add_social_rule(
        virtue_rule(Virtue.ADVENTURE, Virtue.TRANQUILITY, {Friendship: -1}),
        "tranquility likes adventure",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.TRANQUILITY, Virtue.ADVENTURE, {Friendship: -1}),
        "adventure likes tranquility",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.ADVENTURE, Virtue.TRADITION, {Friendship: -1}),
        "adventure dislikes tradition",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.TRADITION, Virtue.ADVENTURE, {Friendship: -1}),
        "tradition dislikes adventure",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.EXCITEMENT, Virtue.TRANQUILITY, {Friendship: -1}),
        "excitement dislikes tranquility",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.TRANQUILITY, Virtue.EXCITEMENT, {Friendship: -1}),
        "tranquility dislikes adventure",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.ROMANCE, Virtue.LOYALTY, {Romance: -1}),
        "romance in not attracted to loyalty",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.LOYALTY, Virtue.ROMANCE, {Romance: -1}),
        "loyalty is not attracted to romance",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.PEACE, Virtue.POWER, {Friendship: -1}),
        "peace dislikes power",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.POWER, Virtue.PEACE, {Friendship: -1}),
        "power dislikes peace",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.PEACE, Virtue.EXCITEMENT, {Friendship: -1}),
        "peace dislikes excitement",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.EXCITEMENT, Virtue.PEACE, {Friendship: -1}),
        "excitement dislikes peace",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.WEALTH, Virtue.MATERIAL_THINGS, {Friendship: 1}),
        "wealth likes material things",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.MATERIAL_THINGS, Virtue.WEALTH, {Friendship: 1}),
        "material things likes wealth",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.KNOWLEDGE, Virtue.POWER, {Friendship: 1}),
        "knowledge likes power",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.POWER, Virtue.KNOWLEDGE, {Friendship: 1}),
        "power likes knowledge",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.WEALTH, Virtue.POWER, {Friendship: 1}), "wealth likes power"
    )
    sim.add_social_rule(
        virtue_rule(Virtue.POWER, Virtue.WEALTH, {Friendship: 1}), "power likes wealth"
    )

    sim.add_social_rule(
        virtue_rule(Virtue.ROMANCE, Virtue.LUST, {Romance: 1}), "romance likes lust"
    )
    sim.add_social_rule(
        virtue_rule(Virtue.LUST, Virtue.ROMANCE, {Romance: 1}), "lust likes romance"
    )

    # This is not reciprocal
    sim.add_social_rule(
        virtue_rule(Virtue.INDEPENDENCE, Virtue.FAMILY, {Friendship: -1}),
        "independence dislikes family",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.CURIOSITY, Virtue.KNOWLEDGE, {Friendship: 1}),
        "curiosity likes knowledge",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.KNOWLEDGE, Virtue.CURIOSITY, {Friendship: 1}),
        "knowledge likes curiosity",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.PEACE, Virtue.NATURE, {Friendship: 1}), "peace likes nature"
    )

    sim.add_social_rule(
        virtue_rule(Virtue.NATURE, Virtue.MATERIAL_THINGS, {Friendship: -1}),
        "nature dislikes material things",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.AMBITION, Virtue.WEALTH, {Friendship: 1}),
        "ambition likes wealth",
    )
    sim.add_social_rule(
        virtue_rule(Virtue.AMBITION, Virtue.POWER, {Friendship: 1}),
        "ambition likes power",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.INDEPENDENCE, Virtue.HEALTH, {Friendship: 1}),
        "independence likes health",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.LUST, Virtue.INDEPENDENCE, {Romance: 1}),
        "lust is attracted to independence",
    )

    sim.add_social_rule(
        virtue_rule(Virtue.FRIENDSHIP, Virtue.FAMILY, {Romance: 1}),
        "friendship is attracted to family virtue",
    )

    sim.add_social_rule(not_attracted_to_family, "related")

    sim.add_social_rule(romance_from_age_difference, "age_difference")
