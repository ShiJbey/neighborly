#!/usr/bin/env python3
"""
This sample shows how to construct a social simulation model manually, It starts with
creating a simulation instance from configuration settings. Next, we use decorator
methods to register new components (Robot, OwesDebt) and a social rule. Finally, within
the main function, we define a new settlement, add new characters, and set some
relationship values.
"""
import time

from neighborly import Neighborly, NeighborlyConfig, SimDateTime
from neighborly.utils.common import (
    add_character_to_settlement,
    add_residence_to_settlement,
    set_residence,
    spawn_character,
    spawn_residence,
    spawn_settlement,
)

sim = Neighborly(
    NeighborlyConfig.parse_obj(
        {
            "seed": 3,
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
                "neighborly.plugins.defaults.names",
                "neighborly.plugins.defaults.characters",
                "neighborly.plugins.defaults.businesses",
                "neighborly.plugins.defaults.residences",
                # "neighborly.plugins.defaults.life_events",
                "neighborly.plugins.defaults.ai",
                "neighborly.plugins.defaults.social_rules",
                "neighborly.plugins.defaults.location_bias_rules",
            ],
        }
    )
)


YEARS_TO_SIMULATE = 5


def main():
    """Main entry point for this module"""
    west_world = spawn_settlement(sim.world, "West World")

    delores = spawn_character(
        sim.world,
        "character::default::female",
        first_name="Delores",
        last_name="Abernathy",
        age=32,
    )

    add_character_to_settlement(delores, west_world)

    house = spawn_residence(sim.world, "residence::default::house")

    add_residence_to_settlement(house, west_world)

    set_residence(delores, house)

    st = time.time()
    sim.run_for(YEARS_TO_SIMULATE)
    elapsed_time = time.time() - st

    print(f"World Date: {str(sim.world.get_resource(SimDateTime))}")
    print("Execution time: ", elapsed_time, "seconds")


if __name__ == "__main__":
    main()
