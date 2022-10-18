import json

from neighborly.core.serializable import ISerializable
from neighborly.core.time import SimDateTime
from neighborly.simulation import Simulation


class NeighborlyJsonExporter:
    """Serializes the simulation to a JSON string"""

    def export(self, sim: Simulation) -> str:
        return json.dumps(
            {
                "seed": sim.seed,
                "date": sim.world.get_resource(SimDateTime).to_iso_str(),
                "gameobjects": {g.id: g.to_dict() for g in sim.world.get_gameobjects()},
                "resources": {
                    r.__class__.__name__: r.to_dict()
                    for r in sim.world.get_all_resources()
                    if isinstance(r, ISerializable)
                },
            }
        )
