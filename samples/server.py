"""
Neighborly Server Sample
-------------------------

This sample script demonstrates how to create a new Python script that runs an instance
of Neighborly and exposes its internal data to REST API endpoints. The simulation is
constructed similarly to the standard simulation, except it uses the NeighborlyServer()
constructor.

Currently, this sample creates a single settlement, character, and a few data table
entries. In the future, we want to be able to inspect and control the entire simulation
using API calls.
"""

from neighborly import NeighborlyConfig
from neighborly.server import NeighborlyServer

app = NeighborlyServer(
    NeighborlyConfig.parse_obj(
        {
            "seed": "Apples",
            "time_increment": "1mo",
            "relationship_schema": {
                "components": {
                    "Friendship": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "Romance": {
                        "min_value": -100,
                        "max_value": 100,
                    },
                    "InteractionScore": {
                        "min_value": -5,
                        "max_value": 5,
                    },
                }
            },
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown.spawn_tables",
                "neighborly.plugins.talktown",
            ],
        }
    )
)


def main():
    app.sim.run_for(1)
    app.run()


if __name__ == "__main__":
    main()
