#!/usr/bin/env python3
"""
This sample shows how to construct a social simulation model manually, It starts with
creating a simulation instance from configuration settings. Next, we use decorator
methods to register new components (Robot, OwesDebt) and a social rule. Finally, within
the main function, we define a new settlement, add new characters, and set some
relationship values.
"""
import time
from typing import Any, Dict

from neighborly import ISystem, Neighborly, NeighborlyConfig, SimDateTime
from neighborly.components import GameCharacter
from neighborly.core.relationship import (
    Friendship,
    InteractionScore,
    RelationshipManager,
    Romance,
)
from neighborly.core.status import StatusComponent, StatusManager
from neighborly.core.traits import TraitComponent
from neighborly.data_collection import DataCollector
from neighborly.decorators import component, system
from neighborly.exporter import export_to_json
from neighborly.utils.common import (
    add_character_to_settlement,
    add_residence_to_settlement,
    set_residence,
    spawn_character,
    spawn_residence,
    spawn_settlement,
)
from neighborly.utils.traits import add_trait

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
                "neighborly.plugins.defaults.life_events",
                "neighborly.plugins.defaults.ai",
                "neighborly.plugins.defaults.social_rules",
                "neighborly.plugins.defaults.location_bias_rules",
            ],
        }
    )
)


@component(sim)
class Robot(TraitComponent):
    """Tags a character as a Robot"""

    pass


@component(sim)
class OwesDebt(StatusComponent):
    """Marks a character as owing money to another character"""

    def __init__(self, amount: int) -> None:
        super().__init__()
        self.amount: int = amount

    def to_dict(self) -> Dict[str, Any]:
        return {**super().to_dict(), "amount": self.amount}


@system(sim)
class RelationshipReporter(ISystem):
    sys_group = "data-collection"

    def process(self, *args: Any, **kwargs: Any) -> None:
        timestamp = self.world.get_resource(SimDateTime).to_iso_str()
        data_collector = self.world.get_resource(DataCollector)
        for guid, (game_character, relationship_manager) in self.world.get_components(
            (GameCharacter, RelationshipManager)
        ):
            if (
                game_character.first_name == "Delores"
                and game_character.last_name == "Abernathy"
            ):
                for target_id, rel_id in relationship_manager.relationships.items():
                    relationship = self.world.get_gameobject(rel_id)
                    data_collector.add_table_row(
                        "relationships",
                        {
                            "timestamp": timestamp,
                            "owner": guid,
                            "target": target_id,
                            "friendship": relationship.get_component(
                                Friendship
                            ).get_value(),
                            "romance": relationship.get_component(Romance).get_value(),
                            "interaction_score": relationship.get_component(
                                InteractionScore
                            ).get_value(),
                            "statuses": str(relationship.get_component(StatusManager)),
                        },
                    )


EXPORT_SIM = True
YEARS_TO_SIMULATE = 50


def main():
    """Main entry point for this module"""
    sim.world.get_resource(DataCollector).create_new_table(
        "relationships",
        (
            "timestamp",
            "owner",
            "target",
            "friendship",
            "romance",
            "interaction_score",
            "statuses",
        ),
    )

    west_world = spawn_settlement(sim.world, "West World")

    delores = spawn_character(
        sim.world,
        "character::default::female",
        first_name="Delores",
        last_name="Abernathy",
        age=32,
    )

    add_trait(delores, Robot())

    add_character_to_settlement(delores, west_world)

    house = spawn_residence(sim.world, "residence::default::house")

    add_residence_to_settlement(house, west_world)

    set_residence(delores, house)

    st = time.time()
    sim.run_for(YEARS_TO_SIMULATE)
    elapsed_time = time.time() - st

    print(f"World Date: {str(sim.world.get_resource(SimDateTime))}")
    print("Execution time: ", elapsed_time, "seconds")

    # rel_data = sim.world.get_resource(DataCollector).get_table_dataframe(
    #     "relationships"
    # )
    #
    # rel_data[:800].to_csv("rel_data.csv")

    if EXPORT_SIM:
        with open(f"neighborly_{sim.config.seed}.json", "w") as f:
            f.write(export_to_json(sim))


if __name__ == "__main__":
    main()
