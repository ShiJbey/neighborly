from typing import Any

from neighborly.plugins.defaults.archetypes import DefaultArchetypesPlugin
from neighborly.plugins.defaults.life_events import DefaultLifeEventPlugin
from neighborly.plugins.defaults.names import DefaultNameDataPlugin
from neighborly.plugins.defaults.systems import DefaultSystemsPlugin
from neighborly.simulation import Plugin, Simulation


class DefaultPlugin(Plugin):
    def setup(self, sim: Simulation, **kwargs: Any) -> None:
        DefaultSystemsPlugin().setup(sim, **kwargs)
        DefaultNameDataPlugin().setup(sim, **kwargs)
        DefaultLifeEventPlugin().setup(sim, **kwargs)
        DefaultArchetypesPlugin().setup(sim, **kwargs)


def get_plugin() -> Plugin:
    return DefaultPlugin()
