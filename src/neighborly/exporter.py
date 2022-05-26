import json
from abc import ABC, abstractmethod
from typing import Union

from neighborly.core.ecs import World
from neighborly.core.life_event import LifeEventLogger
from neighborly.core.social_network import RelationshipNetwork
from neighborly.core.time import SimDateTime
from neighborly.core.town import Town


class NeighborlyExporter(ABC):
    """Serializes the simulation into a string or byte format"""

    @abstractmethod
    def export(self, world: World) -> Union[str, bytes]:
        raise NotImplementedError()


class NeighborlyJsonExporter(NeighborlyExporter):
    """Serializes the simulation world to a JSON string"""

    def export(self, world: World) -> str:
        return json.dumps(
            {
                "date": world.get_resource(SimDateTime).to_iso_str(),
                "town": world.get_resource(Town).to_dict(),
                "gameobjects": {g.id: g.to_dict() for g in world.get_gameobjects()},
                "relationships": world.get_resource(RelationshipNetwork).to_dict(),
                "events": [
                    e.to_dict()
                    for e in world.get_resource(LifeEventLogger).get_all_events()
                ],
            }
        )
