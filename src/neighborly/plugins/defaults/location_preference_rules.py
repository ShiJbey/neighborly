from typing import Optional

from neighborly.components.business import ServiceType, location_has_services
from neighborly.components.character import Virtue, Virtues
from neighborly.ecs import GameObject
from neighborly.location_preference import LocationPreferenceRuleLibrary
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="default location preference rules plugin",
    plugin_id="default.location_preference_rules",
    version="0.1.0",
)


def virtue_to_service_preference(virtue: Virtue, services: ServiceType):
    def rule(character: GameObject, location: GameObject) -> Optional[float]:
        if virtues := character.try_component(Virtues):
            if location_has_services(location, services):
                return float(virtues[virtue] - Virtues.VIRTUE_MIN) / (
                    Virtues.VIRTUE_MAX - Virtues.VIRTUE_MIN
                )

    return rule


def setup(sim: Neighborly):
    # For sake of time, use helper the method
    rule_library = sim.world.resource_manager.get_resource(
        LocationPreferenceRuleLibrary
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.LEISURE_TIME, ServiceType.Leisure)
    )
    rule_library.add(virtue_to_service_preference(Virtue.WEALTH, ServiceType.Gambling))
    rule_library.add(
        virtue_to_service_preference(Virtue.EXCITEMENT, ServiceType.Gambling)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.ADVENTURE, ServiceType.Gambling)
    )
    rule_library.add(virtue_to_service_preference(Virtue.LUST, ServiceType.Gambling))
    rule_library.add(
        virtue_to_service_preference(Virtue.MATERIAL_THINGS, ServiceType.Retail)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.EXCITEMENT, ServiceType.Retail)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.LEISURE_TIME, ServiceType.Retail)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.HEALTH, ServiceType.Recreation)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.EXCITEMENT, ServiceType.Recreation)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.KNOWLEDGE, ServiceType.Education)
    )
    rule_library.add(virtue_to_service_preference(Virtue.POWER, ServiceType.Education))
    rule_library.add(
        virtue_to_service_preference(Virtue.AMBITION, ServiceType.Education)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.KNOWLEDGE, ServiceType.Education)
    )
    rule_library.add(virtue_to_service_preference(Virtue.POWER, ServiceType.Education))
    rule_library.add(
        virtue_to_service_preference(Virtue.LEISURE_TIME, ServiceType.Education)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.RELIABILITY, ServiceType.Retail)
    )
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, ServiceType.Retail))
    rule_library.add(virtue_to_service_preference(Virtue.FAMILY, ServiceType.Retail))
    rule_library.add(virtue_to_service_preference(Virtue.SOCIALIZING, ServiceType.Food))
    rule_library.add(virtue_to_service_preference(Virtue.HEALTH, ServiceType.Food))
    rule_library.add(virtue_to_service_preference(Virtue.FAMILY, ServiceType.Food))
    rule_library.add(
        virtue_to_service_preference(Virtue.SOCIALIZING, ServiceType.Socializing)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.EXCITEMENT, ServiceType.Socializing)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.FRIENDSHIP, ServiceType.Socializing)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.SOCIALIZING, ServiceType.Socializing)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.FRIENDSHIP, ServiceType.Socializing)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.HEALTH, ServiceType.HealthCare)
    )
    rule_library.add(
        virtue_to_service_preference(Virtue.TRANQUILITY, ServiceType.Leisure)
    )
