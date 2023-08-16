#!/usr/bin/python3

"""
Neighborly Server Sample
========================

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
            "plugins": [
                "neighborly.plugins.defaults.all",
                "neighborly.plugins.talktown",
            ],
        }
    )
)


def main():
    app.sim.run_for(20)
    app.run()


if __name__ == "__main__":
    main()
