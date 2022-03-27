import json
from abc import ABC, abstractmethod
from typing import Union

from neighborly.core.ecs import World
from neighborly.core.life_event import EventLog


class NeighborlyExporter(ABC):
    """Serializes the simulation into a string or byte format"""

    @abstractmethod
    def export(self, world: World) -> Union[str, bytes]:
        raise NotImplementedError()


class NeighborlyJsonExporter(NeighborlyExporter):
    """Serializes the simulation world to a JSON string"""

    def export(self, world: World) -> Union[str, bytes]:
        return json.dumps({
            'gameobjects': {g.id: g.to_dict() for g in world.get_gameobjects()},
            'events': [e.to_dict() for e in world.get_resource(EventLog).get_all_events()],
        })
