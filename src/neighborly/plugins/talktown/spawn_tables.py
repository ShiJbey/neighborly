"""Talk of the Town business spawn table

Spawn table information for business types in Talk of the Town.

"""

from typing import Any

from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="Talk of the Town",
    plugin_id="default.talktown",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:
    # sim.world.system_manager.get_system(
    #     CreateDefaultSettlementSystem
    # ).additional_business_tables.append(
    #     pathlib.Path(__file__).parent / "business_spawn_table.csv"
    # )
    pass
