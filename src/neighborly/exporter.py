import json

from neighborly.core.life_event import LifeEventLog
from neighborly.core.relationship import RelationshipGraph
from neighborly.core.time import SimDateTime
from neighborly.core.town import LandGrid, Town
from neighborly.simulation import Simulation


class NeighborlyJsonExporter:
    """Serializes the simulation to a JSON string"""

    def export(self, sim: Simulation) -> str:
        return json.dumps(
            {
                "seed": sim.seed,
                "date": sim.world.get_resource(SimDateTime).to_iso_str(),
                "gameobjects": {g.id: g.to_dict() for g in sim.world.get_gameobjects()},
                "events": [
                    f.to_dict()
                    for f in sim.world.get_resource(LifeEventLog).event_history
                ],
                "relationships": sim.world.get_resource(RelationshipGraph).to_dict(),
                "town": sim.world.get_resource(Town).to_dict(),
                "land": sim.world.get_resource(LandGrid).grid.to_dict(),
            }
        )
