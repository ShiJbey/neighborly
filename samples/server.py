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
from neighborly.data_collection import DataCollector
from neighborly.server import NeighborlyServer
from neighborly.utils.common import (
    add_character_to_settlement,
    spawn_character,
    spawn_settlement,
)

app = NeighborlyServer(
    NeighborlyConfig.parse_obj(
        {
            "relationship_schema": {
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
            },
            "plugins": [
                "neighborly.plugins.defaults.names",
                "neighborly.plugins.defaults.characters",
                "neighborly.plugins.defaults.businesses",
                "neighborly.plugins.defaults.residences",
                "neighborly.plugins.defaults.life_events",
                "neighborly.plugins.defaults.ai",
            ],
            "settings": {"new_families_per_year": 10},
        }
    )
)


def main():
    west_world = spawn_settlement(app.sim.world, "West World")

    delores = spawn_character(
        app.sim.world,
        "character::default::female",
        first_name="Delores",
        last_name="Abernathy",
        age=32,
    )

    add_character_to_settlement(delores, west_world)

    app.sim.world.get_resource(DataCollector).create_new_table(
        "default", ("pizza", "apples")
    )
    app.sim.world.get_resource(DataCollector).add_table_row(
        "default", {"pizza": 2, "apples": 4}
    )
    app.sim.world.get_resource(DataCollector).add_table_row(
        "default", {"pizza": 87, "apples": 1}
    )
    app.sim.world.get_resource(DataCollector).add_table_row(
        "default", {"pizza": 27, "apples": 53}
    )

    app.run()


if __name__ == "__main__":
    main()
