import json
from typing import Optional

from neighborly.ecs import ISerializable
from neighborly.simulation import Neighborly


def export_to_json(sim: Neighborly, indent: Optional[int] = None) -> str:
    serialized_data = {
        "seed": sim.config.seed,
        "gameobjects": {
            str(g.uid): g.to_dict()
            for g in sim.world.gameobject_manager.iter_gameobjects()
        },
        "resources": {
            r.__class__.__name__: r.to_dict()
            for r in sim.world.resource_manager.get_all_resources()
            if isinstance(r, ISerializable)
        },
    }
    return json.dumps(
        serialized_data,
        indent=indent,
    )
