from typing import Any

from neighborly.simulation import Neighborly, PluginInfo

from . import (
    businesses,
    characters,
    create_town,
    life_events,
    location_bias_rules,
    names,
    residences,
    resident_spawning,
    settlement,
    social_rules,
    systems,
)

plugin_info = PluginInfo(
    name="all default plugins",
    plugin_id="default.all",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any):
    businesses.setup(sim, **kwargs)
    characters.setup(sim, **kwargs)
    settlement.setup(sim, **kwargs)
    create_town.setup(sim, **kwargs)
    life_events.setup(sim, **kwargs)
    location_bias_rules.setup(sim, **kwargs)
    names.setup(sim, **kwargs)
    residences.setup(sim, **kwargs)
    resident_spawning.setup(sim, **kwargs)
    social_rules.setup(sim, **kwargs)
    systems.setup(sim, **kwargs)
