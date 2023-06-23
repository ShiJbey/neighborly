import pathlib
from typing import Any

from neighborly.plugins.defaults.create_town import CreateDefaultSettlementSystem
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="Talk of the Town",
    plugin_id="default.talktown",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:
    sim.world.get_system(CreateDefaultSettlementSystem).load_spawn_table(
        "businesses", pathlib.Path(__file__).parent / "business_spawn_table.csv"
    )
