from typing import Dict, Tuple, Type

from neighborly.components.character import GameCharacter, Virtue, Virtues
from neighborly.components.shared import Age
from neighborly.ecs import GameObject
from neighborly.relationship import (
    PlatonicCompatibility,
    Romance,
    RomanticCompatibility,
    SocialRule,
    SocialRuleLibrary,
)
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.stats import StatComponent, StatModifier, StatModifierType
from neighborly.utils.common import lerp
from neighborly.utils.query import are_related, is_single

plugin_info = PluginInfo(
    name="default location preference rules plugin",
    plugin_id="default.location_preference_rules",
    version="0.1.0",
)


class RomanceBoostFromSharedVirtues(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        owner_virtues = owner.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        shared_likes = set(owner_virtues.get_high_values()).intersection(
            set(target_virtues.get_high_values())
        )

        shared_dislikes = set(owner_virtues.get_low_values()).intersection(
            set(target_virtues.get_low_values())
        )

        relationship.get_component(RomanticCompatibility).add_modifier(
            StatModifier(
                value=-len(shared_likes) + len(shared_dislikes),
                modifier_type=StatModifierType.Flat,
                source=self,
            )
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(RomanticCompatibility).remove_modifiers_from_source(
            self
        )

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return owner.has_component(Virtues) and target.has_component(Virtues)


class RomanceLossFromVirtueConflicts(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        owner_virtues = owner.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        subject_conflicts = set(owner_virtues.get_high_values()).intersection(
            set(target_virtues.get_low_values())
        )

        target_conflicts = set(target_virtues.get_high_values()).intersection(
            set(owner_virtues.get_low_values())
        )

        relationship.get_component(RomanticCompatibility).add_modifier(
            StatModifier(
                value=-1 * (len(subject_conflicts) + len(target_conflicts)),
                modifier_type=StatModifierType.Flat,
                source=self,
            )
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(RomanticCompatibility).remove_modifiers_from_source(
            self
        )

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return owner.has_component(Virtues) and target.has_component(Virtues)


class FriendshipBoostFromVirtueCompatibility(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        owner_virtues = owner.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        compatibility = round(
            5 * float(owner_virtues.compatibility(target_virtues)) / 100.0
        )

        relationship.get_component(PlatonicCompatibility).add_modifier(
            StatModifier(
                value=compatibility, modifier_type=StatModifierType.Flat, source=self
            )
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(PlatonicCompatibility).remove_modifiers_from_source(
            self
        )

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return owner.has_component(Virtues) and target.has_component(Virtues)


class VirtueRule(SocialRule):
    def __init__(
        self,
        owner_virtue: Virtue,
        target_virtue: Virtue,
        modifiers: Dict[Type[StatComponent], Tuple[int, StatModifierType]],
    ) -> None:
        self.owner_virtue = owner_virtue
        self.target_virtue = target_virtue
        self.modifiers = modifiers

    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        for stat_type, (modifier_value, modifier_type) in self.modifiers.items():
            relationship.get_component(stat_type).add_modifier(
                StatModifier(
                    value=modifier_value, modifier_type=modifier_type, source=self
                )
            )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        for stat_type in self.modifiers:
            relationship.get_component(stat_type).remove_modifiers_from_source(self)

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        owner_virtues = owner.get_component(Virtues)
        target_virtues = target.get_component(Virtues)

        if owner_virtues[self.owner_virtue] >= Virtues.STRONG_AGREE:
            if target_virtues[self.target_virtue] >= Virtues.STRONG_AGREE:
                return True

        return False


class NotAttractedToFamily(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(Romance).add_modifier(
            StatModifier(
                value=-15, modifier_type=StatModifierType.PercentAdd, source=self
            )
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(Romance).remove_modifiers_from_source(self)

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return are_related(owner, target)


class RomanceBoostFromAgeDifference(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        owner_age = owner.get_component(Age).value
        target_age = target.get_component(Age).value
        modifier_value = -1 * round(
            lerp(-3, 3, min(1.0, abs(owner_age - target_age) / 10))
        )
        relationship.get_component(RomanticCompatibility).add_modifier(
            StatModifier(
                value=modifier_value, modifier_type=StatModifierType.Flat, source=self
            )
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(RomanticCompatibility).remove_modifiers_from_source(
            self
        )

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return owner.has_component(GameCharacter) and target.has_component(
            GameCharacter
        )


class InRelationshipRomanceRule(SocialRule):
    def apply(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(Romance).add_modifier(
            StatModifier(value=-2, modifier_type=StatModifierType.Flat, source=self)
        )

    def remove(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> None:
        relationship.get_component(Romance).remove_modifiers_from_source(self)

    def check_preconditions(
        self, owner: GameObject, target: GameObject, relationship: GameObject
    ) -> bool:
        return (
            owner.has_component(GameCharacter)
            and target.has_component(GameCharacter)
            and not is_single(owner)
        )


def setup(sim: Neighborly):
    social_rule_library = sim.world.resource_manager.get_resource(SocialRuleLibrary)

    social_rule_library.add_rule(InRelationshipRomanceRule())
    social_rule_library.add_rule(RomanceBoostFromAgeDifference())
    social_rule_library.add_rule(FriendshipBoostFromVirtueCompatibility())
    social_rule_library.add_rule(RomanceBoostFromSharedVirtues())
    social_rule_library.add_rule(RomanceLossFromVirtueConflicts())
    social_rule_library.add_rule(NotAttractedToFamily())

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.ADVENTURE,
            Virtue.TRANQUILITY,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.TRANQUILITY,
            Virtue.ADVENTURE,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.ADVENTURE,
            Virtue.TRADITION,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.TRADITION,
            Virtue.ADVENTURE,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.EXCITEMENT,
            Virtue.TRANQUILITY,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.TRANQUILITY,
            Virtue.EXCITEMENT,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.ROMANCE,
            Virtue.LOYALTY,
            {RomanticCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.LOYALTY,
            Virtue.ROMANCE,
            {RomanticCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.PEACE,
            Virtue.POWER,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.POWER,
            Virtue.PEACE,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.EXCITEMENT,
            Virtue.PEACE,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.PEACE,
            Virtue.EXCITEMENT,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.WEALTH,
            Virtue.MATERIAL_THINGS,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.MATERIAL_THINGS,
            Virtue.WEALTH,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.KNOWLEDGE,
            Virtue.POWER,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.POWER,
            Virtue.KNOWLEDGE,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.WEALTH,
            Virtue.POWER,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.POWER,
            Virtue.WEALTH,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.ROMANCE,
            Virtue.LUST,
            {RomanticCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.LUST,
            Virtue.ROMANCE,
            {RomanticCompatibility: (1, StatModifierType.Flat)},
        )
    )

    # This is not reciprocal

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.INDEPENDENCE,
            Virtue.FAMILY,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.CURIOSITY,
            Virtue.KNOWLEDGE,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.KNOWLEDGE,
            Virtue.CURIOSITY,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.PEACE,
            Virtue.NATURE,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.NATURE,
            Virtue.MATERIAL_THINGS,
            {PlatonicCompatibility: (-1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.AMBITION,
            Virtue.WEALTH,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )
    social_rule_library.add_rule(
        VirtueRule(
            Virtue.AMBITION,
            Virtue.POWER,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.INDEPENDENCE,
            Virtue.HEALTH,
            {PlatonicCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.LUST,
            Virtue.INDEPENDENCE,
            {RomanticCompatibility: (1, StatModifierType.Flat)},
        )
    )

    social_rule_library.add_rule(
        VirtueRule(
            Virtue.FRIENDSHIP,
            Virtue.FAMILY,
            {RomanticCompatibility: (1, StatModifierType.Flat)},
        )
    )
