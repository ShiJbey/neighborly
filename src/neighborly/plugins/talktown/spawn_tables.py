import pathlib
from typing import Any, Dict, List

import yaml

from neighborly.core.ecs.ecs import GameObjectFactory
from neighborly.simulation import Neighborly, PluginInfo

plugin_info = PluginInfo(
    name="Talk of the Town",
    plugin_id="default.talktown",
    version="0.1.0",
)


def setup(sim: Neighborly, **kwargs: Any) -> None:

    with open(pathlib.Path(__file__).parent / "business_spawn_table.yaml", "r") as f:
        data: List[Dict[str, Any]] = yaml.safe_load(f)

    GameObjectFactory.get("settlement").components["BusinessSpawnTable"][
        "entries"
    ].extend(data)

    print()
