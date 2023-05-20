import pathlib
from typing import Any

from neighborly.simulation import Neighborly, PluginInfo
from neighborly.plugins.defaults.create_town import CreateDefaultSettlementSystem

plugin_info = PluginInfo(
    name="Talk of the Town",
    plugin_id="default.talktown",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:
    CreateDefaultSettlementSystem.load_spawn_table(
        "businesses", pathlib.Path(__file__).parent / "business_spawn_table.csv"
    )
