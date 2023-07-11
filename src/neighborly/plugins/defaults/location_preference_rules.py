from typing import Optional

from neighborly.components.character import Virtue, Virtues
from neighborly.core.ecs import GameObject
from neighborly.core.location_preference import LocationPreferenceRuleLibrary
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import location_has_services

plugin_info = PluginInfo(
    name="default location preference rules plugin",
    plugin_id="default.location_preference_rules",
    version="0.1.0",
)


def virtue_to_service_preference(virtue: Virtue, service: str):
    def rule(character: GameObject, location: GameObject) -> Optional[float]:
        if virtues := character.try_component(Virtues):
            if location_has_services(location, service):
                return float(virtues[virtue] - Virtues.VIRTUE_MIN) / (
                    Virtues.VIRTUE_MAX - Virtues.VIRTUE_MIN
                )

    return rule


def setup(sim: Neighborly):
    # For sake of time, use helper the method
    rule_library = sim.world.resource_manager.get_resource(
        LocationPreferenceRuleLibrary
    )
    rule_library.add(virtue_to_service_preference(Virtue.LEISURE_TIME, "relaxing"))
    rule_library.add(virtue_to_service_preference(Virtue.WEALTH, "gambling"))
    rule_library.add(virtue_to_service_preference(Virtue.EXCITEMENT, "gambling"))
    rule_library.add(virtue_to_service_preference(Virtue.ADVENTURE, "gambling"))
    rule_library.add(virtue_to_service_preference(Virtue.LUST, "gambling"))
    rule_library.add(virtue_to_service_preference(Virtue.MATERIAL_THINGS, "shopping"))
    rule_library.add(virtue_to_service_preference(Virtue.EXCITEMENT, "shopping"))
    rule_library.add(virtue_to_service_preference(Virtue.LEISURE_TIME, "shopping"))
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, "recreation"))
    rule_library.add(virtue_to_service_preference(Virtue.EXCITEMENT, "recreation"))
    rule_library.add(virtue_to_service_preference(Virtue.KNOWLEDGE, "studying"))
    rule_library.add(virtue_to_service_preference(Virtue.POWER, "studying"))
    rule_library.add(virtue_to_service_preference(Virtue.AMBITION, "studying"))
    rule_library.add(virtue_to_service_preference(Virtue.KNOWLEDGE, "reading"))
    rule_library.add(virtue_to_service_preference(Virtue.POWER, "reading"))
    rule_library.add(virtue_to_service_preference(Virtue.LEISURE_TIME, "reading"))
    rule_library.add(virtue_to_service_preference(Virtue.RELIABILITY, "errands"))
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, "errands"))
    rule_library.add(virtue_to_service_preference(Virtue.FAMILY, "errands"))
    rule_library.add(virtue_to_service_preference(Virtue.SOCIALIZING, "eating"))
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, "eating"))
    rule_library.add(virtue_to_service_preference(Virtue.FAMILY, "eating"))
    rule_library.add(virtue_to_service_preference(Virtue.SOCIALIZING, "socializing"))
    rule_library.add(virtue_to_service_preference(Virtue.EXCITEMENT, "socializing"))
    rule_library.add(virtue_to_service_preference(Virtue.FRIENDSHIP, "socializing"))
    rule_library.add(virtue_to_service_preference(Virtue.SOCIALIZING, "drinking"))
    rule_library.add(virtue_to_service_preference(Virtue.FRIENDSHIP, "drinking"))
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, "relaxing"))
    rule_library.add(virtue_to_service_preference(Virtue.TRANQUILITY, "relaxing"))
    rule_library.add(virtue_to_service_preference(Virtue.LEISURE_TIME, "relaxing"))
