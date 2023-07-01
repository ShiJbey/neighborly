from typing import Any, Optional

from neighborly.components.character import Virtue, Virtues
from neighborly.core.ecs import GameObject
from neighborly.core.location_bias import LocationBiasRuleLibrary
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import location_has_activities

plugin_info = PluginInfo(
    name="default location bias rules plugin",
    plugin_id="default.location_bias_rules",
    version="0.1.0",
)


def virtue_to_activity_bias(virtue: Virtue, activity: str, modifier: int):
    def rule(character: GameObject, location: GameObject) -> Optional[int]:
        if virtues := character.try_component(Virtues):
            if virtues[virtue] >= Virtues.STRONG_AGREE and location_has_activities(
                location, activity
            ):
                return modifier

    return rule


def setup(sim: Neighborly, **kwargs: Any):
    # For sake of time, use helper the method
    rule_library = sim.world.resource_manager.get_resource(LocationBiasRuleLibrary)
    rule_library.add(virtue_to_activity_bias(Virtue.LEISURE_TIME, "relaxing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.WEALTH, "gambling", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.EXCITEMENT, "gambling", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.ADVENTURE, "gambling", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.LUST, "gambling", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.MATERIAL_THINGS, "shopping", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.EXCITEMENT, "shopping", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.LEISURE_TIME, "shopping", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.HEALTH, "recreation", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.EXCITEMENT, "recreation", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.KNOWLEDGE, "studying", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.POWER, "studying", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.AMBITION, "studying", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.KNOWLEDGE, "reading", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.POWER, "reading", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.LEISURE_TIME, "reading", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.RELIABILITY, "errands", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.HEALTH, "errands", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.FAMILY, "errands", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.SOCIALIZING, "eating", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.HEALTH, "eating", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.FAMILY, "eating", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.SOCIALIZING, "socializing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.EXCITEMENT, "socializing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.FRIENDSHIP, "socializing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.SOCIALIZING, "drinking", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.FRIENDSHIP, "drinking", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.HEALTH, "relaxing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.TRANQUILITY, "relaxing", 1))
    rule_library.add(virtue_to_activity_bias(Virtue.LEISURE_TIME, "relaxing", 1))
