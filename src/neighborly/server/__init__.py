from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from neighborly.core.character import GameCharacter

from neighborly.simulation import Simulation


class NeighborlyServer:
    def __init__(self, simulation: Simulation) -> None:
        self.app = Flask(__name__)
        self.app.config["SECRET"] = "neighborly-server-secret"
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.sim = simulation
        self._configure_socketio()
        self._configure_routes()

    def _configure_socketio(self) -> None:
        @self.socketio.on("step")
        def step_simulation():
            print("Stepping simulation")
            self.sim.step()
            emit("simulation-updated", broadcast=True)

    def _configure_routes(self) -> None:
        @self.app.route("/characters")
        def get_characters():
            return {
                gid: character.to_dict()
                for gid, character in self.sim.world.get_component(GameCharacter)
            }

        @self.app.route("/gameobject/<gid>")
        def get_gameobject(gid):
            gameobject = self.sim.world.get_gameobject(int(gid))
            return {"components": [c.to_dict() for c in gameobject.get_components()]}

        @self.app.route("/")
        def index():
            return render_template("index.html")

    def run(self, host: str = "localhost") -> None:
        self.socketio.run(self.app, host=host, debug=True)
