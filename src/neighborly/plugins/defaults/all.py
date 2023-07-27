from neighborly.plugins.defaults import (
    businesses,
    characters,
    location_preference_rules,
    names,
    residences,
    resident_spawning,
    social_rules,
)
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="all default plugins",
    plugin_id="default.all",
    version="0.1.0",
)


def setup(sim: Neighborly):
    businesses.setup(sim)
    characters.setup(sim)
    location_preference_rules.setup(sim)
    names.setup(sim)
    residences.setup(sim)
    resident_spawning.setup(sim)
    social_rules.setup(sim)
