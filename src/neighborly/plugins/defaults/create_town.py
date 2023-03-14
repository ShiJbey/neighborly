from typing import Any

from neighborly.core.ecs.ecs import ISystem
from neighborly.simulation import Neighborly, PluginInfo
from neighborly.utils.common import spawn_settlement

plugin_info = PluginInfo(
    name="default create town plugin",
    plugin_id="default.create_town",
    version="0.1.0",
)


class CreateTown(ISystem):
    sys_group = "initialization"

    def process(self, *args: Any, **kwargs: Any) -> None:
        spawn_settlement(self.world, "settlement")


def setup(sim: Neighborly, **kwargs: Any):
    sim.add_system(CreateTown())
