import threading
from typing import Any, Dict, Optional, List

from flask import Flask, request, abort
from flask_restful import Api, Resource  # type: ignore
from flask_cors import CORS
from marshmallow import Schema, fields

from neighborly.config import NeighborlyConfig
from neighborly.core.ecs import World
from neighborly.core.ecs.ecs import ISerializable
from neighborly.core.life_event import AllEvents
from neighborly.core.time import SimDateTime
from neighborly.data_collection import DataCollector
from neighborly.simulation import Neighborly


class GameObjectResource(Resource):
    world: World

    def get(self, guid: int):
        return self.world.get_gameobject(guid).to_dict()


class ComponentResource(Resource):
    world: World

    def get(self, guid: int, **kwargs: Any):
        component = self.world.get_gameobject(guid).get_component(
            self.world.get_component_info(kwargs["component_type"]).component_type
        )

        if isinstance(component, ISerializable):
            return component.to_dict()

        raise TypeError(f"{kwargs['component_type']} is not serializable to JSON")


class AllGameObjectsResource(Resource):
    world: World

    def get(self):
        return {"gameobjects": [g.uid for g in self.world.get_gameobjects()]}


class GameObjectQuerySchema(Schema):
    components = fields.Str(required=True)


class QueryGameObjectsResource(Resource):
    """Allow users to query for GameObjects based on component types."""

    world: World
    schema = GameObjectQuerySchema()

    def get(self):
        errors = self.schema.validate(request.args)
        if errors:
            abort(400, str(errors))

        data: Any = self.schema.load(request.args)

        component_type_names: List[str] = [
            s.strip() for s in data["components"].split(",") if s
        ]

        component_types = tuple(
            [
                self.world.get_component_info(name).component_type
                for name in component_type_names
            ]
        )

        results = {
            "gameobjects": [
                {"guid": guid, "name": self.world.get_gameobject(guid).name}
                for guid, _ in self.world.get_components(component_types)
            ]
        }

        return results


class DataTablesResource(Resource):
    world: World

    def get(self, table_name: str) -> Dict[str, Any]:
        return (
            self.world.get_resource(DataCollector)
            .get_table_dataframe(table_name)
            .to_dict()  # type: ignore
        )


class SimEventsResource(Resource):
    world: World

    def get(self, event_id: int) -> Dict[str, Any]:
        return self.world.get_resource(AllEvents)[event_id].to_dict()


class WorldSeedResource(Resource):
    world: World
    def get(self):
        return self.world.get_resource(NeighborlyConfig).seed


class WorldDateResource(Resource):
    world: World
    def get(self):
        return self.world.get_resource(SimDateTime).to_date_str()


def run_api_server(sim: Neighborly) -> None:
    server: Flask = Flask("Neighborly")
    CORS(server)
    api: Api = Api(server)

    GameObjectResource.world = sim.world
    ComponentResource.world = sim.world
    AllGameObjectsResource.world = sim.world
    DataTablesResource.world = sim.world
    SimEventsResource.world = sim.world
    QueryGameObjectsResource.world = sim.world
    WorldSeedResource.world = sim.world
    WorldDateResource.world = sim.world

    api.add_resource(GameObjectResource, "/api/gameobject/<int:guid>")  # type: ignore
    api.add_resource(  # type: ignore
        ComponentResource,
        "/api/gameobject/<int:guid>/component/<string:component_type>",
    )
    api.add_resource(  # type: ignore
        AllGameObjectsResource,
        "/api/gameobject/",
    )
    api.add_resource(  # type: ignore
        QueryGameObjectsResource,
        "/api/query/gameobject/",
    )
    api.add_resource(  # type: ignore
        WorldSeedResource,
        "/api/seed/",
    )
    api.add_resource(  # type: ignore
        WorldDateResource,
        "/api/date/",
    )
    api.add_resource(  # type: ignore
        DataTablesResource,
        "/api/data/<string:table_name>",
    )
    api.add_resource(SimEventsResource, "/api/events/<int:event_id>")  # type: ignore

    server.run(debug=False)


def run_simulation(sim: Neighborly) -> None:
    print(id(sim.world))


class NeighborlyServer:
    def __init__(self, config: Optional[NeighborlyConfig] = None):
        self.sim: Neighborly = Neighborly(config)

        self.server_thread = threading.Thread(target=run_api_server, args=(self.sim,))

        self.simulation_thread = threading.Thread(
            target=run_simulation, args=(self.sim,)
        )

    def run(self) -> None:
        try:
            self.server_thread.start()
            self.simulation_thread.start()
            while True:
                pass
            # self.server.run(debug=debug)
        except KeyboardInterrupt:
            self.server_thread.join()
            self.simulation_thread.join()
        except SystemExit:
            self.server_thread.join()
            self.simulation_thread.join()
        except SystemError:
            self.server_thread.join()
            self.simulation_thread.join()
