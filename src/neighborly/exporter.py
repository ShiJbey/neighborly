import json
from typing import Optional

from neighborly.core.ecs.ecs import ISerializable
from neighborly.simulation import Neighborly


def export_to_json(sim: Neighborly, indent: Optional[int] = None) -> str:
    return json.dumps(
        {
            "seed": sim.config.seed,
            "gameobjects": {g.uid: g.to_dict() for g in sim.world.get_gameobjects()},
            "resources": {
                r.__class__.__name__: r.to_dict()
                for r in sim.world.get_all_resources()
                if isinstance(r, ISerializable)
            },
        },
        indent=indent,
    )
